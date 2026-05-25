# MedTriagem IA 🩺🤖

Este projeto é uma ferramenta full-stack que utiliza **Inteligência Artificial (Regressão Logística via Scikit-Learn)** para identificar e prever preliminarmente a gravidade de possíveis quadros respiratórios de pacientes, comparando perfis e sintomas informados com dados massivos governamentais do SIVEP-Gripe (DataSUS).

A interface foi projetada como um **Dashboard Médico**, apresentando um formulário clínico interativo com feedback visual em tempo real sobre o risco do paciente.

---

## 🚀 Arquitetura do Projeto

O projeto é modular e dividido em três pilares principais:

1. **Cérebro (Backend — FastAPI)**: Uma API construída em **Python + FastAPI**, responsável por realizar o processamento dos dados via **Pandas** e treinar a Inteligência Artificial utilizando **Scikit-Learn**. O endpoint de treinamento é protegido por autenticação via header secreto. Toda a lógica de decisão clínica (classificação e limiares de gravidade) reside exclusivamente no backend.

2. **Interface Visual (Dashboard — Streamlit)**: Um dashboard interativo moderno criado com **Streamlit**, com design system externalizado em `style.css`. Guia o usuário pelas etapas de treinamento da IA, preenchimento de sintomas e visualização do diagnóstico. Inclui validação de formulário (ao menos 1 sintoma obrigatório) e cache de 3h para otimização de performance.

3. **Banco de Dados (Supabase)**: O dataset original em formato `.csv` foi migrado para o **Supabase** (PostgreSQL na nuvem), de onde a API busca os dados remotamente de forma automática via chave de API e paginação REST.

---

## 🗂️ Estrutura de Pastas

```
A3-IA/
├── backend/
│   ├── api.py            # Endpoints FastAPI (autenticação, CORS, predição)
│   ├── model.py          # Pipeline de ML (extração, treino, inferência)
│   ├── requirements.txt  # Dependências do backend
│   └── README.md         # Documentação técnica do módulo de IA
├── streamlit/
│   ├── app.py            # Aplicação principal Streamlit
│   ├── style.css         # Design system externo (tema, componentes, responsividade)
│   ├── requirements.txt  # Dependências do frontend
│   └── README.md         # Documentação do dashboard
├── dataset/              # Dataset local SIVEP-Gripe (.csv)
├── venv/                 # Ambiente virtual do backend (gerado localmente, não versionado)
├── .env                  # Variáveis de ambiente (não versionado)
└── README.md
```

---

## ⚙️ Pré-requisitos

- Python **3.10+**
- Credenciais do Supabase (URL e chave de acesso)

---

## 🔑 Configuração do Ambiente (`.env`)

Crie um arquivo `.env` na **raiz do projeto** com as variáveis abaixo:

```env
# ── Supabase (obrigatórias) ───────────────────────────────────
SUPABASE_URL="https://sua-url-do-projeto.supabase.co"
SUPABASE_KEY="sua-chave-anon-publica"

# ── Segurança (obrigatória) ───────────────────────────────────
# Protege o endpoint /train contra chamadas não autorizadas.
# Gere uma chave forte: openssl rand -hex 32
TRAIN_SECRET="sua-chave-secreta-aqui"

# ── Opcionais (possuem padrão para desenvolvimento local) ─────
ALLOWED_ORIGINS="*"
API_BASE="http://localhost:8000"
```

> ⚠️ O `TRAIN_SECRET` deve ser idêntico no backend e no Streamlit. Sem ele, o endpoint `/train` retornará erro **403 Forbidden**.

---

## 💻 Como Rodar Localmente

Para executar o projeto, você precisará de **dois terminais abertos simultaneamente** — um para o Backend e outro para o Streamlit.

---

### 🖥️ Terminal 1 — Backend (API FastAPI)

```bash
# 1. Crie o ambiente virtual (somente na primeira vez)
python3 -m venv venv

# 2. Ative o ambiente virtual
source venv/Scripts/activate    # Windows
# source venv/bin/activate      # Linux / macOS

# 3. Instale as dependências do backend
pip install -r backend/requirements.txt

# 4. Levante a API
uvicorn backend.api:app --reload
```

A API estará disponível em: **http://localhost:8000**

---

### 🌐 Terminal 2 — Dashboard (Streamlit)

Abra um **novo terminal** (mantenha o backend rodando no anterior):

