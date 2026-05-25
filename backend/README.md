# Documentação Técnica: Módulo de Inteligência Artificial

**Arquivos:** `model.py`, `api.py`  
**Projeto:** Triagem Respiratória IA — A3 Inteligência Artificial  
**Instituição:** [Faculdade]  

---

## 1. Visão Geral

Este módulo implementa o **núcleo de aprendizado de máquina** da aplicação de triagem respiratória. Sua responsabilidade é buscar dados clínicos reais do **Supabase** (via REST API paginada), extrair as características clínicas relevantes de cada paciente, treinar um modelo de **Regressão Logística** e, posteriormente, utilizar o modelo treinado para estimar a probabilidade de um novo paciente apresentar um quadro respiratório grave. O modelo treinado é persistido em disco via `joblib` para evitar novo treinamento a cada reinício do servidor.

---

## 2. Fundamento Teórico: Do Perceptron à Regressão Logística

### 2.1 O Perceptron de Rosenblatt (1958)

O **Perceptron** é o precursor de todos os algoritmos de classificação baseados em redes neurais e é o ponto de partida para entender o modelo aqui implementado.

Proposto por Frank Rosenblatt em 1958, o Perceptron é um classificador linear binário que aprende atualizando iterativamente **pesos** associados a cada variável de entrada (feature). Dado um vetor de entrada **x** = [x₁, x₂, ..., xₙ] e um vetor de pesos **w** = [w₁, w₂, ..., wₙ], o Perceptron calcula:

```
z = w₁x₁ + w₂x₂ + ... + wₙxₙ + b
```

Onde `b` é o viés (*bias*). A saída é então determinada por uma função de ativação degrau:

```
ŷ = 1  se z ≥ 0
ŷ = 0  se z < 0
```

A regra de aprendizado do Perceptron atualiza os pesos a cada erro:

```
wⱼ ← wⱼ + η · (y - ŷ) · xⱼ
```

Onde `η` é a **taxa de aprendizado** (learning rate).

**Limitação crítica:** O Perceptron clássico **somente converge** quando os dados são **linearmente separáveis** — ou seja, quando existe um hiperplano que separa perfeitamente as duas classes. Dados médicos reais raramente satisfazem essa condição.

---

### 2.2 A Transição: Perceptron com Função Sigmoide

A primeira grande evolução foi **substituir a função degrau pela função sigmoide (logística)**:

```
σ(z) = 1 / (1 + e^(-z))
```

Esta função mapeia qualquer valor real para o intervalo (0, 1), permitindo interpretar a saída como uma **probabilidade**:

```
P(y=1 | x) = σ(wᵀx + b) = 1 / (1 + e^(-(w·x + b)))
```

Isso é exatamente o que o código JavaScript original implementava manualmente:

```javascript
// Versão JavaScript (Perceptron com Sigmoide)
const sigmoid = (z) => 1 / (1 + Math.exp(-z));

for (let ep = 0; ep < epochs; ep++) {
  for (let i = 0; i < X.length; i++) {
    let z = bias;
    for (let j = 0; j < x.length; j++) z += weights[j] * x[j];
    const y_pred = sigmoid(z);
    const error = y_pred - y;
    for (let j = 0; j < x.length; j++) {
      weights[j] -= learningRate * error * x[j];  // Gradiente Descendente
    }
    bias -= learningRate * error;
  }
}
```

Esta atualização de pesos por gradiente descendente é a base matemática da **Regressão Logística**.

---

### 2.3 Regressão Logística: A Formalização Estatística do Perceptron com Sigmoide

A **Regressão Logística** não é, apesar do nome, um algoritmo de regressão — é um **classificador probabilístico** que generaliza formalmente o Perceptron com sigmoide com uma base sólida em estatística e otimização.

#### Modelo Probabilístico

A probabilidade de um paciente apresentar quadro grave dado seu vetor de sintomas **x** é modelada como:

```
P(Grave=1 | x; w, b) = σ(wᵀx + b) = 1 / (1 + e^(-(Σ wⱼxⱼ + b)))
```

#### Função de Perda: Entropia Cruzada Binária

