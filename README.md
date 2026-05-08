# Triagem Respiratória IA 🩺🤖

Este projeto é uma ferramenta full-stack que utiliza **Inteligência Artificial (Regressão Logística via Scikit-Learn)** para identificar e prever preliminarmente a gravidade de possíveis quadros respiratórios de pacientes, comparando perfis e sintomas informados com dados massivos governamentais do SIVEP-Gripe (DataSUS).

A interface foi projetada como um **Dashboard Médico Premium**, apresentando um modelo anatômico 3D interativo que reage em tempo real aos sintomas (febre, dor de garganta, falta de ar, etc.).

## 🚀 Arquitetura do Projeto

O projeto é modular e dividido em três pilares principais:

1. **Cérebro (Backend - FastAPI)**: Uma API construída em **Python + FastAPI**, responsável por realizar o processamento dos dados via **Pandas** e treinar a Inteligência Artificial utilizando **Scikit-Learn**.
2. **Interface Visual (Frontend - Streamlit)**: Um dashboard interativo moderno criado com **Streamlit**, contando com gráficos avançados de saúde e um boneco 3D anatômico reativo usando propriedades visuais avançadas. Conta com mecanismo de cache de 3h para otimização de performance e redução de latência.
3. **Banco de Dados (Supabase)**: O dataset original em formato `.csv` foi migrado para o **Supabase** (PostgreSQL na nuvem), de onde a API busca os dados remotos automaticamente via chave de API e paginação REST.

## ⚙️ Pré-requisitos
- Python 3.10+
- Chave de acesso e URL do Supabase configuradas

## 💻 Como Rodar Localmente (Passo a Passo)

Para executar o projeto do zero na sua máquina, siga os passos abaixo para configurar os dois servidores (Backend FastAPI e Frontend Streamlit).

### 1. Configurar o Banco de Dados (Supabase)
Crie um arquivo `.env` na raiz do projeto (mesmo nível que a pasta `backend/`) com as suas credenciais do Supabase, que apontam para a tabela `srag` preenchida com os dados governamentais:

```env
SUPABASE_URL="https://sua-url-do-projeto.supabase.co"
SUPABASE_KEY="sua-chave-anon-publica"
```

### 2. Backend (Servidor de Inteligência FastAPI)
Abra o seu terminal na raiz do projeto e configure o ambiente Python:

```bash
# 1. Crie e ative um ambiente virtual (somente na primeira vez)
python -m venv venv

# No Windows:
venv\Scripts\activate
# (Se estiver no Linux/Mac use: source venv/bin/activate)

# 2. Instale as dependências da Inteligência Artificial
pip install -r backend/requirements.txt

# 3. Levante a API
uvicorn backend.api:app --reload
```
A API Python acordará na porta local `8000`.

### 3. Frontend (Dashboard Visual em Streamlit)
Em uma **NOVA aba de terminal** (mantenha o Backend ligado no anterior), instale as dependências visuais e rode a interface:

```bash
# Lembre-se de ativar o ambiente virtual no novo terminal também
venv\Scripts\activate 

# 1. Inicie o painel interativo do Streamlit
cd streamlit
streamlit run app.py
```
A página do dashboard médico com o modelo 3D ficará disponível no seu navegador (normalmente em `http://localhost:8501/`).

## 🧠 Lógica e Aprendizado
*   **Aprendizado e Cache Dinâmico**: Ao abrir o dashboard, o Streamlit fará uma requisição ao Backend. O Backend baixará os dados do Supabase paginados de forma progressiva (até limite estabelecido), extrairá as *features* limpas com Pandas e treinará o modelo `LogisticRegression` em memória. Este treinamento é **salvo localmente** e a chamada de rede do frontend ganha um **cache de 3 horas**, resultando em respostas quase instatâneas nas próximas visitas.
*   **Inferência Médica Visual**: Responda as perguntas no dashboard. Os órgãos 3D correspondentes (pulmões, coração, garganta) acenderão com efeitos de "Glow", simulando o mapeamento termográfico e inflamatório do corpo. Simultaneamente, o Frontend consome o Backend e exibe o "Nível de Risco" (em %) de complicação (Internação/UTI/Óbito), auxiliando visualmente a triagem de pacientes de alto risco.

---
*Projeto idealizado para a disciplina e atividade prática em Inteligência Artificial (A3)*
