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
    
    pedidos_data = requests.get(f"{BASE_URL}/pedidos_{st.session_state.slug}.json").json()
    
    if pedidos_data:
        for p_id, p in pedidos_data.items():
            col1, col2, col3 = st.columns([4, 1, 1])
            col1.write(f"🎤 {p.get('cantor')} - {p.get('musica')}")
            if col2.button("🗑️", key=f"del_{p_id}"): 
                requests.delete(f"{BASE_URL}/pedidos_{st.session_state.slug}/{p_id}.json"); st.rerun()
            
            if col3.button("🎤", key=f"start_{p_id}"):
                # Efeito de anúncio Estilo Herman José
                texto_anuncio = f"Senhoras e senhores, meus amigos! É um privilégio enorme receber aqui no nosso palco, o magnífico, o extraordinário {p.get('cantor')}! Que nos vai presentear com o tema {p.get('musica')}. Uma salva de palmas, por favor!"
                
                st.components.v1.html(f"""
                    <script>
                        // Função para falar e depois tocar palmas
                        var msg = new SpeechSynthesisUtterance("{texto_anuncio}");
                        msg.lang = 'pt-PT';
                        msg.pitch = 0.7; // Voz bem masculina e grave
                        msg.rate = 1.0;  // Ritmo natural
                        msg.volume = 1.0;
                        
                        msg.onend = function() {{
                            var audio = new Audio('https://www.myinstants.com/media/sounds/applause.mp3');
                            audio.play();
                        }};
                        
                        window.speechSynthesis.speak(msg);
                    </script>
                """, height=0)
                
                link = encontrar_link_real(normalizar_nome(p.get('musica')))
                if link: 
                    requests.put(url_status, json={
                        "acao": "contagem", "cantor": p.get('cantor'), 
                        "musica": p.get('musica'), "url_video": link, "comando": "play"
                    })
                    st.rerun()
    else:
        st.write("Fila vazia.")
    
    st.markdown("---")
    st.subheader("🎮 Controlo Remoto")
    if st.button("🔄 RECOMEÇAR MÚSICA"): requests.patch(url_status, json={"comando": "repeat"})
    
    time.sleep(5)
    st.rerun()
