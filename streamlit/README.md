# 🩺 MedTriagem IA — Dashboard Streamlit

Interface visual interativa do sistema de **triagem clínica respiratória**, construída com **Streamlit**. Este painel consome a API FastAPI do backend para treinar e executar o modelo de Inteligência Artificial, apresentando os resultados de forma clara e acessível.

---

## 📋 Visão Geral

O dashboard é dividido em **três telas sequenciais**:

| Tela | Descrição |
|------|-----------|
| 🚀 **Treinamento** | Dispara o treinamento da IA com dados reais do SIVEP-Gripe via backend |
| 📝 **Formulário** | Coleta idade, sintomas e comorbidades do paciente — ao menos 1 item obrigatório |
| 📊 **Resultado** | Exibe o diagnóstico com nível de risco, probabilidade e perfil do paciente |

---

## 🗂️ Estrutura de Arquivos

```
streamlit/
├── app.py            # Aplicação principal do Streamlit
├── style.css         # Design system externo (tema, componentes, responsividade)
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

### 3. Configure as variáveis de ambiente

Crie um arquivo `.env` na raiz do projeto (ao lado do `backend/`) com as seguintes variáveis:

```env
SUPABASE_URL="https://xxxx.supabase.co"
SUPABASE_KEY="sua_chave_aqui"
TRAIN_SECRET="sua_chave_secreta_aqui"

# Opcionais (possuem valores padrão para desenvolvimento local)
ALLOWED_ORIGINS="*"
API_BASE="http://localhost:8000"
```

> O `TRAIN_SECRET` deve ser idêntico ao configurado no backend. Sem ele, o endpoint `/train` retornará erro 403.

### 4. Instale as dependências

Com o venv ativo, instale os pacotes necessários:

```bash
pip install -r requirements.txt
```

### 5. Inicie o dashboard

```bash
streamlit run app.py
```

O painel estará disponível em: **http://localhost:8501**

---

## 🔄 Nas próximas vezes

Nas execuções seguintes, basta ativar o venv e rodar:

```bash
source venv/bin/activate   # Linux/macOS
venv\Scripts\activate      # Windows
streamlit run app.py
```

---

## 📦 Dependências (`requirements.txt`)

| Pacote | Função |
|--------|--------|
| `streamlit` | Framework para criação do dashboard interativo |
| `requests` | Comunicação HTTP com a API FastAPI do backend |
| `python-dotenv` | Leitura das variáveis de ambiente do arquivo `.env` |

---

## 🎨 Design System (`style.css`)

O design visual está completamente **externalizado** em `style.css`, separando responsabilidades: o `app.py` contém apenas lógica Python, enquanto o CSS concentra todo o sistema de design.

O arquivo é carregado dinamicamente no início da aplicação:

```python
def _load_css(path: str):
    with open(path, encoding="utf-8") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

_load_css(os.path.join(os.path.dirname(__file__), "style.css"))
```

**Características do tema:**
- Fundo light premium com gradiente suave (`#f8fbff → #eef5ff`)
- Tipografia: `Inter` (interface) + `JetBrains Mono` (dados técnicos)
- Componentes: header flutuante, badge animado, cards com acento colorido, tags pill
- Responsivo para telas a partir de 768px

---

## 🔐 Configuração de Ambiente

As variáveis sensíveis são lidas com prioridade via `os.environ` (`.env`) e fallback para `st.secrets` (produção no Streamlit Cloud):

```python
def _secret(key: str, default: str) -> str:
    if val := os.environ.get(key):
        return val
    try:
        return st.secrets[key]
    except Exception:
        return default

API_BASE     = _secret("API_BASE",     "http://localhost:8000")
TRAIN_SECRET = _secret("TRAIN_SECRET", "")
```

Em produção, defina as variáveis em `~/.streamlit/secrets.toml` ou nas configurações do Streamlit Cloud.

---

## 🧠 Fluxo da Aplicação

