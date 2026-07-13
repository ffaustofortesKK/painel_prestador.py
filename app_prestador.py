import streamlit as st
import qrcode
from io import BytesIO
from supabase import create_client
import requests

# Configuração do Supabase
url = st.secrets["URL_SUPABASE"]
key = st.secrets["KEY_SUPABASE"]
supabase = create_client(url, key)

st.set_page_config(page_title="Painel do Prestador", layout="centered")

if "prestador_id" not in st.session_state: st.session_state.prestador_id = None

# --- LOGIN / REGISTRO AUTOMÁTICO ---
if st.session_state.prestador_id is None:
    st.title("🎤 Portal do Prestador")
    
    # Captura os dados
    nome_input = st.text_input("Nome:")
    sobrenome_input = st.text_input("Sobrenome:") 
    telef = st.text_input("Telefone:")
    
    if st.button("Entrar"):
        if nome_input and sobrenome_input and telef:
            try:
                # 1. Tenta buscar pelo telefone
                res = supabase.table("prestadores").select("*").eq("telefone", telef).execute()
                
                if res.data and len(res.data) > 0:
                    st.session_state.update({
                        "prestador_id": res.data[0]["id"],
                        "nome": f"{nome_input} {sobrenome_input}",
                        "slug": res.data[0]["slug_unico"]
                    })
                    st.rerun()
                else:
                    # 2. Cadastro automático (Usando nomes exatos das suas colunas)
                    slug_novo = f"{nome_input.lower()}-{sobrenome_input.lower()}"
                    
                    novo_prestador = {
                        "Nome": nome_input,        # Mantido com 'N' maiúsculo
                        "Sobrenome": sobrenome_input, # Alterado para 'Sobrenome'
                        "telefone": telef,
                        "slug_unico": slug_novo
                    }
                    
                    supabase.table("prestadores").insert(novo_prestador).execute()
                    
                    # Busca o ID após inserir
                    res = supabase.table("prestadores").select("*").eq("telefone", telef).execute()
                    
                    if res.data:
                        st.session_state.update({
                            "prestador_id": res.data[0]["id"],
                            "nome": f"{nome_input} {sobrenome_input}",
                            "slug": slug_novo
                        })
                        st.success("Cadastro realizado com sucesso!")
                        st.rerun()
                    else:
                        st.error("Erro ao validar cadastro no banco.")
            except Exception as e:
                st.error(f"Erro no banco: {e}")
        else:
            st.error("⚠️ Preencha todos os campos.")

else:
    # --- PAINEL PRINCIPAL ---
    st.title(f"Bem-vindo, {st.session_state.nome}!")
    
    url_cliente = f"https://ffkaraoke-cliente.streamlit.app/?prestador={st.session_state.slug}"
    st.info("Link de acesso para seus clientes:")
    st.code(url_cliente)
    
    qr = qrcode.make(url_cliente)
    buf = BytesIO()
    qr.save(buf, format="PNG")
    st.image(buf.getvalue(), width=150)

    st.subheader("📋 Pedidos Recebidos")
    if st.button("🔄 Atualizar Fila"):
        url_fila = f"https://grupoffkaraoke-default-rtdb.firebaseio.com/pedidos_{st.session_state.slug}.json"
        try:
            pedidos = requests.get(url_fila).json()
            if pedidos:
                for chave, p in pedidos.items(): st.success(f"🎤 {p.get('cantor')}: {p.get('musica')}")
            else: st.write("Fila vazia.")
        except: st.error("Erro ao carregar pedidos.")

    if st.button("Sair"):
        st.session_state.prestador_id = None
        st.rerun()