Em vez de minimizar diretamente o erro de classificação (como o Perceptron), a Regressão Logística maximiza a **verossimilhança** dos dados. Equivalentemente, minimiza a **entropia cruzada binária** (*Binary Cross-Entropy*):

```
L(w, b) = - (1/N) · Σᵢ [ yᵢ log(ŷᵢ) + (1 - yᵢ) log(1 - ŷᵢ) ]
```

Onde:
- N = número de amostras de treinamento
- yᵢ = rótulo real do paciente i (0 = Leve, 1 = Grave)
- ŷᵢ = probabilidade predita pelo modelo para o paciente i

#### Otimização: L-BFGS

O algoritmo utilizado para minimizar L(w, b) neste projeto é o **L-BFGS** (*Limited-memory Broyden–Fletcher–Goldfarb–Shanno*), um método de otimização quasi-Newton de segunda ordem. Diferente do gradiente descendente simples do Perceptron original (que usa apenas a derivada de primeira ordem), o L-BFGS **aproxima a matriz Hessiana** (de segundas derivadas), convergindo muito mais rapidamente e de forma mais estável em dados reais.

| Característica | Perceptron (JS) | Regressão Logística (Python) |
|---|---|---|
| Função de ativação | Sigmoide | Sigmoide |
| Otimizador | Gradiente Descendente Manual | L-BFGS (quasi-Newton) |
| Função de perda | Erro quadrático implícito | Entropia Cruzada Binária |
| Regularização | Nenhuma | L2 (Ridge) com C=1.0 |
| Balanceamento de classes | Nenhum | `class_weight='balanced'` |
| Convergência | Lenta, pode oscilar | Rápida e estável |

---

## 3. Explicação do Código (`model.py`)

### 3.1 Importações, Constantes e Estado Global

```python
import os
import pandas as pd
import numpy as np
import requests
import joblib
from dotenv import load_dotenv
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score

MODEL_PATH = os.path.join(os.path.dirname(__file__), "modelo_treinado.joblib")

# Ordem canônica das features — usada no treino E na predição (via api.py).
# Qualquer alteração aqui deve ser refletida em api.py e vice-versa.
FEATURE_KEYS = ['FEBRE', 'TOSSE', 'GARGANTA', 'DISPNEIA', 'ASMA', 'DIABETES', 'CARDIOPATI', 'SATURACAO']

_modelo_treinado = None
_accuracy        = 0.0
_samples         = 0
```

`FEATURE_KEYS` é definida como **constante exportável no topo do módulo**, sendo a única fonte de verdade para a ordem das features — tanto no treinamento quanto na predição. Isso elimina o risco de mismatch entre `model.py` e `api.py`.

O modelo treinado é **armazenado em memória** como variável global do módulo Python e **persistido em disco** via `joblib` (`modelo_treinado.joblib`). Na próxima inicialização do servidor, o arquivo é carregado automaticamente — evitando novo treinamento. As credenciais do Supabase são lidas do `.env` via `load_dotenv()`.

---

### 3.2 Extração e Limpeza dos Dados (Fonte: Supabase REST API)

A função `obter_dados_e_treinar()` busca os dados diretamente do **Supabase** em lotes de 1.000 registros (até 50.000 no total):

```python
def obter_dados_e_treinar():
    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_KEY")
    headers = {"apikey": key, "Authorization": f"Bearer {key}"}

    all_data = []
    for offset in range(0, 50000, 1000):
        endpoint = f"{url}/rest/v1/srag?select=*&limit=1000&offset={offset}"
        response = requests.get(endpoint, headers=headers, timeout=10)
        data = response.json()
        if not data: break
        all_data.extend(data)
        if len(data) < 1000: break

    df = pd.DataFrame(all_data)
    df.columns = df.columns.str.strip().str.upper()
```

Os dados chegam como JSON (lista de dicts) do Supabase. O Pandas normaliza os nomes de colunas para maiúsculas e remove espaços. Registros insuficientes (menos de 2 linhas) geram um `ValueError` imediatamente.

A lógica de extração de features foi isolada na função `_extrair_features(df)`, separando responsabilidades e facilitando testes unitários futuros.

