# Triagem Respiratória IA 🩺🤖

Este projeto é uma ferramenta full-stack que utiliza **Inteligência Artificial (Regressão Logística)** para identificar e prever preliminarmente a gravidade de possíveis quadros respiratórios de pacientes, comparando perfis e sintomas informados por você com dados massivos governamentais do SIVEP-Gripe (DataSUS).

## 🚀 Arquitetura do Projeto

O projeto é modular e dividido em duas engrenagens principais:

1.  **Cérebro (Backend)**: Uma API construída em **Python + FastAPI**, responsável por fazer o processamento limpo dos dados via **Pandas** e treinar a Inteligência Artificial diretamente via **Scikit-Learn**.
2.  **Interface visual (Frontend)**: Uma aplicação leve construída com **React + Vite** e lindamente pintada com **Tailwind CSS v4**, enviando e recebendo as informações clínicas da API.

## ⚙️ Pré-requisitos
- Python 3.10+
- Node.js e npm

## 💻 Como Rodar Localmente (Passo a Passo)

Para executar o projeto do zero na sua máquina, siga os passos abaixo para configurar os dois servidores (Backend e Frontend).

### 0. Clone e Prepare o Dataset

> ⚠️ **O arquivo de dataset não está incluído no repositório** (arquivo muito grande, ~50MB). Você precisa baixá-lo manualmente e colocá-lo na pasta correta.

```bash
# Clone o projeto
git clone https://github.com/usuario/A3-IA.git
cd A3-IA

# Crie a pasta do dataset
mkdir dataset
```

Em seguida, acesse o portal do **OpenDataSUS** e baixe o arquivo CSV do SIVEP-Gripe:
- 🔗 https://opendatasus.saude.gov.br/dataset/srag-2021-a-2024

Após o download, mova o arquivo `.csv` para dentro da pasta `dataset/`:
```
A3-IA/
└── dataset/
    └── INFLUD24-XX-XX-XXXX.csv   ← coloque aqui
```

### 1. Backend (Servidor de Inteligência)
Abra o seu terminal na raiz do projeto (`A3-IA`) e configure o ambiente Python:
```bash
# 1. Crie um ambiente virtual (somente na primeira vez)
python -m venv venv

# 2. Ative o ambiente virtual
# No Linux/Mac:
source venv/bin/activate
# No Windows:
venv\Scripts\activate

# 3. Instale as dependências de IA (Pandas, Scikit-Learn e FastAPI)
pip install -r backend/requirements.txt

# 4. Levante a API
uvicorn backend.api:app --reload
```
A API Python acordará na porta local `8000`.

### 2. Frontend (Aplicação Visual)
Em uma **NOVA aba de terminal** (mantenha o Backend ligado no anterior), vá para a pasta frontend e sirva o website:
```bash
cd frontend

# 1. Instale os pacotes NodeJS (somente na primeira vez)
npm install

# 2. Acorde o app web local
npm run dev
```
A página final do programa ficará disponível para você clicar no seu terminal, normalmente em `http://localhost:5173/`.

## 🧠 Lógica e Aprendizado
*   **Aprendizado (Treinamento)**: Ao acessar a Interface rodando no seu navegador, clique no botão de Treinamento. O Backend em Python usará o Pandas para engolir instantaneamente o Dataset local hospedado no servidor, extraindo o Alvo (O paciente precisou de UTI ou Intubação?) e treinando o algoritmo na memória.
*   **Inferência (Diagnóstico)**: Responda as perguntas simulando um novo paciente e obtenha uma medição imediata da rede de Machine Learning (em %) indicando qual seria o desfecho provável deste paciente, guiando as prioridades médicas.

---
*Projeto idealizado para a disciplina e atividade prática em Inteligência Artificial (A3)*
