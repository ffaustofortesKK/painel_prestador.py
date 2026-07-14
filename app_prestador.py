import streamlit as st
import qrcode
from io import BytesIO
from supabase import create_client
import requests

# Configuração do Supabase
url = st.secrets["URL_SUPABASE"]
key = st.secrets["KEY_SUPABASE"]
supabase = create_client(url, key)

st.set_page_config(page_title="Painel do Prestador", layout="wide")

# --- INICIALIZAÇÃO SEGURA DO ESTADO ---
if "prestador_id" not in st.session_state: st.session_state.prestador_id = None
if "nome" not in st.session_state: st.session_state.nome = None
if "slug" not in st.session_state: st.session_state.slug = None

# --- LOGIN / REGISTRO ---
if st.session_state.prestador_id is None:
    st.title("🎤 Portal do Prestador")
    nome_input = st.text_input("Nome:")
    sobrenome_input = st.text_input("Sobrenome:") 
    telef = st.text_input("Telefone:")
    
    if st.button("Entrar"):
        if nome_input and sobrenome_input and telef:
            try:
                res = supabase.table("prestadores").select("*").eq("telefone", telef).execute()
                if res.data and len(res.data) > 0:
                    st.session_state.update({"prestador_id": res.data[0]["id"], "nome": f"{nome_input} {sobrenome_input}", "slug": res.data[0]["slug_unico"]})
                    st.rerun()
                else:
                    slug_novo = f"{nome_input.lower()}-{sobrenome_input.lower()}"
                    supabase.table("prestadores").insert({"Nome": nome_input, "Sobrenome": sobrenome_input, "telefone": telef, "slug_unico": slug_novo}).execute()
                    st.session_state.update({"nome": f"{nome_input} {sobrenome_input}", "slug": slug_novo})
                    st.rerun()
            except Exception as e:
                st.error(f"Erro: {e}")

else:
    # --- PAINEL PRINCIPAL ---
    st.title(f"Bem-vindo, {st.session_state.nome}!")
    
    url_fila = f"https://grupoffkaraoke-default-rtdb.firebaseio.com/pedidos_{st.session_state.slug}.json"
    
    # Exibir Link e QR Code
    url_cliente = f"https://ffkaraoke-cliente.streamlit.app/?prestador={st.session_state.slug}"
    with st.expander("🔗 Link de Acesso"):
        st.code(url_cliente)
        qr = qrcode.make(url_cliente)
        buf = BytesIO()
        qr.save(buf, format="PNG")
        st.image(buf.getvalue(), width=120)

    st.subheader("📋 Gestão de Fila")
    
    if st.button("🔄 Atualizar Fila"):
        st.rerun()
        
    try:
        pedidos_data = requests.get(url_fila).json()
        if pedidos_data:
            # Lista de pedidos para manipulação
            lista_pedidos = list(pedidos_data.items())
            
            for i, (p_id, p) in enumerate(lista_pedidos):
                col1, col2, col3, col4 = st.columns([4, 1, 1, 1])
                col1.write(f"**{i+1}.** {p.get('cantor')} - {p.get('musica')}")
                
                # Ação: Remover
                if col2.button("🗑️", key=f"del_{p_id}"):
                    requests.delete(f"https://grupoffkaraoke-default-rtdb.firebaseio.com/pedidos_{st.session_state.slug}/{p_id}.json")
                    st.rerun()
                
                # Ação: Anunciar e Iniciar (Envia para o Firebase da TV)
                if col3.button("🎤", key=f"start_{p_id}", help="Anunciar e Iniciar Contagem"):
                    requests.patch(f"https://grupoffkaraoke-default-rtdb.firebaseio.com/status_{st.session_state.slug}.json", 
                                   json={"acao": "contagem", "cantor": p.get('cantor')})
                    st.success("Enviado para TV!")
                    
        else:
            st.write("Fila vazia.")
    except:
        st.error("Erro ao conectar com a fila.")

    if st.button("Sair"):
        st.session_state.clear()
        st.rerun()