#### 3.2.1 Definição da Variável Alvo (Target Y)

A variável alvo **Y** é binária: `1` para **Quadro Grave**, `0` para **Quadro Leve/Moderado**.

```python
# EVOLUCAO = 2 → Óbito
if evo == 2: is_grave = True

# UTI = 1 → Internado em UTI
if uti == 1: is_grave = True

# SUPORT_VEN = 1 ou 2 → Suporte ventilatório invasivo/não invasivo
if sup in [1, 2]: is_grave = True
```

Esta definição segue o **Dicionário de Dados do SIVEP-Gripe** publicado pelo Ministério da Saúde. Um caso é classificado como grave se ocorreu **ao menos um** dos três eventos: óbito, internação em UTI ou necessidade de suporte ventilatório.

#### 3.2.2 Definição do Vetor de Features (X)

As features foram escolhidas por sua relevância clínica em quadros respiratórios agudos, conforme literatura médica, e seguem exatamente a ordem definida em `FEATURE_KEYS`:

```python
FEATURE_KEYS = ['FEBRE', 'TOSSE', 'GARGANTA', 'DISPNEIA',
                'ASMA', 'DIABETES', 'CARDIOPATI', 'SATURACAO']
```

> **Nota:** `CARDIOPATI` está sem o "A" final pois o DataSUS limita nomes de colunas a 10 caracteres no formato DBF.

Cada feature é **binarizada**: `1` (presente) ou `0` (ausente). O padrão DataSUS usa `1 = Sim`, `2 = Não`, e `9 = Ignorado`. Registros com valor `9` são **descartados** para não introduzir ruído no treinamento.

```python
row_features.append(1 if val == 1 else 0)
```

A **idade** é normalizada para o intervalo [0, 1] dividindo por 100, para evitar que valores grandes dominem os pesos:

```python
row_features.append(idade_anos / 100.0)
```

O vetor final de cada paciente tem, portanto, **9 dimensões**:
```
x = [febre, tosse, garganta, dispneia, asma, diabetes, cardiopatia, saturacao, idade/100]
```

---

### 3.3 Treinamento do Modelo

#### 3.3.1 Divisão Treino / Teste (80/20)

```python
X_train, X_test, Y_train, Y_test = train_test_split(
    X, Y, test_size=0.2, random_state=42, stratify=Y
)
```

O conjunto de dados é dividido em **80% para treino** e **20% para teste** antes do ajuste do modelo. O parâmetro `stratify=Y` garante que a proporção entre casos leves e graves seja preservada em ambos os conjuntos — essencial dado o desbalanceamento natural dos dados do SIVEP-Gripe.

Esta divisão garante que a **acurácia reportada seja avaliada em dados não vistos durante o treino**, tornando a métrica honesta e representativa do desempenho real do modelo.

#### 3.3.2 Balanceamento de Classes

```python
clf = LogisticRegression(
    random_state=42,          # Semente aleatória para reprodutibilidade
    C=1.0,                    # Inverso da força de regularização L2
    solver='lbfgs',           # Otimizador quasi-Newton
    max_iter=1000,            # Iterações máximas de convergência
    class_weight='balanced'   # Compensação do desbalanceamento de classes
)
clf.fit(X_train, Y_train)
```

O parâmetro `class_weight='balanced'` faz com que o modelo atribua **pesos inversamente proporcionais à frequência de cada classe**. Nos dados do SIVEP-Gripe, casos graves são naturalmente minoria — sem esse ajuste, o modelo tenderia a classificar quase tudo como leve, obtendo acurácia numericamente alta mas clinicamente inútil.

O peso de cada classe é calculado automaticamente como:

```
wₖ = N / (K · Nₖ)
```

Onde N = total de amostras, K = número de classes (2), Nₖ = amostras da classe k.

#### 3.3.3 Avaliação no Conjunto de Teste

```python
Y_pred   = clf.predict(X_test)
accuracy = accuracy_score(Y_test, Y_pred) * 100.0
```

