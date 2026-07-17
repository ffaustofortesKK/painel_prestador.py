import streamlit as st
import qrcode
import re
import unicodedata
import cloudinary
import cloudinary.api
from io import BytesIO
import requests
import time

cloudinary.config(cloud_name="yhwgjh7g", api_key="347924379441394", api_secret="_gzZOnOmzIk6dlmferYm6ck8S08")

st.set_page_config(page_title="Painel do Prestador", layout="wide")

if "nome" not in st.session_state: st.session_state.nome = None
if "slug" not in st.session_state: st.session_state.slug = None

BASE_URL = "https://grupoffkaraoke-default-rtdb.firebaseio.com"

def normalizar_nome(nome):
    nome = nome.replace(".mp4", "")
    nome = re.sub(r'["\'()\[\]]', '', nome)
    nome = unicodedata.normalize('NFKD', nome).encode('ASCII', 'ignore').decode('utf-8')
    nome = re.sub(r'[^\w\s]', '', nome)
    return "_".join(nome.split())

def encontrar_link_real(nome_base):
    try:
        resources = cloudinary.api.resources(type="upload", resource_type="video", prefix=nome_base, max_results=1)
        if resources['resources']:
            return resources['resources'][0]['secure_url'] 
    except: return None

if st.session_state.nome is None:
    st.title("🎤 Portal do Prestador")
    with st.form("login_form"):
        nome_input = st.text_input("Nome:")
        sobrenome_input = st.text_input("Sobrenome:")
        telef = st.text_input("Telefone:")
        if st.form_submit_button("Entrar"):
            if nome_input and sobrenome_input and telef:
                slug_unico = f"{nome_input.lower()}-{sobrenome_input.lower()}"
                telef_limpo = telef.replace(" ", "").replace("-", "")
                requests.put(f"{BASE_URL}/prestadores/{telef_limpo}.json", json={"nome": f"{nome_input} {sobrenome_input}", "slug": slug_unico})
                st.session_state.nome = f"{nome_input} {sobrenome_input}"
                st.session_state.slug = slug_unico
                st.rerun()
else:
    st.sidebar.title("Configurações")
    if st.sidebar.button("Sair"): st.session_state.nome = None; st.session_state.slug = None; st.rerun()
        
    st.title(f"🎤 Bem-vindo, {st.session_state.nome}!")
    url_cliente = f"https://appcliente.streamlit.app/?prestador={st.session_state.slug}"
    c1, c2 = st.columns([2, 1])
    c1.info(f"🔗 **Cliente:** {url_cliente}")
    qr = qrcode.make(url_cliente); buf = BytesIO(); qr.save(buf, format="PNG"); c2.image(buf.getvalue(), width=100)
    
    url_status = f"{BASE_URL}/status_{st.session_state.slug}.json"
    pedidos_data = requests.get(f"{BASE_URL}/pedidos_{st.session_state.slug}.json").json() or {}
    
    if pedidos_data:
        for p_id, p in pedidos_data.items():
            if not str(p.get('musica', '')).startswith("PEDIDO:"):
                col1, col2, col3 = st.columns([4, 1, 1])
                col1.write(f"🎤 {p.get('cantor')} - {p.get('musica')}")
                if col2.button("🗑️", key=f"del_{p_id}"): 
                    requests.delete(f"{BASE_URL}/pedidos_{st.session_state.slug}/{p_id}.json"); st.rerun()
                if col3.button("🎤", key=f"start_{p_id}"):
                    link = encontrar_link_real(normalizar_nome(p.get('musica')))
                    if link: 
                        # CORREÇÃO AQUI: Enviando o comando correto para o cliente ler
                        requests.put(url_status, json={
                            "cantor": p.get('cantor'), 
                            "musica": p.get('musica'), 
                            "url_video": link, 
                            "comando": "aguardando_play" 
                        })
                        st.rerun()
    st.divider()
    if st.button("▶️ FORÇAR INÍCIO"): requests.patch(url_status, json={"comando": "play"}); st.rerun()
    time.sleep(3); st.rerun()
