# 🩺 Triagem Respiratória IA — Dashboard Streamlit

Interface visual interativa do sistema de **triagem clínica respiratória**, construída com **Streamlit**. Este painel consome a API FastAPI do backend para treinar e executar o modelo de Inteligência Artificial, apresentando os resultados de forma clara e acessível.

---

## 📋 Visão Geral

O dashboard é dividido em **três telas sequenciais**:

| Tela | Descrição |
|------|-----------|
| 🚀 **Treinamento** | Dispara o treinamento da IA com dados reais do SIVEP-Gripe via backend |
| 📝 **Formulário** | Coleta idade, sintomas e comorbidades do paciente |
| 📊 **Resultado** | Exibe o diagnóstico com nível de risco de complicação grave |

---

## 🗂️ Estrutura de Arquivos

```
streamlit/
├── app.py            # Aplicação principal do Streamlit
├── requirements.txt  # Dependências Python do módulo
├── venv/             # Ambiente virtual (gerado localmente, não versionado)
└── README.md         # Este arquivo
```

---

## ⚙️ Pré-requisitos

- Python **3.10+**
- Backend FastAPI rodando em `http://localhost:8000` *(obrigatório)*

> ⚠️ **Importante:** O Streamlit depende inteiramente do backend para treinar o modelo e gerar previsões. Certifique-se de que a API está ativa antes de iniciar o dashboard.

---

## 🚀 Como Rodar

### 1. Entre na pasta do módulo

```bash
cd streamlit
```

### 2. Crie e ative o ambiente virtual

> Faça isso apenas na **primeira vez** ou se a pasta `venv/` não existir.

```bash
# Criar o venv
python3 -m venv venv

# Ativar (Linux / macOS)
source venv/bin/activate

# Ativar (Windows)
venv\Scripts\activate
```

### 3. Instale as dependências

Com o venv ativo, instale os pacotes necessários:

```bash
pip install -r requirements.txt
```

### 4. Inicie o dashboard

```bash
streamlit run app.py
```

O painel estará disponível em: **http://localhost:8501**

---

## 🔄 Nas próximas vezes

Nas execuções seguintes, basta ativar o venv e rodar:

```bash
source venv/bin/activate   # Linux/macOS
streamlit run app.py
```

---

## 📦 Dependências (`requirements.txt`)

| Pacote | Função |
|--------|--------|
| `streamlit` | Framework para criação do dashboard interativo |
| `requests` | Comunicação HTTP com a API FastAPI do backend |

---

## 🧠 Fluxo da Aplicação

```
Usuário abre o dashboard
        │
        ▼
[Tela 1] Clica em "Iniciar Treinamento"
        │
        ▼
Streamlit faz POST /train → FastAPI
        │  (dados SIVEP-Gripe via Supabase)
        ▼
Modelo LogisticRegression treinado
Resultado em cache por 3 horas ⚡
        │
        ▼
[Tela 2] Formulário de Sintomas
  • Idade (slider)
  • Sintomas: Febre, Tosse, Falta de Ar, Dor de Garganta, Sat. O₂ < 95%
  • Comorbidades: Asma, Diabetes, Cardiopatia
        │
        ▼
Streamlit faz POST /predict → FastAPI
        │
        ▼
[Tela 3] Resultado do Diagnóstico
  🚨 Grave    → prob ≥ 60%
  ⚠️ Moderado → prob ≥ 30%
  ✅ Leve     → prob < 30%
  🛡️ Sem Indícios → sem sintomas relevantes
```

---

## 🔗 Endpoints Consumidos

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| `POST` | `/train` | Treina o modelo com os dados do Supabase |
| `POST` | `/predict` | Retorna a probabilidade de complicação grave |

A URL base da API é configurada diretamente no código:

```python
API_BASE = "http://localhost:8000"
```

---

## ⚡ Cache de Performance

O Streamlit utiliza `@st.cache_data` com TTL de **3 horas** para o resultado do treinamento, evitando chamadas desnecessárias ao backend e reduzindo latência nas visitas subsequentes.

```python
@st.cache_data(ttl=10800, show_spinner=False)
def fetch_and_train():
    r = requests.post(f"{API_BASE}/train")
    ...
```

Para forçar um novo treinamento antes do cache expirar, reinicie o servidor Streamlit.

---

## 🐛 Problemas Comuns

| Erro | Causa Provável | Solução |
|------|----------------|---------|
| `command not found: streamlit` | Venv não ativado ou deps não instaladas | Ative o venv e rode `pip install -r requirements.txt` |
| `Erro de conexão: ...` | Backend FastAPI não está rodando | Suba a API antes de iniciar o Streamlit |
| `Erro do Backend: ...` | Problema interno na API (ex: Supabase offline) | Verifique as variáveis de ambiente `.env` e os logs do backend |
| `externally-managed-environment` | Python gerenciado pelo sistema | Use sempre o ambiente virtual (`venv`) |

---

## 🏗️ Arquitetura Completa

Este módulo faz parte de um projeto full-stack. Para rodar o sistema completo:

| Serviço | Comando | Porta |
|---------|---------|-------|
| **Backend (FastAPI)** | `uvicorn backend.api:app --reload` | `:8000` |
| **Streamlit** | `streamlit run app.py` | `:8501` |
| **Frontend (React/Vite)** | `npm run dev` (em `frontend/`) | `:5173` |

Consulte o [README principal](../README.md) para instruções completas de configuração do ambiente.

---

*⚕️ Ferramenta de apoio clínico — não substitui avaliação médica profissional.*  
*Dados: SIVEP-Gripe (DataSUS) · Modelo: Scikit-Learn LogisticRegression*
