import streamlit as st
import qrcode
from io import BytesIO
from supabase import create_client
import requests
from bs4 import BeautifulSoup

# Configuração do Supabase (Usar Secrets do Streamlit Cloud)
url = st.secrets["URL_SUPABASE"]
key = st.secrets["KEY_SUPABASE"]
supabase = create_client(url, key)

st.set_page_config(page_title="Painel do Prestador", layout="centered")

# --- ESTILO DARK MODE ---
st.markdown("""
    <style>
    .stApp { background-color: #0e0e0e; }
    h1, h2, h3, p, label, div { color: #ffffff !important; }
    .big-box { background-color: #1a1a1a; padding: 20px; border-radius: 10px; border: 1px solid #333; margin-bottom: 10px; }
    </style>
""", unsafe_allow_html=True)

# Inicializar sessão
if "prestador_id" not in st.session_state: st.session_state.prestador_id = None

# Login
if st.session_state.prestador_id is None:
    st.title("🎤 Portal do Prestador")
    nome = st.text_input("Usuário:")
    senha = st.text_input("Senha:", type="password")
    if st.button("Entrar"):
        res = supabase.table("prestadores").select("*").eq("nome_prestador", nome).eq("senha_acesso", senha).execute()
        if res.data:
            st.session_state.update({"prestador_id": res.data[0]["id"], "nome": res.data[0]["nome_prestador"], "slug": res.data[0]["slug_unico"]})
            st.rerun()
        else: st.error("Credenciais inválidas!")
else:
    st.title(f"Bem-vindo, {st.session_state.nome}!")
    
    # Link e QR Code
    url_cliente = f"https://ffkaraoke-cliente.streamlit.app/?prestador={st.session_state.slug}"
    st.info("Link do cliente:")
    st.code(url_cliente)
    
    qr = qrcode.make(url_cliente)
    buf = BytesIO()
    qr.save(buf, format="PNG")
    st.image(buf.getvalue(), width=150, caption="QR Code")

    if st.button("🔄 Atualizar Fila"):
        url_fila = f"https://grupoffkaraoke-default-rtdb.firebaseio.com/pedidos_{st.session_state.slug}.json"
        try:
            pedidos = requests.get(url_fila).json()
            if pedidos:
                for chave, p in pedidos.items(): st.success(f"🎤 {p.get('cantor')}: {p.get('musica')}")
            else: st.write("Fila vazia.")
        except: st.error("Erro ao carregar pedidos.")

    if st.button("Sair"):
        st.session_state.prestador_id = None
        st.rerun()
