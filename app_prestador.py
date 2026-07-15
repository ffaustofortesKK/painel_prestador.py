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

# FUNÇÃO ROBUSTA: Remove acentos e padroniza o nome
def normalizar_nome(nome):
    nome = nome.replace(".mp4", "")
    # Remove acentos (converte "Dúnem" para "Dunem")
    nome = unicodedata.normalize('NFKD', nome).encode('ASCII', 'ignore').decode('utf-8')
    # Remove caracteres especiais
    nome = re.sub(r'[^\w\s]', '', nome)
    # Substitui espaços por underline
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
    col_link, col_qr = st.columns([2, 1])
    with col_link:
        st.info("🔗 Link para seus Clientes:")
        st.code(url_cliente)
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
                    # ATENÇÃO: Se o nome no Firebase não for idêntico ao do Cloudinary, 
                    # a URL não vai funcionar. 
                    nome_tecnico = normalizar_nome(nome_musica)
                    
                    # Se todos os seus ficheiros tiverem o sufixo _jmzrrn, mantenha.
                    # Se cada ficheiro tiver um sufixo diferente, você TEM que remover esses sufixos no Cloudinary.
                    link_montado = f"https://res.cloudinary.com/{CLOUDINARY_CLOUD_NAME}/video/upload/{nome_tecnico}"
                    
                    requests.put(url_status, json={
                        "acao": "contagem", 
                        "cantor": p.get('cantor'), 
                        "musica": nome_musica,
                        "url_video": link_montado
                    })
                    st.success(f"Enviado para TV: {nome_musica}")
                    st.rerun()
        else: 
            st.write("Fila vazia.")
    except Exception as e:
        st.error(f"Erro ao processar fila: {e}")