A acurácia é calculada via `accuracy_score` do scikit-learn **exclusivamente sobre o conjunto de teste** — dados que o modelo nunca viu durante o treinamento. Isso substitui a abordagem anterior (`clf.score(X, Y)`), que avaliava o modelo nos próprios dados de treino, produzindo métricas artificialmente infladas.

#### Parâmetro de Regularização C

O parâmetro `C = 1/λ` controla a **regularização L2** (Ridge), que adiciona uma penalidade `λ · ||w||²` à função de perda:

```
L_reg(w, b) = L(w, b) + λ · Σ wⱼ²
```

A regularização **evita overfitting** — o fenômeno em que o modelo memoriza os dados de treino mas generaliza mal para novos pacientes. Com `C=1.0`, há um equilíbrio entre ajuste aos dados e simplicidade do modelo.

---

### 3.4 Inferência (Predição)

```python
def prever_gravidade(features_list: list) -> float:
    proba = _modelo_treinado.predict_proba([features_list])[0]
    return float(proba[1] * 100.0)
```

O método `predict_proba` retorna um array `[P(Leve), P(Grave)]`. Retornamos `P(Grave) × 100` como percentual de risco de complicação. Matematicamente:

```
P(Grave) = σ(wᵀx + b) = 1 / (1 + e^(-(w·x + b)))
```

Os coeficientes `w` aprendidos pelo modelo podem ser inspecionados via `clf.coef_` e `clf.intercept_` após o treinamento.

---

### 3.5 Persistência do Modelo (`joblib`)

Após cada treinamento o modelo é salvo em `backend/modelo_treinado.joblib`. Na inicialização do servidor o arquivo é recarregado automaticamente:

```python
# Salvar
joblib.dump({"modelo": clf, "accuracy": _accuracy, "samples": _samples}, MODEL_PATH)

# Carregar (na inicialização)
if os.path.exists(MODEL_PATH):
    dados = joblib.load(MODEL_PATH)
    _modelo_treinado = dados["modelo"]
```

---

### 3.6 Endpoints da API (`api.py`)

| Método | Rota | Autenticação | Descrição |
|--------|------|-------------|-----------|
| `POST` | `/train` | Header `X-Train-Secret` | Busca dados do Supabase e treina o modelo. Retorna `accuracy` e `samples`. |
| `POST` | `/predict` | Nenhuma | Recebe sintomas em JSON e retorna probabilidade, classificação e limiares. |
| `GET` | `/status` | Nenhuma | Retorna se o modelo está treinado, acurácia atual e número de amostras. |

#### Segurança do `/train`

O endpoint de treinamento é protegido por um header secreto configurado via variável de ambiente:

```python
TRAIN_SECRET = os.environ.get("TRAIN_SECRET", "")

@app.post("/train")
def train_model(x_train_secret: str = Header(default="")):
    if TRAIN_SECRET and x_train_secret != TRAIN_SECRET:
        raise HTTPException(403, "Acesso não autorizado ao endpoint de treinamento.")
```

Sem essa proteção, qualquer requisição externa poderia disparar um retreinamento completo do modelo.

#### CORS Configurável

As origens permitidas são configuradas via variável de ambiente, evitando o `allow_origins=["*"]` em produção:

```python
_raw_origins = os.environ.get("ALLOWED_ORIGINS", "*")
ALLOWED_ORIGINS = [o.strip() for o in _raw_origins.split(",")] if _raw_origins != "*" else ["*"]
```

#### Payload do `/predict`

```json
{
  "idade": 45,
  "febre": true,
  "tosse": true,
  "dispneia": false,
  "garganta": false,
  "saturacao": false,
  "asma": false,
  "diabetes": false,
  "cardiopatia": false
}
```

#### Resposta do `/predict`

```json
{
  "probabilidadeGravidade": 32.7,
  "classificacao": "moderado",
  "limiares": {
    "grave": 60.0,
    "moderado": 30.0
  }
}
```

A resposta agora inclui `classificacao` (rótulo textual) e `limiares` (thresholds usados), centralizando toda a lógica de decisão clínica no backend. O frontend apenas exibe o que recebe, sem recalcular nada.

---

## 4. Variáveis de Ambiente (`.env`)

