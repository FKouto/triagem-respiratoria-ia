import streamlit as st
import requests

API_BASE = "http://localhost:8000"

st.set_page_config(page_title="Triagem Respiratória IA", page_icon="🩺", layout="centered")

st.markdown("""<style>
.stButton>button { width:100%; border-radius:12px; padding:.75rem 1rem; font-weight:bold; }
.main-title {
    text-align:center;
    background:-webkit-linear-gradient(45deg,#3b82f6,#06b6d4);
    -webkit-background-clip:text; -webkit-text-fill-color:transparent;
    font-weight:800; font-size:3rem; margin-bottom:0;
}
.sub-title { text-align:center; color:#64748b; font-size:1.2rem; margin-bottom:2rem; }
</style>""", unsafe_allow_html=True)

for key, default in [("step", "train"), ("trainedModel", None), ("resultado", None)]:
    if key not in st.session_state:
        st.session_state[key] = default

col1, col2 = st.columns([1, 10])
with col1:
    st.markdown("## 🩺")
with col2:
    st.markdown("**Triagem Respiratória**  \n*Powered by Python AI*")

if st.session_state.trainedModel:
    st.success(f"IA Ativa · {st.session_state.trainedModel['samples']:,} pacientes")

st.divider()


@st.cache_data(ttl=10800, show_spinner=False)
def fetch_and_train():
    r = requests.post(f"{API_BASE}/train")
    r.raise_for_status()
    return r.json()


def handle_train():
    try:
        with st.spinner("Treinando IA com dados SIVEP-Gripe (cache 3h)..."):
            data = fetch_and_train()
            st.session_state.trainedModel = {
                "accuracy": data.get("accuracy"),
                "samples": data.get("samples")
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


# ─── TELA: TREINAR ───────────────────────────────────────────

if st.session_state.step == "train":
    st.markdown('<p class="main-title">Inteligência Artificial</p>', unsafe_allow_html=True)
    st.markdown('<p class="sub-title">para Triagem Clínica</p>', unsafe_allow_html=True)
    st.markdown(
        "<p style='text-align:center;color:gray;'>"
        "Sistema de diagnóstico respiratório treinado com dados reais do SIVEP-Gripe (DataSUS)."
        "</p>", unsafe_allow_html=True
    )
    st.write("")
    if st.button("🚀 Iniciar Treinamento da IA", type="primary"):
        handle_train()
        st.rerun()
    st.write("---")
    c1, c2, c3 = st.columns(3)
    c1.metric("Algoritmo", "Reg. Logística")
    c2.metric("Dataset", "SIVEP-Gripe")
    c3.metric("Backend", "FastAPI")


# ─── TELA: FORMULÁRIO ────────────────────────────────────────

elif st.session_state.step == "form":
    st.header("Formulário de Sintomas")
    st.markdown("Preencha as informações do paciente para avaliação pela IA.")

    st.subheader("Informações Básicas")
    idade = st.slider("Idade do Paciente (anos)", 0, 100, 45)

    st.subheader("Sintomas Principais")
    c1, c2 = st.columns(2)
    with c1:
        febre     = st.checkbox("🌡️ Febre")
        tosse     = st.checkbox("😮‍💨 Tosse")
        dispneia  = st.checkbox("💨 Falta de Ar")
    with c2:
        garganta  = st.checkbox("🔴 Dor de Garganta")
        saturacao = st.checkbox("🩸 Sat. O₂ < 95%")

    st.subheader("Comorbidades")
    c1, c2, c3 = st.columns(3)
    asma        = c1.checkbox("🌬️ Asma")
    diabetes    = c2.checkbox("💉 Diabetes")
    cardiopatia = c3.checkbox("❤️ Cardiopatia")

    st.write("")
    if st.button("Gerar Diagnóstico pela IA ➔", type="primary"):
        form_data = {
            "idade": idade, "saturacao": saturacao, "febre": febre,
            "tosse": tosse, "garganta": garganta, "dispneia": dispneia,
            "asma": asma, "diabetes": diabetes, "cardiopatia": cardiopatia
        }
        sintomas_principais  = tosse or dispneia or saturacao
        sintomas_secundarios = febre or garganta
        tem_problema = sintomas_principais or (sintomas_secundarios and (asma or cardiopatia))
        prob_gravidade = 0.0

        if tem_problema:
            try:
                resp = requests.post(f"{API_BASE}/predict", json=form_data)
                resp.raise_for_status()
                prob_gravidade = resp.json().get("probabilidadeGravidade", 0.0)
            except Exception as e:
                st.error(f"Erro ao conectar ao backend: {e}")

        st.session_state.resultado = {
            "temProblema": tem_problema,
            "probabilidadeGravidade": prob_gravidade,
            "formData": form_data
        }
        st.session_state.step = "result"
        st.rerun()


# ─── TELA: RESULTADO ─────────────────────────────────────────

elif st.session_state.step == "result":
    resultado = st.session_state.resultado

    if resultado["temProblema"]:
        prob = resultado["probabilidadeGravidade"]
        if prob >= 60:
            st.error("🚨 **Quadro Grave:** Risco elevado de internação ou UTI")
        elif prob >= 30:
            st.warning("⚠️ **Quadro Moderado:** Avaliação médica urgente recomendada")
        else:
            st.info("✅ **Quadro Leve:** Monitoramento em casa recomendado")

        st.metric("Chance de complicação grave", f"{prob:.1f}%")
        st.progress(min(prob / 100.0, 1.0))

        st.markdown("### Sintomas Informados:")
        fd = resultado["formData"]
        labels = [
            ("febre",       "🌡️ Febre"),
            ("tosse",       "😮‍💨 Tosse"),
            ("dispneia",    "💨 Falta de Ar"),
            ("garganta",    "🔴 Dor de Garganta"),
            ("saturacao",   "🩸 Sat. O₂ < 95%"),
            ("asma",        "🌬️ Asma"),
            ("diabetes",    "💉 Diabetes"),
            ("cardiopatia", "❤️ Cardiopatia"),
        ]
        for key, label in labels:
            if fd.get(key):
                st.write(f"- {label}")
    else:
        st.success("🛡️ **Sem Indícios Respiratórios**")
        st.write("Não foram detectados sinais de problema respiratório significativo.")

    st.write("---")
    st.caption("* Ferramenta de apoio — não substitui avaliação médica. Dados: SIVEP-Gripe · Scikit-Learn")

    if st.button("← Fazer Nova Avaliação"):
        st.session_state.step = "form"
        st.session_state.resultado = None
        st.rerun()
