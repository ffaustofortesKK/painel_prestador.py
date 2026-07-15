import streamlit as st
import qrcode
import re
import unicodedata
from io import BytesIO
import requests

st.set_page_config(page_title="Painel do Prestador", layout="wide")

# Inicialização
if "nome" not in st.session_state: st.session_state.nome = None
if "slug" not in st.session_state: st.session_state.slug = None

BASE_URL = "https://grupoffkaraoke-default-rtdb.firebaseio.com"
CLOUDINARY_CLOUD_NAME = "yhwgjh7g"

def normalizar_nome(nome):
    nome = nome.replace(".mp4", "")
    nome = unicodedata.normalize('NFKD', nome).encode('ASCII', 'ignore').decode('utf-8')
    nome = re.sub(r'[^\w\s]', '', nome)
    nome = "_".join(nome.split())
    return nome

# --- LOGIN ---
if st.session_state.nome is None:
    st.title("🎤 Portal do Prestador")
    nome_input = st.text_input("Nome:")
    sobrenome_input = st.text_input("Sobrenome:") 
    telef = st.text_input("Telefone:")
    
    if st.button("Entrar"):
        if nome_input and sobrenome_input and telef:
            slug_unico = f"{nome_input.lower()}-{sobrenome_input.lower()}"
            data_prestador = {"nome": f"{nome_input} {sobrenome_input}", "telefone": telef, "slug": slug_unico}
            telef_limpo = telef.replace(" ", "").replace("-", "")
            requests.put(f"{BASE_URL}/prestadores/{telef_limpo}.json", json=data_prestador)
            st.session_state.update({"nome": f"{nome_input} {sobrenome_input}", "slug": slug_unico})
            st.rerun()
else:
    st.title(f"Bem-vindo, {st.session_state.nome}!")
    
    url_cliente = f"https://appcliente.streamlit.app/?prestador={st.session_state.slug}"
    url_tv = f"https://ffktela.streamlit.app/?prestador={st.session_state.slug}"
    
    col_link, col_qr = st.columns([2, 1])
    with col_link:
        st.info("🔗 Link para seus Clientes:")
        st.code(url_cliente)
        st.info("📺 Link para a sua TV:")
        st.code(url_tv)
    with col_qr:
        qr = qrcode.make(url_cliente)
        buf = BytesIO()
        qr.save(buf, format="PNG")
        st.image(buf.getvalue(), width=120, caption="QR Code Cliente")

    st.divider()
    st.subheader("📋 Gestão de Fila")
    
    if st.button("🔄 Atualizar Fila"): st.rerun()
    
    url_fila = f"{BASE_URL}/pedidos_{st.session_state.slug}.json"
    url_status = f"{BASE_URL}/status_{st.session_state.slug}.json"
    
    try:
        pedidos_data = requests.get(url_fila).json()
        if pedidos_data:
            for p_id, p in pedidos_data.items():
                col1, col2, col3 = st.columns([4, 1, 1])
                nome_musica = p.get('musica')
                col1.write(f"🎤 {p.get('cantor')} - {nome_musica}")
                
                if col2.button("🗑️", key=f"del_{p_id}"):
                    requests.delete(f"{BASE_URL}/pedidos_{st.session_state.slug}/{p_id}.json")
                    st.rerun()
                
                if col3.button("🎤", key=f"start_{p_id}"):
                    # Normalizamos o nome
                    nome_tecnico = normalizar_nome(nome_musica)
                    
                    # ENVIAMOS O NOME NORMALIZADO EM VEZ DO LINK COMPLETO
                    # A TV (ffktela) deve ser programada para pegar este 'nome_tecnico'
                    # e montar o link lá. Isso evita problemas de sufixos aleatórios.
                    requests.put(url_status, json={
                        "acao": "contagem", 
                        "cantor": p.get('cantor'), 
                        "musica": nome_musica,
                        "nome_tecnico": nome_tecnico
                    })
                    st.success(f"Enviado para TV: {nome_musica}")
                    st.rerun()
        else: 
            st.write("Fila vazia.")
    except Exception as e:
        st.error(f"Erro ao processar fila: {e}")
