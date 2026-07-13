import streamlit as st
import qrcode
from io import BytesIO
from supabase import create_client
import requests
from bs4 import BeautifulSoup

# Configuração do Supabase
url = st.secrets["URL_SUPABASE"]
key = st.secrets["KEY_SUPABASE"]
supabase = create_client(url, key)

st.set_page_config(page_title="Painel do Prestador", layout="centered")

# --- ESTILO DARK MODE ---
st.markdown("""
    <style>
    .stApp { background-color: #0e0e0e; }
    h1, h2, h3, p, label, div { color: #ffffff !important; }
    .big-box { background-color: #1a1a1a; padding: 20px; border-radius: 10px; border: 1px solid #333; margin-bottom: 10px; }
    </style>
""", unsafe_allow_html=True)

# --- FUNÇÃO DE BUSCA ---
def buscar_musicas(termo):
    headers = {"User-Agent": "Mozilla/5.0"}
    url_base = "https://www.nephobox.com/portuguese/main?category=all&path=%2FKARAOKE"
    try:
        response = requests.get(url_base, headers=headers, timeout=10)
        soup = BeautifulSoup(response.content, 'html.parser')
        resultados = [item.text.strip() for item in soup.find_all(['a', 'div', 'span']) if termo.lower() in item.text.lower()]
        return list(set(resultados[:10])) if resultados else ["Nenhuma música encontrada."]
    except Exception as e:
        return [f"Erro: {e}"]

# Inicializar sessão
if "prestador_id" not in st.session_state:
    st.session_state["prestador_id"] = None

# --- FLUXO PRINCIPAL ---
if st.session_state["prestador_id"] is None:
    st.title("🎤 Portal do Prestador")
    nome = st.text_input("Nome de Usuário:")
    senha = st.text_input("Senha:", type="password")
    if st.button("Entrar"):
        res = supabase.table("prestadores").select("*").eq("nome_prestador", nome).eq("senha_acesso", senha).execute()
        if res.data:
            st.session_state["prestador_id"] = res.data[0]["id"]
            st.session_state["nome"] = res.data[0]["nome_prestador"]
            st.session_state["slug"] = res.data[0]["slug_unico"]
            st.rerun()
        else:
            st.error("Credenciais inválidas!")
else:
    st.title(f"Bem-vindo, {st.session_state['nome']}!")
    slug = st.session_state["slug"]
    
    # 1. LINK E QR CODE (O Elo de Ligação)
    url_cliente = f"https://ffkaraoke-cliente.streamlit.app/?prestador={slug}"
    st.info(f"Link de acesso para seus clientes:")
    st.code(url_cliente)
    
    qr = qrcode.make(url_cliente)
    buf = BytesIO()
    qr.save(buf, format="PNG")
    st.image(buf.getvalue(), width=150, caption="QR Code do Prestador")

    st.divider()

    # 2. FILA DE PEDIDOS (Conexão Firebase)
    st.subheader("📋 Pedidos Recebidos")
    url_fila = f"https://grupoffkaraoke-default-rtdb.firebaseio.com/pedidos_{slug}.json"
    if st.button("🔄 Atualizar Fila"):
        try:
            resp = requests.get(url_fila)
            pedidos = resp.json()
            if pedidos:
                for chave, p in pedidos.items():
                    st.success(f"🎤 {p.get('cantor')}: {p.get('musica')}")
            else:
                st.write("Nenhum pedido novo.")
        except:
            st.error("Erro ao buscar fila.")

    # 3. BUSCA NA NUVEM
    st.markdown('<div class="big-box">', unsafe_allow_html=True)
    st.subheader("🔍 Pesquisar na Nuvem")
    termo = st.text_input("Nome da Música:")
    if st.button("Buscar"):
        st.session_state["resultados"] = buscar_musicas(termo)
    
    if "resultados" in st.session_state:
        selecionada = st.selectbox("Resultado:", st.session_state["resultados"])
        st.info(f"Música selecionada para o cliente: {selecionada}")
    st.markdown('</div>', unsafe_allow_html=True)

    if st.button("Sair"):
        st.session_state["prestador_id"] = None
        st.rerun()
