import streamlit as st
import qrcode
from io import BytesIO
from supabase import create_client

# Configuração
supabase = create_client(st.secrets["URL_SUPABASE"], st.secrets["KEY_SUPABASE"])

st.title("Painel do Prestador")

# Login do Prestador
nome_prestador = st.text_input("Nome de Usuário:")
senha = st.text_input("Senha:", type="password")

if st.button("Entrar"):
    # Verifica no banco se o prestador existe
    prestador = supabase.table("prestadores").select("*").eq("nome_prestador", nome_prestador).eq("senha_acesso", senha).execute().data
    
    if prestador:
        st.session_state["prestador_id"] = prestador[0]["id"]
        st.session_state["slug"] = prestador[0]["slug_unico"]
        st.rerun()
    else:
        st.error("Credenciais inválidas!")

# Se logado, mostra o painel dele
if "prestador_id" in st.session_state:
    st.write(f"Bem-vindo, {nome_prestador}!")
    
    # Gerar link exclusivo
    link_cliente = f"https://sua-app-de-pedidos.streamlit.app/?prestador={st.session_state['slug']}"
    
    st.info(f"Compartilhe este link com seus clientes: {link_cliente}")
    
    # Gerar QR Code
    qr = qrcode.make(link_cliente)
    buf = BytesIO()
    qr.save(buf, format="PNG")
    st.image(buf.getvalue(), caption="QR Code exclusivo para seus clientes")
