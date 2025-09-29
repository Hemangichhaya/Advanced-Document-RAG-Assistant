# app.py
import streamlit as st
from state import init_session_state
from sidebar import setup_sidebar
from ui import document_upload_tab, summary_tab
from chat import chat_tab

def main():
    init_session_state()
    st.set_page_config(page_title="Advanced Document RAG", page_icon="📄", layout="wide")
    st.title("📄 Advanced Document RAG Assistant")
    selected_model, api_key = setup_sidebar()
    tab1, tab2, tab3 = st.tabs(["📁 Upload", "💬 Chat", "📋 Summaries"])
    with tab1: 
        document_upload_tab()
    with tab2: 
        chat_tab()
    with tab3: 
        summary_tab()

if __name__ == "__main__":
    main()
