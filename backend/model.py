import os
import pandas as pd
import numpy as np
import requests
import joblib
from dotenv import load_dotenv
from sklearn.linear_model import LogisticRegression

MODEL_PATH = os.path.join(os.path.dirname(__file__), "modelo_treinado.joblib")

_modelo_treinado = None
_accuracy = 0.0
_samples = 0

try:
    if os.path.exists(MODEL_PATH):
        dados_salvos = joblib.load(MODEL_PATH)
        _modelo_treinado = dados_salvos["modelo"]
        _accuracy = dados_salvos["accuracy"]
        _samples = dados_salvos["samples"]
except Exception as e:
    print(f"Aviso: Não foi possível carregar o modelo salvo: {e}")

load_dotenv()

def obter_dados_e_treinar():
    global _modelo_treinado, _accuracy, _samples
    
    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_KEY")
    if not url or not key:
        raise ValueError("Configurações do Supabase (SUPABASE_URL ou SUPABASE_KEY) não encontradas no arquivo .env.")
    
    headers = {
        "apikey": key,
        "Authorization": f"Bearer {key}"
    }
    
    all_data = []
    limit = 1000
    max_total = 50000
    
    for offset in range(0, max_total, limit):
        endpoint = f"{url}/rest/v1/srag?select=*&limit={limit}&offset={offset}"
        response = requests.get(endpoint, headers=headers, timeout=10)
        
        if not response.ok:
            raise ValueError(f"Erro ao buscar do Supabase: {response.text}")
            
        data = response.json()
        if not data:
            break
            
        all_data.extend(data)
        if len(data) < limit:
            break
            
    df = pd.DataFrame(all_data)
    
    if len(df) < 2:
        raise ValueError("Tabela vazia ou com dados insuficientes no Supabase.")
        
    df.columns = df.columns.str.strip().str.upper()
    df = df.replace('"', '', regex=True)
    
    # Nota: CARDIOPATI está sem o "A" final pois o DataSUS as vezes limita os nomes das colunas a 10 caracteres (formato DBF)
    feature_keys = ['FEBRE', 'TOSSE', 'GARGANTA', 'DISPNEIA', 'ASMA', 'DIABETES', 'CARDIOPATI', 'SATURACAO']
    
    X = []
    Y = []
    
    # Processar cada uma das linhas seguindo a logica JavaScript original
    for index, row in df.iterrows():
        is_grave = False
        has_valid_target = False
        
        # Logica de Diagnostico Gravidade
        if 'UTI' in row:
            try:
                uti = int(float(str(row['UTI'])))
                if uti in [1, 2]: has_valid_target = True
                if uti == 1: is_grave = True
            except Exception: pass
            
        if 'EVOLUCAO' in row:
            try:
                evo = int(float(str(row['EVOLUCAO'])))
                if evo in [1, 2]: has_valid_target = True
                if evo == 2: is_grave = True # Óbito
            except Exception: pass
            
        if 'SUPORT_VEN' in row:
            try:
                sup = int(float(str(row['SUPORT_VEN'])))
                if sup in [1, 2, 3]: has_valid_target = True
                if sup in [1, 2]: is_grave = True # Precisou de suporte ventilatório
            except Exception: pass
            
        if not has_valid_target:
            continue
            
        # Logica Idade
        idade_anos = 0
        try:
            if 'NU_IDADE_N' in row and 'TP_IDADE' in row:
                tp_idade = int(float(row['TP_IDADE']))
                nu_idade = int(float(row['NU_IDADE_N']))
                if tp_idade == 3: idade_anos = nu_idade
                elif tp_idade == 2: idade_anos = nu_idade / 12.0
        except Exception: pass
        
        if np.isnan(idade_anos) or idade_anos > 120:
            continue
            
        # Extracao das Features que vao entrar na Inteligencia
        row_features = []
        row_valid = True
        
        for feat in feature_keys:
            val = 2 # 2 significa Não encontrado/falso no padrao DataSUS
            try:
                if feat in row:
                    val = int(float(str(row[feat])))
            except Exception: pass
            
            # Se for ignorado (9), a gente da discard na linha
            if val not in [1, 2]:
                row_valid = False
                break
                
            row_features.append(1 if val == 1 else 0)
            
        if row_valid:
            row_features.append(idade_anos / 100.0)
            X.append(row_features)
            # Y = 1 (Quadro Grave), Y = 0 (Quadro Leve/Moderado)
            Y.append(1 if is_grave else 0)
            
    if len(X) < 20: 
        raise ValueError("Foram encontradas poucas linhas válidas de pacientes.")
        
    X = np.array(X)
    Y = np.array(Y)
    
    # Substituíndo o Perceptron rudimentar por uma classificador inteligente usando ML de verdade (LogisticRegression)
    clf = LogisticRegression(random_state=42, C=1.0, solver='lbfgs', max_iter=1000)
    clf.fit(X, Y)
    
    # Acuracia
    accuracy = clf.score(X, Y) * 100.0
    _accuracy = accuracy
    _samples = len(X)
    _modelo_treinado = clf
    
    # Salvar o modelo treinado localmente
    try:
        joblib.dump({
            "modelo": _modelo_treinado,
            "accuracy": _accuracy,
            "samples": _samples
        }, MODEL_PATH)
    except Exception as e:
        print(f"Aviso: Falha ao salvar o modelo: {e}")
    
    return _accuracy, _samples

def prever_gravidade(features_list):
    global _modelo_treinado
    if _modelo_treinado is None:
        raise Exception("O Modelo de Inteligência ainda não foi treinado.")
        
    # Obtemos a probabilidade de ser Quadro Grave [0.0 até 1.0]
    proba = _modelo_treinado.predict_proba([features_list])[0]
    
    # Retornamos multiplicando por 100
    return float(proba[1] * 100.0)

def get_stats():
    return {
        "treinado": _modelo_treinado is not None,
        "accuracy": _accuracy,
        "samples": _samples
    }
