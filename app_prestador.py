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

# Inicialização segura
if "prestador_id" not in st.session_state: st.session_state.prestador_id = None
if "nome" not in st.session_state: st.session_state.nome = None
if "slug" not in st.session_state: st.session_state.slug = None

# --- LOGIN ---
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
    
    # Links de Acesso
    url_cliente = f"https://appcliente.streamlit.app/?prestador={st.session_state.slug}"
    url_tv = f"https://ffktela.streamlit.app/?prestador={st.session_state.slug}"
    
    col_link, col_qr = st.columns([2, 1])
    with col_link:
        st.info("🔗 Link para seus Clientes:")
        st.code(url_cliente)
        st.info("📺 Link para a sua TV:")
        st.code(url_tv)
    with col_qr:
        # Correção do erro do QR Code
        qr = qrcode.make(url_cliente)
        buf = BytesIO()
        qr.save(buf, format="PNG")
        st.image(buf.getvalue(), width=120, caption="QR Code Cliente")

    st.divider()
    st.subheader("📋 Gestão de Fila")
    
    if st.button("🔄 Atualizar Fila"): st.rerun()
    
    base_url = "https://grupoffkaraoke-default-rtdb.firebaseio.com"
    url_fila = f"{base_url}/pedidos_{st.session_state.slug}.json"
    url_status = f"{base_url}/status_{st.session_state.slug}.json"
    
    try:
        pedidos_data = requests.get(url_fila).json()
        if pedidos_data:
            for p_id, p in pedidos_data.items():
                col1, col2, col3 = st.columns([4, 1, 1])
                nome_musica = p.get('musica')
                col1.write(f"🎤 {p.get('cantor')} - {nome_musica}")
                
                if col2.button("🗑️", key=f"del_{p_id}"):
                    requests.delete(f"{base_url}/pedidos_{st.session_state.slug}/{p_id}.json")
                    st.rerun()
                
                if col3.button("🎤", key=f"start_{p_id}"):
                    # BUSCA AUTOMÁTICA NO SUPABASE
                    # Certifique-se que a sua tabela no Supabase chama-se 'musicas' 
                    # e tem as colunas 'nome' e 'link'
                    musica_db = supabase.table("musicas").select("link").eq("nome", nome_musica).execute()
                    
                    link_encontrado = ""
                    if musica_db.data and len(musica_db.data) > 0:
                        link_encontrado = musica_db.data[0]["link"]
                    
                    if link_encontrado:
                        requests.put(url_status, json={
                            "acao": "contagem", 
                            "cantor": p.get('cantor'), 
                            "musica": nome_musica,
                            "url_video": link_encontrado
                        })
                        st.success(f"Enviado para TV: {nome_musica}")
                        st.rerun()
                    else:
                        st.error(f"Vídeo de '{nome_musica}' não encontrado na tabela 'musicas' do Supabase!")
        else: 
            st.write("Fila vazia.")
    except Exception as e:
        st.error(f"Erro ao processar fila: {e}")
