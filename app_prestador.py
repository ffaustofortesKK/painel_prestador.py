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
cloudinary.config(cloud_name="yhwgjh7g", api_key="347924379441394", api_secret="_gzZOnOmzIk6dlmferYm6ck8S08")

st.set_page_config(page_title="Painel do Prestador", layout="wide")

# Inicialização segura do estado
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

# --- ESTRUTURA DA PÁGINA ---

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
    if st.sidebar.button("Sair (Limpar Sessão)"):
        st.session_state.nome = None
        st.session_state.slug = None
        st.rerun()
        
    st.title(f"🎤 Bem-vindo, {st.session_state.nome}!")
    st.markdown("---")

    # CARREGAR PEDIDOS
    pedidos = requests.get(f"{BASE_URL}/pedidos_{st.session_state.slug}.json").json() or {}
    
    st.subheader("Fila de Pedidos")
    if not pedidos:
        st.info("Nenhum pedido na fila.")
    else:
        for p_id, p in pedidos.items():
            col1, col2 = st.columns([4, 1])
            col1.write(f"🎤 {p.get('cantor')} - {p.get('musica')}")
            
            if col2.button("Chamar", key=f"btn_{p_id}"):
                # LÓGICA DE CHAMADA: Atualiza o status para o cliente captar
                nome_musica = p.get('musica')
                link = encontrar_link_real(normalizar_nome(nome_musica))
                
                payload = {
                    "cantor": p.get('cantor'),
                    "musica": nome_musica,
                    "url_video": link,
                    "comando": "aguardando_play"
                }
                requests.put(f"{BASE_URL}/status_{st.session_state.slug}.json", json=payload)
                st.toast(f"Chamando {p.get('cantor')}...")
                time.sleep(1)
                st.rerun()

    # Botão para forçar play (se necessário)
    if st.button("▶️ FORÇAR PLAY"):
        requests.patch(f"{BASE_URL}/status_{st.session_state.slug}.json", json={"comando": "play"})
        st.rerun()
