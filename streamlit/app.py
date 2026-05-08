import streamlit as st
import requests

API_BASE = "http://localhost:8000"

st.set_page_config(
    page_title="Triagem Respiratória IA",
    page_icon="🩺",
    layout="centered"
)

# Custom CSS to mimic some of the original design (optional mas melhora a aparência)
st.markdown("""
    <style>
    .stButton>button {
        width: 100%;
        border-radius: 12px;
        padding: 0.75rem 1rem;
        font-weight: bold;
    }
    .main-title {
        text-align: center;
        background: -webkit-linear-gradient(45deg, #3b82f6, #06b6d4);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: 800;
        font-size: 3rem;
        margin-bottom: 0;
    }
    .sub-title {
        text-align: center;
        color: #64748b;
        font-size: 1.2rem;
        margin-bottom: 2rem;
    }
    </style>
""", unsafe_allow_html=True)

if 'step' not in st.session_state:
    st.session_state.step = 'train'
if 'trainedModel' not in st.session_state:
    st.session_state.trainedModel = None
if 'resultado' not in st.session_state:
    st.session_state.resultado = None

# Header
col1, col2 = st.columns([1, 10])
with col1:
    st.markdown("## 🩺")
with col2:
    st.markdown("**Triagem Respiratória**  \n*Powered by Python AI*")

if st.session_state.trainedModel:
    st.success(f"IA Ativa · {st.session_state.trainedModel['samples']:,} pacientes")

st.divider()

def handle_train():
    try:
        with st.spinner("Processando dataset SIVEP-Gripe e treinando IA..."):
            response = requests.post(f"{API_BASE}/train")
            response.raise_for_status()
            data = response.json()
            st.session_state.trainedModel = {"accuracy": data.get("accuracy"), "samples": data.get("samples")}
            st.session_state.step = 'form'
    except requests.exceptions.HTTPError as e:
        try:
            error_detail = e.response.json().get('detail', str(e))
        except:
            error_detail = str(e)
        st.error(f"Erro do Backend: {error_detail}")
    except Exception as e:
        st.error(f"Erro ao conectar ao backend Python: {e}")

if st.session_state.step == 'train':
    st.markdown('<p class="main-title">Inteligência Artificial</p>', unsafe_allow_html=True)
    st.markdown('<p class="sub-title">para Triagem Clínica</p>', unsafe_allow_html=True)
    
    st.markdown("<p style='text-align: center; color: gray;'>Acesse o sistema de diagnóstico respiratório treinado com dados reais do SIVEP-Gripe (DataSUS).</p>", unsafe_allow_html=True)
    
    st.write("")
    if st.button("🚀 Iniciar Treinamento da IA", type="primary"):
        handle_train()
        st.rerun()

    st.write("---")
    c1, c2, c3 = st.columns(3)
    c1.metric("Algoritmo", "Regressão Logística")
    c2.metric("Dataset", "SIVEP-Gripe")
    c3.metric("Backend", "Python + FastAPI")

elif st.session_state.step == 'form':
    st.header("Formulário de Sintomas")
    st.markdown("Preencha as informações do paciente para avaliação pela IA.")
    
    with st.form("patient_form"):
        st.subheader("Informações Básicas")
        idade = st.slider("Idade do Paciente (anos)", 0, 100, 45)
        
        st.subheader("Sintomas Principais")
        col_s1, col_s2 = st.columns(2)
        with col_s1:
            febre = st.checkbox("🌡️ Febre (Temperatura elevada)")
            tosse = st.checkbox("😮‍💨 Tosse persistente")
            dispneia = st.checkbox("💨 Falta de Ar (Dispneia)")
        with col_s2:
            garganta = st.checkbox("🔴 Dor de Garganta")
            saturacao = st.checkbox("🩸 Saturação O₂ < 95%")
            
        st.subheader("Comorbidades")
        col_c1, col_c2, col_c3 = st.columns(3)
        with col_c1:
            asma = st.checkbox("🌬️ Asma")
        with col_c2:
            diabetes = st.checkbox("💉 Diabetes")
        with col_c3:
            cardiopatia = st.checkbox("❤️ Cardiopatia")
            
        submit = st.form_submit_button("Gerar Diagnóstico pela IA ➔", type="primary")
        
        if submit:
            form_data = {
                "idade": idade,
                "saturacao": saturacao,
                "febre": febre,
                "tosse": tosse,
                "garganta": garganta,
                "dispneia": dispneia,
                "asma": asma,
                "diabetes": diabetes,
                "cardiopatia": cardiopatia
            }
            
            sintomas_principais = tosse or dispneia or saturacao
            sintomas_secundarios = febre or garganta
            tem_problema = sintomas_principais or (sintomas_secundarios and (asma or cardiopatia))
            desc_problema = 'Indícios de Quadro Respiratório Detectados' if tem_problema else 'Saudável / Sem indícios respiratórios'
            prob_gravidade = 0.0
            
            if tem_problema:
                try:
                    resp = requests.post(f"{API_BASE}/predict", json=form_data)
                    resp.raise_for_status()
                    data = resp.json()
                    prob_gravidade = data.get("probabilidadeGravidade", 0.0)
                except Exception as e:
                    st.error(f"Erro ao conectar ao backend: {e}")
            
            st.session_state.resultado = {
                "temProblema": tem_problema,
                "descProblema": desc_problema,
                "probabilidadeGravidade": prob_gravidade,
                "formData": form_data
            }
            st.session_state.step = 'result'
            st.rerun()

elif st.session_state.step == 'result':
    resultado = st.session_state.resultado
    
    if resultado['temProblema']:
        prob = resultado['probabilidadeGravidade']
        
        if prob >= 60:
            st.error("🚨 **Quadro Grave:** Risco elevado de internação ou UTI")
        elif prob >= 30:
            st.warning("⚠️ **Quadro Moderado:** Recomenda-se avaliação médica urgente")
        else:
            st.info("✅ **Quadro Leve:** Monitoramento recomendado em casa")
            
        st.metric("Chance de complicação grave", f"{prob:.1f}%")
        st.progress(min(prob / 100.0, 1.0))
        
        st.markdown("### Sintomas Informados:")
        fd = resultado['formData']
        sintomas = []
        if fd['febre']: sintomas.append("🌡️ Febre")
        if fd['tosse']: sintomas.append("😮‍💨 Tosse")
        if fd['dispneia']: sintomas.append("💨 Falta de Ar")
        if fd['garganta']: sintomas.append("🔴 Dor de Garganta")
        if fd['saturacao']: sintomas.append("🩸 Sat. O₂ < 95%")
        if fd['asma']: sintomas.append("🌬️ Asma")
        if fd['diabetes']: sintomas.append("💉 Diabetes")
        if fd['cardiopatia']: sintomas.append("❤️ Cardiopatia")
        
        if sintomas:
            for s in sintomas:
                st.write(f"- {s}")
        else:
            st.write("Nenhum sintoma selecionado")
            
    else:
        st.success("🛡️ **Sem Indícios Respiratórios**")
        st.write("Com base nos sintomas informados, não foram detectados sinais de problema respiratório significativo.")
        
    st.write("---")
    st.caption("* Este sistema é uma ferramenta de apoio e não substitui avaliação médica profissional. Baseado em dados do SIVEP-Gripe · Scikit-Learn · Regressão Logística")
    
    if st.button("← Fazer Nova Avaliação"):
        st.session_state.step = 'form'
        st.session_state.resultado = None
        st.rerun()
