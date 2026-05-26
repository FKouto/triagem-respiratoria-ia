import os
import requests
import streamlit as st
from datetime import date, timedelta
# pyrefly: ignore [missing-import]
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

API_BASE      = _secret("API_BASE",      "http://localhost:8000")
TRAIN_SECRET  = _secret("TRAIN_SECRET",  "")
SUPABASE_URL  = _secret("SUPABASE_URL",  "")
SUPABASE_KEY  = _secret("SUPABASE_KEY",  "")

AUTH_HEADERS  = {
    "apikey":        SUPABASE_KEY,
    "Content-Type":  "application/json",
}


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
if "user" not in st.session_state or st.session_state.user is None:
    cookie_val = st.context.cookies.get("medtriagem_user")
    if cookie_val:
        try:
            import urllib.parse
            import json
            decoded = urllib.parse.unquote(cookie_val)
            st.session_state["user"] = json.loads(decoded)
        except Exception:
            pass

defaults = {
    "user":         None,   # dict com email e token quando logado
    "step":         "train",
    "trainedModel": None,
    "resultado":    None,
}
for key, default in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = default


# ══════════════════════════════════════════════════════════════
# AUTENTICAÇÃO — Supabase Auth REST API
# ══════════════════════════════════════════════════════════════

def _set_user_cookie(user_data: dict):
    """Grava o cookie no navegador e recarrega a página pai."""
    import urllib.parse
    import json
    # pyrefly: ignore [missing-import]
    import streamlit.components.v1 as components
    val = urllib.parse.quote(json.dumps(user_data))
    js_code = f"""
    <script>
        var date = new Date();
        date.setTime(date.getTime() + (7 * 24 * 60 * 60 * 1000));
        var expires = "; expires=" + date.toUTCString();
        window.parent.document.cookie = "medtriagem_user=" + "{val}" + expires + "; path=/; SameSite=Lax";
        window.parent.location.reload();
    </script>
    """
    components.html(js_code, height=0, width=0)


def _delete_user_cookie():
    """Remove o cookie do navegador e recarrega a página pai."""
    # pyrefly: ignore [missing-import]
    import streamlit.components.v1 as components
    js_code = """
    <script>
        window.parent.document.cookie = "medtriagem_user=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/; SameSite=Lax";
        window.parent.location.reload();
    </script>
    """
    components.html(js_code, height=0, width=0)


def _supabase_login(email: str, password: str) -> dict:
    """Autentica via POST /auth/v1/token?grant_type=password."""
    resp = requests.post(
        f"{SUPABASE_URL}/auth/v1/token?grant_type=password",
        headers=AUTH_HEADERS,
        json={"email": email, "password": password},
        timeout=10,
    )
    return resp.json(), resp.status_code


def _supabase_signup(email: str, password: str) -> dict:
    """Cadastra via POST /auth/v1/signup."""
    resp = requests.post(
        f"{SUPABASE_URL}/auth/v1/signup",
        headers=AUTH_HEADERS,
        json={"email": email, "password": password},
        timeout=10,
    )
    return resp.json(), resp.status_code


def _error_msg(data: dict) -> str:
    """Extrai a mensagem de erro da resposta do Supabase e traduz."""
    raw = data.get("error_description") or data.get("msg") or data.get("message", "")
    translations = {
        "Invalid login credentials":         "Email ou senha incorretos.",
        "User already registered":           "Este email já está cadastrado.",
        "Password should be at least 6 characters":
            "A senha deve ter no mínimo 6 caracteres.",
        "Unable to validate email address: invalid format":
            "Formato de email inválido.",
    }
    return translations.get(raw, raw or "Erro desconhecido.")


def do_logout():
    """Limpa toda a sessão e volta para o login."""
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    _delete_user_cookie()


# ══════════════════════════════════════════════════════════════
# TELA: LOGIN / CADASTRO
# ══════════════════════════════════════════════════════════════

