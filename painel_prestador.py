import streamlit as st
import qrcode
from io import BytesIO
from supabase import create_client

# Configuração
url = st.secrets["URL_SUPABASE"]
key = st.secrets["KEY_SUPABASE"]
supabase = create_client(url, key)

st.set_page_config(page_title="Painel do Prestador", layout="centered")
st.title("🎤 Portal do Prestador")

# Inicializar sessão de login
if "prestador_id" not in st.session_state:
    
        else:
            st.error("Credenciais inválidas!")
else:
    st.success(f"Olá, {st.session_state['nome']}!")
    
    # Gerar link do prestador
    # O cliente usará este link para pedir músicas
    url_cliente = f"https://ffkaraoke-cliente.streamlit.app/?prestador={st.session_state['slug']}"
    
    st.info(f"Seu link de pedidos: {url_cliente}")
    
    # Gerar QR Code
    qr = qrcode.make(url_cliente)
    buf = BytesIO()
    qr.save(buf, format="PNG")
    st.image(buf.getvalue(), caption="Imprima este QR Code para seus clientes")
    
    if st.button("Sair"):
        st.session_state["prestador_id"] = None
        st.rerun()