```
Usuário abre o dashboard
        │
        ▼
[Tela 1] Clica em "Iniciar Treinamento da IA"
        │
        ▼
Streamlit faz POST /train
  Header: X-Train-Secret → FastAPI autentica
        │  (dados SIVEP-Gripe via Supabase)
        ▼
Modelo LogisticRegression treinado
Resultado em cache por 3 horas ⚡
        │
        ▼
[Tela 2] Formulário de Sintomas
  • Idade (slider: 0–100 anos)
  • Sintomas: Febre, Tosse, Falta de Ar, Dor de Garganta, Sat. O₂ < 95%
  • Comorbidades: Asma, Diabetes, Cardiopatia
  ⚠️ Ao menos 1 item obrigatório — botão desabilitado se nenhum marcado
        │
        ▼
Streamlit faz POST /predict → FastAPI
  (todos os perfis enviados ao modelo, sem pré-filtro no frontend)
        │
        ▼
[Tela 3] Resultado do Diagnóstico
  🚨 Grave    → prob ≥ 60%
  ⚠️ Moderado → prob ≥ 30%
  ✅ Leve     → prob < 30%
  (limiares definidos e retornados pelo backend)
```

---

## 🔗 Endpoints Consumidos

| Método | Endpoint | Header obrigatório | Descrição |
|--------|----------|--------------------|-----------|
| `POST` | `/train` | `X-Train-Secret` | Treina o modelo com os dados do Supabase |
| `POST` | `/predict` | — | Retorna probabilidade, classificação e limiares |

**Resposta do `/predict`:**
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

> A classificação e os limiares são definidos **exclusivamente pelo backend**. O frontend apenas exibe o que recebe, sem recalcular nem filtrar.

---

## ✅ Validação do Formulário

O botão "Analisar com IA" permanece **desabilitado** enquanto nenhum sintoma ou comorbidade estiver marcado:

```python
algum_selecionado = any([febre, tosse, dispneia, garganta,
                         saturacao, asma, diabetes, cardiopatia])

if not algum_selecionado:
    # exibe aviso visual
    
if st.button("Analisar com IA →", type="primary", disabled=not algum_selecionado):
    ...
```

Isso garante que o modelo sempre receba ao menos um sinal clínico, evitando previsões baseadas exclusivamente na idade.

---

## ⚡ Cache de Performance

O Streamlit utiliza `@st.cache_data` com TTL de **3 horas** para o resultado do treinamento, evitando chamadas desnecessárias ao backend. O `secret` é incluído como parâmetro da função cacheada para garantir invalidação automática em caso de mudança de credencial:

```python
@st.cache_data(ttl=10800, show_spinner=False)
def fetch_and_train(secret: str):
    headers = {"X-Train-Secret": secret} if secret else {}
    r = requests.post(f"{API_BASE}/train", headers=headers, timeout=300)
    r.raise_for_status()
    return r.json()
```

Para forçar um novo treinamento antes do cache expirar, reinicie o servidor Streamlit.

---

## 🐛 Problemas Comuns

| Erro | Causa Provável | Solução |
|------|----------------|---------|
| `command not found: streamlit` | Venv não ativado ou deps não instaladas | Ative o venv e rode `pip install -r requirements.txt` |
| `Erro de conexão: ...` | Backend FastAPI não está rodando | Suba a API antes de iniciar o Streamlit |
| `403 Forbidden` no `/train` | `TRAIN_SECRET` ausente ou divergente do backend | Verifique se o `.env` tem o mesmo valor em ambos os módulos |
| `Erro do Backend: ...` | Problema interno na API (ex: Supabase offline) | Verifique as variáveis de ambiente `.env` e os logs do backend |
| `StreamlitSecretNotFoundError` | `st.secrets` acessado sem `secrets.toml` | Normal em dev local — o código faz fallback para `os.environ` automaticamente |
| `externally-managed-environment` | Python gerenciado pelo sistema | Use sempre o ambiente virtual (`venv`) |

---

## 🏗️ Arquitetura Completa

Este módulo faz parte de um projeto full-stack. Para rodar o sistema completo:

| Serviço | Comando | Porta |
|---------|---------|-------|
| **Backend (FastAPI)** | `uvicorn backend.api:app --reload` | `:8000` |
| **Streamlit** | `streamlit run app.py` | `:8501` |

Consulte o [README principal](../README.md) para instruções completas de configuração do ambiente.

---

*⚕️ Ferramenta de apoio clínico — não substitui avaliação médica profissional.*  
*Dados: SIVEP-Gripe (DataSUS) · Modelo: Scikit-Learn LogisticRegression · Backend: FastAPI*