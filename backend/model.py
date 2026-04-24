import pandas as pd
import numpy as np
from io import StringIO
from sklearn.linear_model import LogisticRegression

_modelo_treinado = None
_accuracy = 0.0
_samples = 0

def obeter_dados_e_treinar(file_path: str):
    global _modelo_treinado, _accuracy, _samples
    
    # Carregar dados CSV usando Pandas. Evita erros de colunas sujas do DataSUS
    try:
        df = pd.read_csv(file_path, sep=';', dtype=str, encoding='utf-8')
    except UnicodeDecodeError:
        df = pd.read_csv(file_path, sep=';', dtype=str, encoding='latin-1')
    
    if len(df) < 2:
        raise ValueError("Arquivo vazio ou inválido.")
        
    df.columns = df.columns.str.strip().str.upper()
    df = df.replace('"', '', regex=True)
    
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
            except: pass
            
        if 'EVOLUCAO' in row:
            try:
                evo = int(float(str(row['EVOLUCAO'])))
                if evo in [1, 2]: has_valid_target = True
                if evo == 2: is_grave = True # Óbito
            except: pass
            
        if 'SUPORT_VEN' in row:
            try:
                sup = int(float(str(row['SUPORT_VEN'])))
                if sup in [1, 2, 3]: has_valid_target = True
                if sup in [1, 2]: is_grave = True # Precisou de suporte ventilatório
            except: pass
            
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
        except: pass
        
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
            except: pass
            
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
