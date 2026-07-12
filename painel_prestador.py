import streamlit as st
impor
    st.image(buf.getvalue(), caption="Imprima este QR Code para seus clientes")
    
    if st.button("Sair"):
        st.session_state["prestador_id"] = None
        st.rerun()
