import streamlit as st
import qrcode
import re
import unicodedata
import cloudinary
import cloudinary.api
from io import BytesIO
import requests

# Configuração Cloudinary
cloudinary.config( 
  cloud_name = "yhwgjh7g", 
  api_key = st.secrets["CLOUDINARY_API_KEY"], 
  api_secret = st.secrets["CLOUDINARY_API_SECRET"]
)

st.set_page_config(page_title="Painel do Prestador", layout="wide")

# Inicialização
if "nome" not in st.session_state: st.session_state.nome = None
if "slug" not in st.session_state: st.session_state.slug = None

BASE_URL = "https://grupoffkaraoke-default-rtdb.firebaseio.com"

def normalizar_nome(nome):
    nome = nome.replace(".mp4", "")
    nome = unicodedata.normalize('NFKD', nome).encode('ASCII', 'ignore').decode('utf-8')
    nome = re.sub(r'[^\w\s]', '', nome)
    # Trocamos espaços por underscore para combinar com o início do arquivo no Cloudinary
    nome = "_".join(nome.split())
    return nome

def buscar_url_no_cloudinary(nome_base):
    # Busca vídeos que começam com o nome normalizado
    try:
        # Busca recursos que iniciam com o nome da música
        res = cloudinary.api.resources(
            type="upload", resource_type="video", prefix=nome_base, max_results=1
        )
        if res['resources']:
            return res['resources'][0]['secure_url']
    except Exception:
        return None
    return None

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
    
    # ... (Seu código de Links e QR Code mantém-se igual)

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
                    nome_base = normalizar_nome(nome_musica)
                    # Busca o link real ignorando o sufixo aleatório do Cloudinary
                    link_real = buscar_url_no_cloudinary(nome_base)
                    
                    if link_real:
                        requests.put(url_status, json={
                            "acao": "contagem", 
                            "cantor": p.get('cantor'), 
                            "musica": nome_musica,
                            "url_video": link_real
                        })
                        st.success(f"Enviado para TV: {nome_musica}")
                    else:
                        st.error(f"Vídeo não encontrado no Cloudinary (Nome buscado: {nome_base})")
                    st.rerun()
        else: 
            st.write("Fila vazia.")
    except Exception as e:
        st.error(f"Erro ao processar fila: {e}")
