import os
import requests
import streamlit as st
from dotenv import load_dotenv

load_dotenv()


# ── Ambiente ──────────────────────────────────────────────────
def _secret(key: str, default: str) -> str:
    if val := os.environ.get(key):
        return val
    try:
        return st.secrets[key]
    except Exception:
        return default

API_BASE     = _secret("API_BASE",     "http://localhost:8000")
TRAIN_SECRET = _secret("TRAIN_SECRET", "")


# ── Config da página ──────────────────────────────────────────
st.set_page_config(
    page_title="MedTriagem IA",
    page_icon="🩺",
    layout="centered",
    initial_sidebar_state="collapsed",
    menu_items=None
)


# ── Design system externo ─────────────────────────────────────
def _load_css(path: str):
    with open(path, encoding="utf-8") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

_load_css(os.path.join(os.path.dirname(__file__), "style.css"))


# ── Estado da sessão ──────────────────────────────────────────
for key, default in [("step", "train"), ("trainedModel", None), ("resultado", None)]:
    if key not in st.session_state:
        st.session_state[key] = default


# ── Header global (todas as telas) ───────────────────────────
st.markdown("""
<div class="med-header">
    <span class="med-header-icon">🩺</span>
    <div>
        <p class="med-header-title">MedTriagem IA</p>
        <p class="med-header-sub">Triagem Respiratória · SIVEP-Gripe · DataSUS</p>
    </div>
</div>
""", unsafe_allow_html=True)

if st.session_state.trainedModel:
    m = st.session_state.trainedModel
    st.markdown(
        f'<div class="status-badge">'
        f'<span class="status-dot"></span>'
        f'IA ATIVA &nbsp;·&nbsp; {m["samples"]:,} pacientes &nbsp;·&nbsp; acurácia {m["accuracy"]:.1f}%'
        f'</div>',
        unsafe_allow_html=True,
    )


# ── Funções auxiliares ────────────────────────────────────────
@st.cache_data(ttl=10800, show_spinner=False)
def fetch_and_train(secret: str):
    headers = {"X-Train-Secret": secret} if secret else {}
    r = requests.post(f"{API_BASE}/train", headers=headers, timeout=300)
    r.raise_for_status()
    return r.json()


def handle_train():
    try:
        with st.spinner("Conectando ao backend e treinando o modelo..."):
            data = fetch_and_train(TRAIN_SECRET)
            st.session_state.trainedModel = {
                "accuracy": data.get("accuracy"),
                "samples":  data.get("samples"),
            }
            st.session_state.step = "form"
    except requests.exceptions.HTTPError as e:
        try:
            detail = e.response.json().get("detail", str(e))
        except Exception:
            detail = str(e)
        st.error(f"Erro do Backend: {detail}")
        st.cache_data.clear()
    except Exception as e:
        st.error(f"Erro de conexão: {e}")
        st.cache_data.clear()


def _label_sintoma(key: str) -> str:
    return {
        "febre":       "🌡️ Febre",
        "tosse":       "😮‍💨 Tosse",
        "dispneia":    "💨 Falta de Ar",
        "garganta":    "🔴 Dor de Garganta",
        "saturacao":   "🩸 Sat. O₂ < 95%",
        "asma":        "🌬️ Asma",
        "diabetes":    "💉 Diabetes",
        "cardiopatia": "❤️ Cardiopatia",
    }.get(key, key)