if st.session_state.user is None:

    st.markdown("""
    <div class="login-wrapper">
        <div class="login-icon">🩺</div>
        <div class="login-title">MedTriagem IA</div>
        <div class="login-subtitle">Triagem Respiratória · SIVEP-Gripe · DataSUS</div>
    </div>
    """, unsafe_allow_html=True)

    tab_login, tab_signup = st.tabs(["🔑 Entrar", "📝 Criar Conta"])

    # ── Tab: Login ────────────────────────────────────────────
    with tab_login:
        with st.form("login_form"):
            email_login = st.text_input("Email", placeholder="seu@email.com", key="login_email")
            senha_login = st.text_input("Senha", type="password", placeholder="••••••••", key="login_senha")
            submit_login = st.form_submit_button("Entrar", type="primary", use_container_width=True)

        if submit_login:
            if not email_login or not senha_login:
                st.error("Preencha email e senha.")
            else:
                with st.spinner("Autenticando..."):
                    data, status = _supabase_login(email_login, senha_login)
                if status == 200 and "access_token" in data:
                    user_email = data.get("user", {}).get("email", email_login)
                    st.session_state.user = {
                        "email": user_email,
                        "token": data["access_token"],
                    }
                    _set_user_cookie(st.session_state.user)
                else:
                    st.error(_error_msg(data))

    # ── Tab: Cadastro ─────────────────────────────────────────
    with tab_signup:
        with st.form("signup_form"):
            email_signup  = st.text_input("Email", placeholder="seu@email.com", key="signup_email")
            senha_signup  = st.text_input("Senha", type="password", placeholder="Mínimo 6 caracteres", key="signup_senha")
            senha_confirm = st.text_input("Confirmar Senha", type="password", placeholder="Repita a senha", key="signup_confirm")
            submit_signup = st.form_submit_button("Criar Conta", type="primary", use_container_width=True)

        if submit_signup:
            if not email_signup or not senha_signup:
                st.error("Preencha todos os campos.")
            elif senha_signup != senha_confirm:
                st.error("As senhas não coincidem.")
            elif len(senha_signup) < 6:
                st.error("A senha deve ter no mínimo 6 caracteres.")
            else:
                with st.spinner("Criando conta..."):
                    data, status = _supabase_signup(email_signup, senha_signup)
                if status in (200, 201) and data.get("id"):
                    st.success("✅ Conta criada com sucesso! Faça login na aba **Entrar**.")
                elif status in (200, 201) and data.get("access_token"):
                    user_email = data.get("user", {}).get("email", email_signup)
                    st.session_state.user = {
                        "email": user_email,
                        "token": data["access_token"],
                    }
                    _set_user_cookie(st.session_state.user)
                else:
                    st.error(_error_msg(data))

    st.markdown("""
    <div class="med-caption">
        ⚕️ Ferramenta de apoio clínico — não substitui avaliação médica presencial.<br>
        Dados: SIVEP-Gripe (DataSUS) · Modelo: Regressão Logística (Scikit-Learn) · Backend: FastAPI
    </div>
    """, unsafe_allow_html=True)

    st.stop()


# ══════════════════════════════════════════════════════════════
# ÁREA AUTENTICADA (todo o fluxo original abaixo)
# ══════════════════════════════════════════════════════════════

# ── Top bar (todas as telas) ──────────────────────────────────
user_email = st.session_state.user["email"]

with st.container(key="topbar"):
    col_logo, col_email, col_sair = st.columns([5, 3, 1])
    with col_logo:
        st.markdown(
            '<div class="topbar-logo">'
            '<span class="topbar-icon">🩺</span>'
            '<div>'
            '<p class="topbar-title">MedTriagem IA</p>'
            '<p class="topbar-sub">Triagem Respiratória · SIVEP-Gripe · DataSUS</p>'
            '</div>'
            '</div>',
            unsafe_allow_html=True,
        )
    with col_email:
        st.markdown(
            f'<div class="topbar-user">👤 {user_email}</div>',
            unsafe_allow_html=True,
        )
    with col_sair:
        if st.button("Sair", key="btn_logout"):
            do_logout()

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


