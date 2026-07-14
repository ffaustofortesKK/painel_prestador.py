import streamlit as st
import qrcode
from io import BytesIO
from supabase import create_client
import requests

# Configuração do Supabase (utiliza os valores salvos no Streamlit Cloud Secrets)
url = st.secrets["URL_SUPABASE"]
key = st.secrets["KEY_SUPABASE"]
supabase = create_client(url, key)

st.set_page_config(page_title="Painel do Prestador", layout="centered")

# Inicialização de estado para manter o prestador logado
if "prestador_id" not in st.session_state: 
    st.session_state.prestador_id = None
if "nome" not in st.session_state: 
    st.session_state.nome = None
if "slug" not in st.session_state: 
    st.session_state.slug = None

# --- LOGIN / REGISTRO AUTOMÁTICO ---
if st.session_state.prestador_id is None:
    st.title("🎤 Portal do Prestador")
    st.write("Insira seus dados para acessar o seu painel de gerenciamento.")
    
    nome_input = st.text_input("Nome:")
    sobrenome_input = st.text_input("Sobrenome:") 
    telef = st.text_input("Telefone:")
    
    if st.button("Entrar / Cadastrar"):
        if nome_input and sobrenome_input and telef:
            try:
                # 1. Tenta buscar prestador pelo telefone
                res = supabase.table("prestadores").select("*").eq("telefone", telef).execute()
                
                if res.data and len(res.data) > 0:
                    st.session_state.update({
                        "prestador_id": res.data[0]["id"],
                        "nome": f"{nome_input} {sobrenome_input}",
                        "slug": res.data[0]["slug_unico"]
                    })
                    st.rerun()
                else:
                    # 2. Cadastro automático
                    slug_novo = f"{nome_input.lower()}-{sobrenome_input.lower()}"
                    novo_prestador = {
                        "Nome": nome_input,
                        "Sobrenome": sobrenome_input,
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
            except Exception as e:
                st.error(f"Erro ao conectar ao banco: {e}")
        else:
            st.warning("⚠️ Por favor, preencha todos os campos.")

else:
    # --- PAINEL PRINCIPAL ---
    st.title(f"Bem-vindo, {st.session_state.nome}!")
    
    # Gerador de Link Dinâmico para o Cliente
    # Certifique-se de que o URL abaixo corresponde ao seu app do cliente
    url_cliente = f"https://ffkaraoke-cliente.streamlit.app/?prestador={st.session_state.slug}"
    
    st.info("🔗 Link de acesso exclusivo para seus clientes:")
    st.code(url_cliente)
    
    # Geração do QR Code
    qr = qrcode.make(url_cliente)
    buf = BytesIO()
    qr.save(buf, format="PNG")
    st.image(buf.getvalue(), width=150, caption="QR Code para Clientes")

    st.divider()
    st.subheader("📋 Pedidos Recebidos")
    
    # Botão para atualizar a fila específica no Firebase
    if st.button("🔄 Atualizar Fila de Pedidos"):
        # A URL aponta para a fila exclusiva deste prestador
        url_fila = f"https://grupoffkaraoke-default-rtdb.firebaseio.com/pedidos_{st.session_state.slug}.json"
        
        try:
            resposta = requests.get(url_fila)
            pedidos = resposta.json()
            
            if pedidos:
                # Exibe a lista de pedidos
                for chave, p in pedidos.items():
                    st.success(f"🎤 **{p.get('cantor')}**: {p.get('musica')}")
            else:
                st.info("A fila de pedidos está vazia no momento.")
        except Exception as e:
            st.error("Erro ao carregar pedidos. Verifique sua conexão com o Firebase.")

    st.divider()
    if st.button("Sair da Conta"):
        # Limpa o estado da sessão para garantir segurança
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()
