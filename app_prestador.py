import streamlit as st
import qrcode
from io import BytesIO
from supabase import create_client
import requests

# Configuração Supabase
url = st.secrets["URL_SUPABASE"]
key = st.secrets["KEY_SUPABASE"]
supabase = create_client(url, key)

st.set_page_config(page_title="Painel do Prestador", layout="wide")

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
            res = supabase.table("prestadores").select("*").eq("telefone", telef).execute()
            if res.data and len(res.data) > 0:
                st.session_state.update({"prestador_id": res.data[0]["id"], "nome": f"{nome_input} {sobrenome_input}", "slug": res.data[0]["slug_unico"]})
                st.rerun()
            else:
                slug_novo = f"{nome_input.lower()}-{sobrenome_input.lower()}"
                supabase.table("prestadores").insert({"Nome": nome_input, "Sobrenome": sobrenome_input, "telefone": telef, "slug_unico": slug_novo}).execute()
                st.session_state.update({"nome": f"{nome_input} {sobrenome_input}", "slug": slug_novo})
                st.rerun()
else:
    st.title(f"Bem-vindo, {st.session_state.nome}!")
    url_fila = f"https://grupoffkaraoke-default-rtdb.firebaseio.com/pedidos_{st.session_state.slug}.json"
    
    # Gerar link dinâmico
    url_cliente = f"https://ffkaraoke-cliente.streamlit.app/?prestador={st.session_state.slug}"
    st.code(url_cliente)
    
    if st.button("🔄 Atualizar Fila"): st.rerun()
    
    try:
        pedidos_data = requests.get(url_fila).json()
        if pedidos_data:
            for p_id, p in pedidos_data.items():
                col1, col2, col3 = st.columns([4, 1, 1])
                col1.write(f"🎤 {p.get('cantor')} - {p.get('musica')}")
                if col2.button("🗑️", key=f"del_{p_id}"):
                    requests.delete(f"https://grupoffkaraoke-default-rtdb.firebaseio.com/pedidos_{st.session_state.slug}/{p_id}.json")
                    st.rerun()
                if col3.button("🎤", key=f"start_{p_id}"):
                    requests.patch(f"https://grupoffkaraoke-default-rtdb.firebaseio.com/status_{st.session_state.slug}.json", json={"acao": "contagem", "cantor": p.get('cantor')})
        else: st.write("Fila vazia.")
    except: st.error("Erro ao conectar.")
    
    if st.button("Sair"): st.session_state.clear(); st.rerun()