# ── Histórico — Supabase ──────────────────────────────────────
def salvar_historico(form_data: dict, prob: float, classificacao: str):
    """Insere uma avaliação na tabela `historico` do Supabase."""
    usuario = st.session_state.user.get("email", "Usuário")
    token   = st.session_state.user.get("token", "")
    
    payload_full = {
        "usuario":       usuario,
        "idade":         form_data["idade"],
        "nome":          form_data.get("nome", ""),
        "sexo":          form_data.get("sexo", ""),
        "cpf":           form_data.get("cpf", ""),
        "febre":         form_data["febre"],
        "tosse":         form_data["tosse"],
        "dispneia":      form_data["dispneia"],
        "garganta":      form_data["garganta"],
        "saturacao":     form_data["saturacao"],
        "asma":          form_data["asma"],
        "diabetes":      form_data["diabetes"],
        "cardiopatia":   form_data["cardiopatia"],
        "probabilidade": round(prob, 2),
        "classificacao": classificacao,
    }
    
    payload_compat = {
        "usuario":       usuario,
        "idade":         form_data["idade"],
        "febre":         form_data["febre"],
        "tosse":         form_data["tosse"],
        "dispneia":      form_data["dispneia"],
        "garganta":      form_data["garganta"],
        "saturacao":     form_data["saturacao"],
        "asma":          form_data["asma"],
        "diabetes":      form_data["diabetes"],
        "cardiopatia":   form_data["cardiopatia"],
        "probabilidade": round(prob, 2),
        "classificacao": classificacao,
    }
    
    headers = {
        "apikey":        SUPABASE_KEY,
        "Authorization": f"Bearer {token}",
        "Content-Type":  "application/json",
        "Prefer":        "return=minimal",
    }
    
    try:
        resp = requests.post(
            f"{SUPABASE_URL}/rest/v1/historico",
            headers=headers,
            json=payload_full,
            timeout=10,
        )
        if resp.status_code == 400:
            requests.post(
                f"{SUPABASE_URL}/rest/v1/historico",
                headers=headers,
                json=payload_compat,
                timeout=10,
            )
    except Exception:
        pass  # Falha silenciosa — não interrompe o fluxo principal


