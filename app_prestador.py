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

    

    url_cliente = f"https://appcliente.streamlit.app/?prestador={st.session_state.slug}"

    url_tv = f"https://ffktela.streamlit.app/?prestador={st.session_state.slug}"

    

    c1, c2 = st.columns([2, 1])

    c1.info(f"🔗 **Cliente:** {url_cliente}")

    c1.info(f"📺 **TV:** {url_tv}")

    qr = qrcode.make(url_cliente); buf = BytesIO(); qr.save(buf, format="PNG"); c2.image(buf.getvalue(), width=100)

    

    url_status = f"{BASE_URL}/status_{st.session_state.slug}.json"

    st.subheader("📋 Gestão de Fila")

    

    pedidos_data = requests.get(f"{BASE_URL}/pedidos_{st.session_state.slug}.json").json() or {}

    

    if pedidos_data:

        for p_id, p in pedidos_data.items():

            # Filtra apenas pedidos normais (exclui os manuais para esta lista)

            if not str(p.get('musica', '')).startswith("PEDIDO:"):

                col1, col2, col3 = st.columns([4, 1, 1])

                col1.write(f"🎤 {p.get('cantor')} - {p.get('musica')}")

                if col2.button("🗑️", key=f"del_{p_id}"): 

                    requests.delete(f"{BASE_URL}/pedidos_{st.session_state.slug}/{p_id}.json"); st.rerun()

                

                if col3.button("🎤", key=f"start_{p_id}"):

                    link = encontrar_link_real(normalizar_nome(p.get('musica')))

                    if link: 

                        requests.put(url_status, json={

                            "acao": "contagem", "cantor": p.get('cantor'), 

                            "musica": p.get('musica'), "url_video": link, "comando": "aguardando_play" 

                        })

                        st.rerun()

        

        st.markdown("---")

        if st.button("▶️ FORÇAR INÍCIO DE MÚSICA (IMEDIATO)"):

            requests.patch(url_status, json={"comando": "play"})

            st.rerun()

    else:

        st.write("Fila vazia.")



    # --- CAIXA DE PEDIDOS MANUAIS ---

    st.markdown("---")

    st.subheader("⚠️ Pedidos Manuais (Atenção)")

    

    pedidos_manuais = {k: v for k, v in pedidos_data.items() if str(v.get('musica', '')).startswith("PEDIDO:")}

    

    if pedidos_manuais:

        st.markdown("""

            <style>

                .blink { animation: blinker 1s linear infinite; color: yellow; font-weight: bold; 

                         background-color: rgba(255, 255, 0, 0.1); padding: 10px; border: 2px solid yellow; border-radius: 10px; }

                @keyframes blinker { 50% { opacity: 0; } }

            </style>

        """, unsafe_allow_html=True)

        

        for p_id, p in pedidos_manuais.items():

            st.markdown(f'<div class="blink">📢 {p.get("cantor")}: {p.get("musica")}</div>', unsafe_allow_html=True)

            if st.button(f"Remover aviso {p_id[:4]}", key=f"del_man_{p_id}"):

                requests.delete(f"{BASE_URL}/pedidos_{st.session_state.slug}/{p_id}.json")

                st.rerun()

    else:

        st.success("Nenhum pedido manual pendente.")

            

    time.sleep(5)

    st.rerun()
