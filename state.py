# state.py
import streamlit as st
from langchain_core.messages import SystemMessage
from config import DEFAULT_SYSTEM_MESSAGE, DEFAULT_EMBEDDING_MODEL

def init_session_state():
    if "messages" not in st.session_state:
        st.session_state.messages = [SystemMessage(content=DEFAULT_SYSTEM_MESSAGE)]
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
    if "embedding_model" not in st.session_state:
        st.session_state.embedding_model = DEFAULT_EMBEDDING_MODEL
    if "processed_documents" not in st.session_state:
        st.session_state.processed_documents = {}
    if "document_retrievers" not in st.session_state:
        st.session_state.document_retrievers = {}
    if "document_vector_stores" not in st.session_state:
        st.session_state.document_vector_stores = {}
    if "combined_retriever" not in st.session_state:
        st.session_state.combined_retriever = None
    if "selected_document" not in st.session_state:
        st.session_state.selected_document = "All Documents"
    if "chat_mode" not in st.session_state:
        st.session_state.chat_mode = "multi"
    if "document_summaries" not in st.session_state:
        st.session_state.document_summaries = {}
    if "summary_generating" not in st.session_state:
        st.session_state.summary_generating = set()