def render_footer():
    st.markdown("""
    <div class="med-caption">
        ⚕️ Ferramenta de apoio clínico — não substitui avaliação médica presencial.<br>
        Dados: SIVEP-Gripe (DataSUS) · Modelo: Regressão Logística (Scikit-Learn) · Backend: FastAPI
    </div>
    """, unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════
# TELA: TREINAR
# ══════════════════════════════════════════════════════════════
if st.session_state.step == "train":

    st.markdown("""
    <div class="hero-section">
        <p class="hero-eyebrow">Sistema de Diagnóstico Respiratório</p>
        <h1 class="hero-title">Triagem Clínica<br><span>com Inteligência Artificial</span></h1>
        <p class="hero-desc">
            Acesse o sistema de diagnóstico respiratório treinado com dados reais do SIVEP-Gripe (DataSUS).
        </p>
    </div>
    """, unsafe_allow_html=True)

    if st.button("⚡  Iniciar Treinamento da IA →", type="primary"):
        handle_train()
        st.rerun()

    st.markdown("""
    <div class="metrics-row">
        <div class="metric-card">
            <div class="metric-card-label">Algoritmo</div>
            <div class="metric-card-value metric-card-accent">Reg. Logística</div>
        </div>
        <div class="metric-card">
            <div class="metric-card-label">Dataset</div>
            <div class="metric-card-value">SIVEP-Gripe</div>
        </div>
        <div class="metric-card">
            <div class="metric-card-label">Backend</div>
            <div class="metric-card-value">FastAPI</div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    render_footer()
    
# ══════════════════════════════════════════════════════════════
# TELA: FORMULÁRIO
# ══════════════════════════════════════════════════════════════
elif st.session_state.step == "form":

    st.markdown("""
    <div class="form-title">Avaliação do Paciente</div>
    <div class="form-subtitle">Preencha os dados clínicos para análise pela IA</div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="form-section-title">Dados Básicos</div>', unsafe_allow_html=True)
    col_input, col_badge = st.columns([4, 1])
    with col_input:
        idade = st.number_input("Idade do Paciente (anos)", min_value=0, max_value=120, value=45, step=1)
    with col_badge:
        st.markdown(
            f'<div class="idade-badge">'
            f'<span class="idade-valor">{idade}</span>'
            f'<span class="idade-label">anos</span>'
            f'</div>',
            unsafe_allow_html=True,
        )

    st.markdown('<div class="form-section-title">Sintomas Principais</div>', unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1:
        febre    = st.checkbox("🌡️ Febre")
        tosse    = st.checkbox("😮‍💨 Tosse")
        dispneia = st.checkbox("💨 Falta de Ar / Dispneia")
    with c2:
        garganta  = st.checkbox("🔴 Dor de Garganta")
        saturacao = st.checkbox("🩸 Saturação O₂ < 95%")

    st.markdown('<div class="form-section-title">Comorbidades</div>', unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3)
    asma        = c1.checkbox("🌬️ Asma")
    diabetes    = c2.checkbox("💉 Diabetes")
    cardiopatia = c3.checkbox("❤️ Cardiopatia")

    st.write("")

    # Validação: ao menos 1 sintoma ou comorbidade deve estar marcado
    algum_selecionado = any([febre, tosse, dispneia, garganta, saturacao, asma, diabetes, cardiopatia])

    if not algum_selecionado:
        st.markdown("""
        <div style="
            background: rgba(245,158,11,0.08);
            border: 1px solid rgba(245,158,11,0.25);
            border-radius: 14px;
            padding: 14px 18px;
            font-size: 0.88rem;
            color: #92400e;
            font-family: 'JetBrains Mono', monospace;
            margin-bottom: 30px;
        ">
            ⚠️ Selecione ao menos um sintoma ou comorbidade para prosseguir.
        </div>
        """, unsafe_allow_html=True)

    if st.button("Analisar com IA →", type="primary", disabled=not algum_selecionado):
        form_data = {
            "idade": idade, "febre": febre, "tosse": tosse,
            "garganta": garganta, "dispneia": dispneia, "saturacao": saturacao,
            "asma": asma, "diabetes": diabetes, "cardiopatia": cardiopatia,
        }
        prob_gravidade = 0.0
        classificacao  = "leve"
        limiares       = {"grave": 60.0, "moderado": 30.0}
        erro_backend   = None

        try:
            resp = requests.post(f"{API_BASE}/predict", json=form_data, timeout=15)
            resp.raise_for_status()
            payload        = resp.json()
            prob_gravidade = payload.get("probabilidadeGravidade", 0.0)
            classificacao  = payload.get("classificacao", "leve")
            limiares       = payload.get("limiares", limiares)
        except Exception as e:
            erro_backend = str(e)

        st.session_state.resultado = {
            "probabilidadeGravidade": prob_gravidade,
            "classificacao":          classificacao,
            "limiares":               limiares,
            "formData":               form_data,
            "erroBackend":            erro_backend,
        }
        st.session_state.step = "result"
        st.rerun()
        
    render_footer()

# ══════════════════════════════════════════════════════════════
# TELA: RESULTADO
# ══════════════════════════════════════════════════════════════
elif st.session_state.step == "result":
    resultado     = st.session_state.resultado
    prob          = resultado["probabilidadeGravidade"]
    classificacao = resultado["classificacao"]
    fd            = resultado["formData"]

    if resultado.get("erroBackend"):
        st.error(f"⚠️ Não foi possível consultar a IA: {resultado['erroBackend']}")

    cfg = {
        "grave":    ("result-grave",    "result-label-grave",    "🚨", "QUADRO GRAVE",    "Risco elevado de internação ou UTI. Encaminhar imediatamente."),
        "moderado": ("result-moderado", "result-label-moderado", "⚠️", "QUADRO MODERADO", "Avaliação médica urgente recomendada nas próximas horas."),
        "leve":     ("result-leve",     "result-label-leve",     "✅", "QUADRO LEVE",     "Monitoramento domiciliar recomendado. Retornar se piorar."),
    }.get(classificacao, ("result-leve", "result-label-leve", "✅", "QUADRO LEVE", ""))

    card_cls, label_cls, icon, label, desc = cfg
    bar_pct = min(prob, 100)

    st.markdown(f"""
    <div class="result-card {card_cls}">
        <div class="result-icon">{icon}</div>
        <div class="result-label {label_cls}">{label}</div>
        <div class="result-title">{desc}</div>
    </div>
    """, unsafe_allow_html=True)

    c1, c2 = st.columns([2, 3])
    with c1:
        st.markdown(f"""
        <div style="padding:20px 0 8px;">
            <div class="prob-value">{prob:.1f}%</div>
            <div class="prob-label">chance de complicação grave</div>
        </div>
        """, unsafe_allow_html=True)
    with c2:
        st.markdown(f"""
        <div style="padding:28px 0 8px;">
            <div class="prob-bar-wrap">
                <div class="prob-bar-fill prob-bar-{classificacao}" style="width:{bar_pct}%"></div>
            </div>
            <div class="prob-scale">
                <span>0%</span><span>Leve</span><span>Moderado</span><span>100%</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown('<div class="form-section-title">Perfil do Paciente</div>', unsafe_allow_html=True)
    st.markdown(f"**Idade:** {fd['idade']} anos")

    st.markdown('<div class="form-section-title">Sintomas e Comorbidades informados</div>', unsafe_allow_html=True)
    sintomas_marcados = [
        _label_sintoma(k)
        for k in ["febre", "tosse", "dispneia", "garganta", "saturacao", "asma", "diabetes", "cardiopatia"]
        if fd.get(k)
    ]

    if sintomas_marcados:
        tags_html = "".join(f'<span class="sintoma-tag">{s}</span>' for s in sintomas_marcados)
        st.markdown(f'<div class="tags-wrap">{tags_html}</div>', unsafe_allow_html=True)
    else:
        st.markdown('<p style="color:#475569;font-size:0.88rem;">Nenhum sintoma ou comorbidade informado.</p>', unsafe_allow_html=True)
        
    st.markdown('<div class="section-spacing"></div>', unsafe_allow_html=True)

    st.write("")
    if st.button("← Nova Avaliação"):
        st.session_state.step      = "form"
        st.session_state.resultado = None
        st.rerun()

    render_footer()