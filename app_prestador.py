import streamlit as st
import qrcode
import re
import unicodedata
import cloudinary
import cloudinary.api
from io import BytesIO
import requests
import time

# Configuração Cloudinary
cloudinary.config( 
  cloud_name = "yhwgjh7g", 
  api_key = "347924379441394", 
  api_secret = "_gzZOnOmzIk6dlmferYm6ck8S08"
)

st.set_page_config(page_title="Painel do Prestador", layout="wide")

if "nome" not in st.session_state: st.session_state.nome = None
if "slug" not in st.session_state: st.session_state.slug = None

BASE_URL = "https://grupoffkaraoke-default-rtdb.firebaseio.com"

def normalizar_nome(nome):
    nome = nome.replace(".mp4", "")
    nome = unicodedata.normalize('NFKD', nome).encode('ASCII', 'ignore').decode('utf-8')
    nome = re.sub(r'[^\w\s]', '', nome)
    nome = "_".join(nome.split())
    return nome

def encontrar_link_real(nome_base):
    try:
        resources = cloudinary.api.resources(type="upload", resource_type="video", prefix=nome_base, max_results=1)
        if resources['resources']:
            url = resources['resources'][0]['secure_url']
            return url.replace("/upload/", "/upload/fl_attachment/") + ".mp4"
    except: return None

# --- LOGIN ---
if st.session_state.nome is None:
    st.title("🎤 Portal do Prestador")
    nome_input = st.text_input("Nome:")
    sobrenome_input = st.text_input("Sobrenome:") 
    telef = st.text_input("Telefone:")
    if st.button("Entrar"):
        if nome_input and sobrenome_input and telef:
            slug_unico = f"{nome_input.lower()}-{sobrenome_input.lower()}"
            telef_limpo = telef.replace(" ", "").replace("-", "")
            requests.put(f"{BASE_URL}/prestadores/{telef_limpo}.json", json={"nome": f"{nome_input} {sobrenome_input}", "slug": slug_unico})
            st.session_state.update({"nome": f"{nome_input} {sobrenome_input}", "slug": slug_unico})
            st.rerun()
else:
    st.title(f"Bem-vindo, {st.session_state.nome}!")
    url_cliente = f"https://appcliente.streamlit.app/?prestador={st.session_state.slug}"
    url_tv = f"https://ffktela.streamlit.app/?prestador={st.session_state.slug}"
    
    col_l1, col_l2 = st.columns([2, 1])
    with col_l1:
        st.info(f"🔗 Cliente: {url_cliente}")
        st.info(f"📺 TV: {url_tv}")
    with col_l2:
        qr = qrcode.make(url_cliente)
        buf = BytesIO()
        qr.save(buf, format="PNG")
        st.image(buf.getvalue(), width=100, caption="QR Code Cliente")
    
    url_status = f"{BASE_URL}/status_{st.session_state.slug}.json"
    
    st.divider()
    st.subheader("📋 Gestão de Fila (Atualização Automática)")
    
    pedidos_data = requests.get(f"{BASE_URL}/pedidos_{st.session_state.slug}.json").json()
    
    if pedidos_data:
        for p_id, p in pedidos_data.items():
            col1, col2, col3 = st.columns([4, 1, 1])
            col1.write(f"🎤 {p.get('cantor')} - {p.get('musica')}")
            if col2.button("🗑️", key=f"del_{p_id}"):
                requests.delete(f"{BASE_URL}/pedidos_{st.session_state.slug}/{p_id}.json")
                st.rerun()
            if col3.button("🎤", key=f"start_{p_id}"):
                link_real = encontrar_link_real(normalizar_nome(p.get('musica')))
                if link_real:
                    requests.put(url_status, json={"acao": "contagem", "cantor": p.get('cantor'), "musica": p.get('musica'), "url_video": link_real, "comando": "play"})
                    st.rerun()
    else:
        st.write("Fila vazia.")

    # --- CONTROLO REMOTO ---
    st.divider()
    st.subheader("🎮 Controlo Remoto")
    c1, c2, c3, c4, c5 = st.columns(5)
    if c1.button("⏸️ Pause"): requests.patch(url_status, json={"comando": "pause"})
    if c2.button("▶️ Play"): requests.patch(url_status, json={"comando": "play"})
    if c3.button("🔄 Repetir"): requests.patch(url_status, json={"comando": "repeat"})
    if c4.button("⏪ -10s"): requests.patch(url_status, json={"comando": "voltar"})
    if c5.button("⏩ +10s"): requests.patch(url_status, json={"comando": "avancar"})
    
    time.sleep(5) # Atualiza a fila a cada 5 segundos
    st.rerun()