```bash
# 1. Entre na pasta do Streamlit
cd streamlit

# 2. Crie o ambiente virtual do Streamlit (somente na primeira vez)
python3 -m venv venv

# 3. Ative o ambiente virtual
source venv/Scripts/activate    # Windows
# source venv/bin/activate      # Linux / macOS

# 4. Instale as dependências
pip install -r requirements.txt

# 5. Inicie o dashboard
streamlit run app.py
```

O dashboard estará disponível em: **http://localhost:8501**

---

### 🔄 Nas próximas execuções

O venv e as dependências já estarão instalados. Basta ativar e rodar:

**Backend:**
```bash
source venv/Scripts/activate && uvicorn backend.api:app --reload
```

**Streamlit:**
```bash
cd streamlit && source venv/Scripts/activate && streamlit run app.py
```

---

## 📊 Resumo dos Serviços

| Serviço | Pasta | Comando | Porta |
|---------|-------|---------|-------|
| **Backend (FastAPI)** | `backend/` | `uvicorn backend.api:app --reload` | `:8000` |
| **Dashboard (Streamlit)** | `streamlit/` | `streamlit run app.py` | `:8501` |

---

## 🧠 Lógica e Aprendizado

### Pipeline de Machine Learning

Ao abrir o dashboard, o usuário dispara o treinamento da IA. O backend:

1. Busca os dados do Supabase de forma paginada (lotes de 1.000, até 50.000 registros)
2. Extrai 9 features clínicas por paciente via `_extrair_features()`: febre, tosse, dor de garganta, dispneia, asma, diabetes, cardiopatia, saturação O₂ e idade normalizada
3. Define o target binário: `1 = Grave` (óbito, UTI ou suporte ventilatório) e `0 = Leve/Moderado`
4. Divide os dados em **80% treino / 20% teste** com estratificação por classe
5. Treina `LogisticRegression` com `class_weight='balanced'` para compensar o desbalanceamento natural entre casos leves e graves nos dados do SIVEP-Gripe
6. Avalia a acurácia **exclusivamente no conjunto de teste** — dados não vistos durante o treino
7. Persiste o modelo em disco via `joblib` para reutilização em reinicios do servidor

Este treinamento é **cacheado por 3 horas** no Streamlit, resultando em respostas quase instantâneas nas visitas seguintes.

### Inferência e Classificação

O usuário preenche o formulário com ao menos um sintoma ou comorbidade (validação obrigatória). O modelo retorna a **probabilidade de complicação grave** e o backend classifica o quadro:

| Classificação | Condição | Orientação |
|---|---|---|
| 🚨 **Grave** | prob ≥ 60% | Encaminhar imediatamente para UTI |
| ⚠️ **Moderado** | prob ≥ 30% | Avaliação médica urgente nas próximas horas |
| ✅ **Leve** | prob < 30% | Monitoramento domiciliar |

> Toda a lógica de classificação (limiares e rótulos) é definida e retornada pelo backend. O frontend apenas exibe o resultado recebido, sem recalcular nada.

### Segurança

O endpoint `/train` é protegido pelo header `X-Train-Secret`, impedindo que qualquer requisição externa dispare um retreinamento não autorizado do modelo.

---

## 🐛 Problemas Comuns

| Erro | Causa Provável | Solução |
|------|----------------|---------|
| `403 Forbidden` no `/train` | `TRAIN_SECRET` ausente ou diferente entre backend e Streamlit | Verifique se o `.env` tem o mesmo valor nos dois módulos |
| `Erro de conexão` no Streamlit | Backend FastAPI não está rodando | Suba o Terminal 1 antes de iniciar o Streamlit |
| `Erro do Backend` | Supabase offline ou credenciais inválidas | Verifique `SUPABASE_URL` e `SUPABASE_KEY` no `.env` |
| `StreamlitSecretNotFoundError` | `st.secrets` acessado sem `secrets.toml` | Normal em dev local — o código faz fallback para `os.environ` automaticamente |
| `externally-managed-environment` | Python gerenciado pelo sistema | Use sempre o ambiente virtual (`venv`) |

---

*Projeto idealizado para a disciplina e atividade prática em Inteligência Artificial (A3)*  
*Dados: SIVEP-Gripe (DataSUS) · Modelo: Scikit-Learn LogisticRegression · Backend: FastAPI*