| Variável | Obrigatória | Descrição |
|---|---|---|
| `SUPABASE_URL` | ✅ | URL do projeto Supabase |
| `SUPABASE_KEY` | ✅ | Chave de acesso da API Supabase |
| `TRAIN_SECRET` | ✅ | Segredo para autenticar o endpoint `/train` |
| `ALLOWED_ORIGINS` | ❌ | Origens CORS permitidas (padrão: `*`) |
| `API_BASE` | ❌ | URL base do backend usada pelo frontend (padrão: `http://localhost:8000`) |

---

## 5. Fluxo Completo do Sistema

```
[Supabase REST API — tabela `srag`]
         │  (paginação: lotes de 1.000, até 50.000 registros)
         ▼
[DataFrame Pandas — normalização e limpeza de colunas]
         │
         ▼
[_extrair_features(df) — lógica isolada]
    ├── Definição do Target Y: {0: Leve, 1: Grave}
    │   (UTI=1 | EVOLUCAO=2 | SUPORT_VEN∈{1,2})
    └── Vetor X: 9 dimensões por paciente
        (FEATURE_KEYS + idade/100)
         │
         ▼
[train_test_split — 80% treino / 20% teste, stratify=Y]
         │
         ▼
[Treinamento LogisticRegression — Scikit-Learn]
    Otimizador: L-BFGS
    Perda: Entropia Cruzada Binária
    Regularização: L2 (C=1.0)
    Balanceamento: class_weight='balanced'
         │
         ▼
[Avaliação: accuracy_score(Y_test, Y_pred)]
    ← Acurácia medida em dados NÃO vistos no treino
         │
         ├─── Memória: _modelo_treinado (variável global)
         └─── Disco: modelo_treinado.joblib (joblib)
         │
         ▼
[Inferência: P(Grave|x) = σ(wᵀx + b)]
         │
         ▼
[API FastAPI retorna probabilidade + classificação + limiares]
         │
         ▼
[Dashboard Streamlit exibe resultado ao usuário]
```

---

## 6. Relação com o Perceptron Original

O código JavaScript original implementava **manualmente** um Perceptron com sigmoide e gradiente descendente:

```
Perceptron Manual (JS) → Regressão Logística (Python/Scikit-Learn)
```

A mudança **não é conceitual** — o modelo matemático é o mesmo. O que muda é:

1. **O otimizador**: De gradiente descendente ingênuo para L-BFGS, que converge mais rapidamente e de forma mais estável.
2. **A função de perda**: Formalizada como entropia cruzada, com garantias matemáticas de convexidade.
3. **A regularização**: Adicionada via parâmetro `C`, prevenindo overfitting.
4. **O balanceamento**: `class_weight='balanced'` compensa a desproporção entre casos leves e graves.
5. **A avaliação**: Separação treino/teste garante métricas honestas e representativas.
6. **A robustez**: A biblioteca `scikit-learn` lida com casos de borda numérica (overflow de `e^z`, etc.) que o código JS ignorava.

Em essência, a Regressão Logística do `scikit-learn` é um **Perceptron com sigmoide otimizado por décadas de pesquisa em otimização numérica**.

---

## 7. Referências

- Rosenblatt, F. (1958). *The Perceptron: A Probabilistic Model for Information Storage and Organization in the Brain*. Psychological Review, 65(6), 386–408.
- Bishop, C. M. (2006). *Pattern Recognition and Machine Learning*. Springer. Cap. 4 (Linear Models for Classification).
- Nocedal, J., & Wright, S. J. (2006). *Numerical Optimization* (2nd ed.). Springer. Cap. 7 (Large-Scale Unconstrained Optimization — L-BFGS).
- Ministério da Saúde do Brasil. *Dicionário de Dados SIVEP-Gripe*. DATASUS, 2023.
- Scikit-learn Developers. *sklearn.linear\_model.LogisticRegression*. https://scikit-learn.org/stable/modules/generated/sklearn.linear_model.LogisticRegression.html
- Scikit-learn Developers. *sklearn.model\_selection.train\_test\_split*. https://scikit-learn.org/stable/modules/generated/sklearn.model_selection.train_test_split.html