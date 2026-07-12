import streamlit as st
import qrcode
from io import BytesIO
from supabase import create_client

# Configuração
url = st.secrets["URL_SUPABASE"]
key = st.secrets["KEY_SUPABASE"]
supabase = create_client(url, key)

st.set_page_config(page_title="Painel do Prestador", layout="centered")

# --- ESTILO DARK MODE ---
st.markdown("""
    <style>
    .stApp { background-color: #0e0e0e; }
    h1, h2, h3, p, label, div { color: #ffffff !important; }
    .big-box { background-color: #1a1a1a; padding: 20px; border-radius: 10px; border: 1px solid #333; }
    .sintonia-box { background-color: #260000; padding: 15px; border-radius: 5px; border: 1px solid #ff4b4b; }
    </style>
""", unsafe_allow_html=True)

if "prestador_id" not in st.session_state:
    st.session_state["prestador_id"] = None

# --- LOGIN ---
if st.session_state["prestador_id"] is None:
    st.title("🎤 Portal do Prestador")
    nome = st.text_input("Nome de Usuário:")
    senha = st.text_input("Senha:", type="password")
    
    if st.button("Entrar"):
        res = supabase.table("prestadores").select("*").eq("nome_prestador", nome).eq("senha_acesso", senha).execute()
        if res.data:
            st.session_state["prestador_id"] = res.data[0]["id"]
            st.session_state["nome"] = res.data[0]["nome_prestador"]
            st.session_state["slug"] = res.data[0]["slug_unico"]
            st.rerun()
        else:
            st.error("Credenciais inválidas!")

# --- PAINEL ---
else:
    st.title(f"🎤 Bem-vindo, {st.session_state['nome']}!")
    
    # Link personalizado
    slug = st.session_state["slug"]
    url_cliente = f"https://ffkaraoke-cliente.streamlit.app/?prestador={slug}"
    st.info(f"Link do cliente: {url_cliente}")
    
    # Gerar QR Code
    qr = qrcode.make(url_cliente)
    buf = BytesIO()
    qr.save(buf, format="PNG")
    st.image(buf.getvalue(), width=200)

    # Interface de Pedidos
    st.markdown('<div class="big-box">', unsafe_allow_html=True)
    st.subheader("➕ Adicionar Música")
    nome_cantor = st.text_input("Nome do Cantor:")
    musica = st.text_input("Nome da Música:")
    if st.button("Adicionar à Lista"):
        st.success("Adicionado!")
    st.markdown('</div>', unsafe_allow_html=True)

    # Fila de Reprodução
    st.markdown("### Fila de Reprodução")
    col1, col2, col3 = st.columns(3)
    col1.button("Subir")
    col2.button("Descer")
    col3.button("Remover")

    # Sistema Cloud
    st.markdown('<div class="sintonia-box">', unsafe_allow_html=True)
    st.markdown("### ☁️ SISTEMA EM SINTONIA CLOUD")
    c1, c2 = st.columns(2)
    c1.button("✅ Validar")
    c2.button("❌ Recusar")
    st.markdown('</div>', unsafe_allow_html=True)

    if st.button("Sair"):
        st.session_state["prestador_id"] = None
        st.rerun()