def carregar_historico() -> list:
    """Busca as avaliações do usuário logado, ordenadas da mais recente."""
    usuario = st.session_state.user.get("email", "")
    token   = st.session_state.user.get("token", "")
    try:
        resp = requests.get(
            f"{SUPABASE_URL}/rest/v1/historico"
            f"?usuario=eq.{usuario}&order=criado_em.desc&limit=50",
            headers={
                "apikey":        SUPABASE_KEY,
                "Authorization": f"Bearer {token}",
            },
            timeout=10,
        )
        if resp.ok:
            return resp.json()
    except Exception:
        pass
    return []


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
    
    nome = st.text_input("Nome Completo do Paciente", placeholder="Ex: Maria da Silva", key="paciente_nome")
    
    c1, c2, c3, c4 = st.columns([2, 1.0, 1.4, 0.8])
    with c1:
        cpf = st.text_input("CPF", placeholder="000.000.000-00", max_chars=14, key="paciente_cpf")
        # Injeção de JS para aplicar a máscara no campo de CPF em tempo real (on key press)
        st.components.v1.html(r"""
        <script>
        const doc = window.parent.document;
        // Procura todos os inputs do Streamlit
        const inputs = Array.from(doc.querySelectorAll('input'));
        // Localiza o input do CPF pelo placeholder único
        const cpfInput = inputs.find(i => i.placeholder === '000.000.000-00');
        
        if (cpfInput && !cpfInput.dataset.maskAttached) {
            cpfInput.dataset.maskAttached = 'true';
            cpfInput.addEventListener('input', function(e) {
                let v = e.target.value.replace(/\D/g, ''); // Remove tudo que não for dígito
                if (v.length > 14) v = v.slice(0, 14); // Max 14 dígitos
                
                // Aplica a máscara XXX.XXX.XXX-XX
                v = v.replace(/(\d{3})(\d)/, '$1.$2');
                v = v.replace(/(\d{3})(\d)/, '$1.$2');
                v = v.replace(/(\d{3})(\d{1,2})$/, '$1-$2');
                
                if (e.target.value !== v) {
                    // Atualiza o valor contornando o state do React para o Streamlit reconhecer
                    let nativeInputValueSetter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, "value").set;
                    nativeInputValueSetter.call(e.target, v);
                    e.target.dispatchEvent(new Event('input', { bubbles: true }));
                }
            });
        }
        </script>
        """, height=0, width=0)
    with c2:
        sexo = st.selectbox("Sexo", options=["Feminino", "Masculino"], index=None, placeholder="Selecione", key="paciente_sexo")
    with c3:
        data_minima = date.today() - timedelta(days=130*365)
        data_nasc = st.date_input("Nascimento", value=None, min_value=data_minima, max_value=date.today(), format="DD/MM/YYYY", key="paciente_nascimento")
        
        if data_nasc:
            hoje = date.today()
            idade = hoje.year - data_nasc.year - ((hoje.month, hoje.day) < (data_nasc.month, data_nasc.day))
        else:
            idade = "—"
    with c4:
        st.markdown(
            f'<div class="idade-badge" style="margin-top: 24px;">'
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

    # Validação
    algum_selecionado = any([febre, tosse, dispneia, garganta, saturacao, asma, diabetes, cardiopatia])
    cpf_numeros = "".join(filter(str.isdigit, cpf)) if cpf else ""
    cpf_valido = len(cpf_numeros) == 11
    dados_preenchidos = bool(nome and nome.strip() and cpf_valido and sexo and data_nasc)
    pode_enviar = algum_selecionado and dados_preenchidos

    if not dados_preenchidos:
        st.markdown("""
        <div style="
            background: rgba(220,38,38,0.08);
            border: 1px solid rgba(220,38,38,0.25);
            border-radius: 14px;
            padding: 14px 18px;
            font-size: 0.88rem;
            color: #991b1b;
            font-family: 'JetBrains Mono', monospace;
            margin-bottom: 10px;
        ">
            ⚠️ Preencha todos os Dados Básicos (Nome, CPF válido, Sexo e Nascimento).
        </div>
        """, unsafe_allow_html=True)

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
    else:
        st.markdown('<div style="margin-bottom: 30px;"></div>', unsafe_allow_html=True)

    st.write("")
    col_btn1, col_btn2 = st.columns(2)
    with col_btn1:
        analisar_clicado = st.button("Analisar com IA →", type="primary", disabled=not pode_enviar, use_container_width=True)
    with col_btn2:
        if st.button("📋 Ver Histórico", use_container_width=True):
            st.session_state.step = "historico"
            st.rerun()

    if analisar_clicado:
        payload_ia = {
            "idade": idade, "febre": febre, "tosse": tosse,
            "garganta": garganta, "dispneia": dispneia, "saturacao": saturacao,
            "asma": asma, "diabetes": diabetes, "cardiopatia": cardiopatia,
        }
        form_data = {
            "nome": nome, "sexo": sexo, "cpf": cpf,
            **payload_ia
        }
        prob_gravidade = 0.0
        classificacao  = "leve"
        limiares       = {"grave": 60.0, "moderado": 30.0}
        erro_backend   = None

        try:
            resp = requests.post(f"{API_BASE}/predict", json=payload_ia, timeout=15)
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
        # Salva no histórico do Supabase (falha silenciosa)
        if not erro_backend:
            salvar_historico(form_data, prob_gravidade, classificacao)
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
    
    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f"**Nome:** {fd.get('nome', '—') or '—'}")
        st.markdown(f"**CPF:** {fd.get('cpf', '—') or '—'}")
    with col2:
        st.markdown(f"**Sexo:** {fd.get('sexo', '—') or '—'}")
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
    c1, c2 = st.columns(2)
    with c1:
        if st.button("← Nova Avaliação", use_container_width=True):
            st.session_state.step      = "form"
            st.session_state.resultado = None
            st.rerun()
    with c2:
        if st.button("📋 Ver Histórico", type="primary", use_container_width=True):
            st.session_state.step = "historico"
            st.rerun()

    render_footer()


