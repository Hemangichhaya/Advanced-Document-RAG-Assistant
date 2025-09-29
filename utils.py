# utils.py
import streamlit as st, gc
from config import DEFAULT_SYSTEM_MESSAGE
from langchain_core.messages import SystemMessage

def clear_all_data():
    st.session_state.processed_documents = {}
    st.session_state.document_retrievers = {}
    st.session_state.document_vector_stores = {}
    st.session_state.document_summaries = {}
    st.session_state.summary_generating = set()
    st.session_state.messages = [SystemMessage(content=DEFAULT_SYSTEM_MESSAGE)]
    gc.collect()
    st.success("🔄 Cleared all data")
