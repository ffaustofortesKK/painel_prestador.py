import streamlit as st
import qrcode
from io import BytesIO
from supabase import create_client
import requests
from bs4 import BeautifulSoup

# ... (Mantenha o resto das suas configurações de Supabase e Estilo intactas)

# --- FUNÇÃO DE BUSCA OTIMIZADA ---
def buscar_musicas(termo):
    # O Nephobox exige que o cabeçalho pareça um navegador real
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    url_base = "https://www.nephobox.com/portuguese/main?category=all&path=%2FKARAOKE"
    
    try:
        response = requests.get(url_base, headers=headers, timeout=10)
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # O Nephobox costuma listar arquivos em tags específicas. 
        # Vamos buscar todos os textos que possam ser nomes de músicas/arquivos
        # Se o site usa JS, a lista pode estar dentro de um JSON escondido na página
        resultados = []
        # Tenta pegar elementos comuns de lista de arquivos
        for item in soup.find_all(['a', 'div', 'span'], class_=lambda x: x and 'name' in x):
            if termo.lower() in item.text.lower():
                resultados.append(item.text.strip())
        
        # Se não encontrar nada via tags específicas, busca no texto puro da página
        if not resultados:
            texto_pagina = soup.get_text()
            # Lógica simples para extrair linhas que contenham o termo
            linhas = [l.strip() for l in texto_pagina.split('\n') if termo.lower() in l.lower()]
            resultados = linhas
            
        return list(set(resultados[:10])) if resultados else ["Nenhuma música encontrada (Verifique se o site requer login)."]
    except Exception as e:
        return [f"Erro ao acessar a nuvem: {e}"]

# --- PAINEL (Onde a busca acontece) ---
else:
    st.title(f"🎤 Bem-vindo, {st.session_state['nome']}!")
    
    # ... (Seu código de Link e QR Code aqui)

    # Interface de Busca e Adição
    st.markdown('<div class="big-box">', unsafe_allow_html=True)
    st.subheader("🔍 Pesquisar na Nuvem")
    termo = st.text_input("Nome da Música:")
    
    # Botão de busca com estado
    if st.button("Buscar na Biblioteca"):
        with st.spinner('Procurando na nuvem...'):
            st.session_state["resultados"] = buscar_musicas(termo)
    
    # Exibir resultados
    if "resultados" in st.session_state:
        selecionada = st.selectbox("Selecione a música desejada:", st.session_state["resultados"])
        if st.button("Adicionar à Lista"):
            st.success(f"Adicionando: {selecionada}...")
            # Aqui você inseriria no Supabase
    st.markdown('</div>', unsafe_allow_html=True)

    # ... (Resto do código)