# ══════════════════════════════════════════════════════════════
# TELA: HISTÓRICO
# ══════════════════════════════════════════════════════════════
elif st.session_state.step == "historico":

    st.markdown("""
    <div class="form-title">Histórico de Avaliações</div>
    <div class="form-subtitle">Suas últimas 50 avaliações realizadas</div>
    """, unsafe_allow_html=True)

    with st.spinner("Carregando histórico..."):
        registros = carregar_historico()

    if not registros:
        st.markdown("""
        <div style="
            text-align: center;
            padding: 48px 24px;
            background: rgba(255,255,255,0.6);
            border: 1px solid rgba(148,163,184,0.12);
            border-radius: 20px;
            margin-top: 24px;
        ">
            <div style="font-size: 2.5rem; margin-bottom: 12px;">📋</div>
            <div style="font-size: 1rem; font-weight: 600; color: #0f172a;">Nenhuma avaliação encontrada</div>
            <div style="font-size: 0.88rem; color: #64748b; margin-top: 6px;">
                As avaliações realizadas aparecerão aqui.
            </div>
        </div>
        """, unsafe_allow_html=True)
    else:
        # Badges de classificação
        badge_cfg = {
            "grave":    ("🚨", "#dc2626", "rgba(239,68,68,0.08)",   "rgba(239,68,68,0.2)"),
            "moderado": ("⚠️", "#d97706", "rgba(245,158,11,0.08)",  "rgba(245,158,11,0.2)"),
            "leve":     ("✅", "#059669", "rgba(16,185,129,0.08)",  "rgba(16,185,129,0.2)"),
        }

        sintoma_keys = ["febre", "tosse", "dispneia", "garganta", "saturacao", "asma", "diabetes", "cardiopatia"]

        for reg in registros:
            classi = reg.get("classificacao", "leve")
            icon, cor, bg, border = badge_cfg.get(classi, badge_cfg["leve"])
            prob  = reg.get("probabilidade", 0)
            idade = reg.get("idade", "—")

            # Novos campos do paciente no histórico
            reg_nome = reg.get("nome")
            reg_sexo = reg.get("sexo")
            reg_cpf = reg.get("cpf")
            
            perfil_detalhado = f"🎂 {idade} anos"
            if reg_sexo:
                perfil_detalhado += f" &nbsp;·&nbsp; 🚻 {reg_sexo}"
            if reg_cpf:
                perfil_detalhado += f" &nbsp;·&nbsp; 💳 CPF: {reg_cpf}"

            # Formata data
            criado_em = reg.get("criado_em", "")
            try:
                from datetime import datetime, timezone
                dt = datetime.fromisoformat(criado_em.replace("Z", "+00:00"))
                dt_local = dt.astimezone()
                data_fmt = dt_local.strftime("%d/%m/%Y %H:%M")
            except Exception:
                data_fmt = criado_em[:16] if criado_em else "—"

            # Tags de sintomas
            sintomas = [_label_sintoma(k) for k in sintoma_keys if reg.get(k)]
            tags_html = "".join(
                f'<span style="background:rgba(255,255,255,0.8);border:1px solid rgba(148,163,184,0.2);'
                f'border-radius:999px;padding:3px 10px;font-size:0.78rem;color:#334155;">{s}</span>'
                for s in sintomas
            ) if sintomas else '<span style="color:#94a3b8;font-size:0.82rem;">Nenhum sintoma registrado</span>'

            # HTML do nome do paciente
            nome_html = f'<div style="font-size:0.92rem;font-weight:700;color:#0f172a;margin-bottom:4px;">🧑 {reg_nome}</div>' if reg_nome else ""

            card_html = f"""
<div style="background: rgba(255,255,255,0.88); border: 1px solid rgba(148,163,184,0.12); border-radius: 18px; padding: 22px 24px; margin-bottom: 14px; box-shadow: 0 4px 16px rgba(15,23,42,0.04); position: relative; overflow: hidden;">
<div style="position:absolute;top:0;left:0;width:100%;height:3px;background:linear-gradient(90deg,{cor},{cor}88);"></div>
<div style="display:flex;justify-content:space-between;align-items:flex-start;flex-wrap:wrap;gap:12px;">
<div>
<div style="display:inline-flex;align-items:center;gap:6px; background:{bg};border:1px solid {border}; border-radius:999px;padding:4px 12px; font-size:0.75rem;font-weight:700;color:{cor}; font-family:'JetBrains Mono',monospace; text-transform:uppercase;letter-spacing:0.1em; margin-bottom:10px;">
{icon} {classi.upper()}
</div>
{nome_html}
<div style="font-size:0.82rem;color:#64748b;font-family:'JetBrains Mono',monospace;margin-bottom:4px;">
Data e Hora: 🕐 {data_fmt}
</div>
<div style="font-size:0.85rem;color:#475569;margin-bottom:4px;">
{perfil_detalhado}
</div>
<div style="display:flex;flex-wrap:wrap;gap:6px;margin-top:10px;">
{tags_html}
</div>
</div>
<div style="text-align:right;min-width:80px;">
<div style="font-size:2rem;font-weight:800;color:#0f172a;font-family:'JetBrains Mono',monospace;letter-spacing:-0.04em;">{prob:.1f}%</div>
<div style="font-size:0.72rem;color:#94a3b8;">prob. complicação</div>
</div>
</div>
</div>
"""
            st.markdown(card_html, unsafe_allow_html=True)

    st.write("")
    if st.button("← Voltar", use_container_width=True):
        st.session_state.step = "form"
        st.rerun()

    render_footer()