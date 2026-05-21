# Triagem Respiratória IA 🩺🤖

Este projeto é uma ferramenta full-stack que utiliza **Inteligência Artificial (Regressão Logística via Scikit-Learn)** para identificar e prever preliminarmente a gravidade de possíveis quadros respiratórios de pacientes, comparando perfis e sintomas informados com dados massivos governamentais do SIVEP-Gripe (DataSUS).

A interface foi projetada como um **Dashboard Médico**, apresentando um formulário clínico interativo com feedback visual em tempo real sobre o risco do paciente.

---

## 🚀 Arquitetura do Projeto

O projeto é modular e dividido em três pilares principais:

1. **Cérebro (Backend — FastAPI)**: Uma API construída em **Python + FastAPI**, responsável por realizar o processamento dos dados via **Pandas** e treinar a Inteligência Artificial utilizando **Scikit-Learn**.
2. **Interface Visual (Dashboard — Streamlit)**: Um dashboard interativo moderno criado com **Streamlit**, que guia o usuário pelas etapas de treinamento da IA, preenchimento de sintomas e visualização do diagnóstico. Conta com mecanismo de cache de 3h para otimização de performance e redução de latência.
3. **Banco de Dados (Supabase)**: O dataset original em formato `.csv` foi migrado para o **Supabase** (PostgreSQL na nuvem), de onde a API busca os dados remotamente de forma automática via chave de API e paginação REST.

### 🗂️ Estrutura de Pastas

```
A3-IA/
├── backend/       # API FastAPI + modelo de IA (Scikit-Learn)
├── streamlit/     # Dashboard visual (Streamlit)
├── dataset/       # Dataset local SIVEP-Gripe (.csv)
├── venv/          # Ambiente virtual do backend (gerado localmente)
├── .env           # Variáveis de ambiente (não versionado)
└── README.md
```

---

## ⚙️ Pré-requisitos

- Python **3.10+**
- Chave de acesso e URL do Supabase configuradas no arquivo `.env`

---

## 🔑 Configuração do Banco de Dados (Supabase)

Crie um arquivo `.env` na **raiz do projeto** com as suas credenciais do Supabase, que apontam para a tabela `srag` preenchida com os dados governamentais:

```env
SUPABASE_URL="https://sua-url-do-projeto.supabase.co"
SUPABASE_KEY="sua-chave-anon-publica"
```

---

## 💻 Como Rodar Localmente (Passo a Passo)

Para executar o projeto, você precisará de **dois terminais abertos simultaneamente** — um para o Backend e outro para o Streamlit.

---

### 🖥️ Terminal 1 — Backend (API FastAPI)

```bash
# 1. Crie o ambiente virtual (somente na primeira vez)
python3 -m venv venv

# 2. Ative o ambiente virtual
source venv/bin/activate        # Linux / macOS
# venv\Scripts\activate         # Windows

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
source venv/bin/activate        # Linux / macOS
# venv\Scripts\activate         # Windows

# 4. Instale as dependências do Streamlit
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
source venv/bin/activate && uvicorn backend.api:app --reload
```

**Streamlit:**
```bash
cd streamlit && source venv/bin/activate && streamlit run app.py
```

---

## 📊 Resumo dos Serviços

| Serviço | Pasta | Comando | Porta |
|---------|-------|---------|-------|
| **Backend (FastAPI)** | `backend/` | `uvicorn backend.api:app --reload` | `:8000` |
| **Dashboard (Streamlit)** | `streamlit/` | `streamlit run app.py` | `:8501` |

---

## 🧠 Lógica e Aprendizado

- **Treinamento e Cache Dinâmico**: Ao abrir o dashboard, o usuário dispara o treinamento da IA. O Backend baixa os dados do Supabase de forma paginada, extrai as *features* com Pandas e treina o modelo `LogisticRegression` em memória. Este treinamento é **cacheado por 3 horas** no Streamlit, resultando em respostas quase instantâneas nas visitas seguintes.
- **Inferência Médica**: O usuário preenche o formulário com sintomas (febre, tosse, falta de ar, saturação O₂, etc.) e comorbidades (asma, diabetes, cardiopatia). O modelo retorna a **probabilidade de complicação grave** (internação / UTI / óbito), classificando o quadro como Leve, Moderado ou Grave.

---

*Projeto idealizado para a disciplina e atividade prática em Inteligência Artificial (A3)*  
*Dados: SIVEP-Gripe (DataSUS) · Modelo: Scikit-Learn LogisticRegression*
