import streamlit as st
import qrcode
import re
import unicodedata
import cloudinary
import cloudinary.api
import cloudinary.search
from io import BytesIO
import requests
import time

# Configuração Cloudinary
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
        search_result = cloudinary.search.search().expression('resource_type:video').max_results(500).execute()
        for res in search_result.get('resources', []):
            public_id = res.get('public_id', '').lower()
            nome_arquivo = public_id.split('/')[-1]
            if nome_base.lower() in nome_arquivo or nome_base.lower() in public_id:
                return res.get('secure_url')
    except Exception as e:
        print(f"Erro ao procurar link real: {e}")
    return None

def obter_lista_video_clipes():
    lista = []
    seen_urls = set()
    
    try:
        search_result = cloudinary.search.search().expression('resource_type:video').max_results(500).execute()
        for item in search_result.get('resources', []):
            pid = item.get('public_id', '')
            url = item.get('secure_url')
            
            if url and url not in seen_urls:
                nome_limpo = pid.split('/')[-1]
                lista.append((nome_limpo, url))
                seen_urls.add(url)
    except Exception as e:
        try:
            result = cloudinary.api.resources(type="upload", resource_type="video", max_results=500)
            for item in result.get('resources', []):
                pid = item.get('public_id', '')
                url = item.get('secure_url')
                if url and url not in seen_urls:
                    nome_limpo = pid.split('/')[-1]
                    lista.append((nome_limpo, url))
                    seen_urls.add(url)
        except Exception as inner_e:
            print(f"Erro ao obter vídeos: {inner_e}")
            
    return lista

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
    
    st.subheader("🎬 Playlist de Vídeos Clipes")
    
    with st.container():
        st.markdown("""
            <style>
                .retangulo-playlist {
                    border: 2px solid #ffd700;
                    padding: 20px;
                    border-radius: 10px;
                    background-color: rgba(255, 215, 0, 0.02);
                    margin-bottom: 20px;
                }
            </style>
        """, unsafe_allow_html=True)
        
        st.markdown('<div class="retangulo-playlist">', unsafe_allow_html=True)
        
        clipes_disponiveis = obter_lista_video_clipes()
        
        if clipes_disponiveis:
            termo_pesquisa = st.text_input("🔍 Pesquisar clipe:", "").strip().lower()
            
            if termo_pesquisa:
                clipes_filtrados = [c for c in clipes_disponiveis if termo_pesquisa in c[0].lower()]
            else:
                clipes_filtrados = clipes_disponiveis
                
            if clipes_filtrados:
                nomes_clipes = [c[0] for c in clipes_filtrados]
                col_p1, col_p2 = st.columns([3, 1])
                with col_p1:
                    clipe_escolhido = st.selectbox("Selecione o clipe encontrado:", nomes_clipes, label_visibility="collapsed")
                with col_p2:
                    if st.button("🚀 Enviar Clipe para Tela"):
                        url_selecionada = next((c[1] for c in clipes_filtrados if c[0] == clipe_escolhido), None)
                        if url_selecionada:
                            requests.patch(url_status, json={
                                "cantor": "VÍDEO CLIPE",
                                "musica": clipe_escolhido,
                                "url_video": url_selecionada,
                                "comando": "clipe"
                            })
                            st.success(f"Clipe '{clipe_escolhido}' enviado com sucesso para a TV!")
                            time.sleep(1)
                            st.rerun()
            else:
                st.warning(f"Nenhum clipe encontrado com o termo '{termo_pesquisa}'.")
        else:
            st.warning("⚠️ Nenhum vídeo encontrado na conta Cloudinary.")
            
        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("---")
    st.subheader("📋 Gestão de Fila")
    
    pedidos_data = requests.get(f"{BASE_URL}/pedidos_{st.session_state.slug}.json").json() or {}
    
    if pedidos_data:
        for p_id, p in pedidos_data.items():
            if not str(p.get('musica', '')).startswith("PEDIDO:"):
                col1, col2, col3 = st.columns([4, 1, 1])
                col1.write(f"🎤 {p.get('cantor')} - {p.get('musica')}")
                if col2.button("🗑️", key=f"del_{p_id}"): 
                    requests.delete(f"{BASE_URL}/pedidos_{st.session_state.slug}/{p_id}.json"); st.rerun()
                
                if col3.button("🎤", key=f"start_{p_id}"):
                    nome_musica = p.get('musica')
                    link = encontrar_link_real(normalizar_nome(nome_musica))
                    
                    if link:
                        requests.put(url_status, json={
                            "cantor": p.get('cantor'), 
                            "musica": nome_musica, 
                            "url_video": link, 
                            "comando": "aguardando_play" 
                        })
                        requests.delete(f"{BASE_URL}/pedidos_{st.session_state.slug}/{p_id}.json")
                        st.rerun()
                    else:
                        st.error(f"❌ Vídeo '{nome_musica}' não foi encontrado no Cloudinary! Verifique o nome.")
        
        st.markdown("---")
        if st.button("▶️ FORÇAR INÍCIO DE MÚSICA (IMEDIATO)"):
            requests.patch(url_status, json={"comando": "executando_karaoke"})
            st.success("Comando de início imediato enviado para a TV!")
            time.sleep(1)
            st.rerun()
    else:
        st.write("Fila vazia.")

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
        
    time.sleep(2)
    st.rerun()
