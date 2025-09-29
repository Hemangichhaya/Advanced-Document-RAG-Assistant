# sidebar.py
import streamlit as st
import os
from config import DEFAULT_SYSTEM_MESSAGE, EMBEDDING_MODEL_OPTIONS
from langchain_core.messages import (
    AIMessage,
    HumanMessage,
    SystemMessage,
)
import gc

def setup_sidebar():
    st.sidebar.header("🔑 Configuration")

    api_key = st.sidebar.text_input("Google Gemini API Key", type="password")
    if api_key:
        st.session_state.api_key = api_key
        os.environ["GOOGLE_API_KEY"] = api_key
        st.sidebar.success("✅ API key configured")
    else:
        st.sidebar.info("💡 Enter your API key to start")

    st.sidebar.subheader("🧠 Embedding Model")
    selected_embedding = st.sidebar.selectbox(
        "Choose Model (Free)", list(EMBEDDING_MODEL_OPTIONS.keys())
    )
    st.session_state.embedding_model = selected_embedding

    st.sidebar.subheader("🤖 Generation Model")
    selected_model = st.sidebar.selectbox(
        "Choose Gemini Model",
        ["gemini-2.5-flash", "gemini-2.5-pro", "gemini-2.0-flash", "gemini-1.5-flash", "gemini-1.5-pro"],
    )
    st.session_state.model = selected_model

    st.sidebar.divider()

    # Session Info
    st.sidebar.subheader("📊 Session Info")
    message_count = len(st.session_state.messages) - 1
    document_count = len(st.session_state.processed_documents)
    summary_count = len(st.session_state.document_summaries)
    
    col1, col2 = st.sidebar.columns(2)
    with col1:
        st.metric("Messages", message_count)
        st.metric("Summaries", summary_count)
    with col2:
        st.metric("Documents", document_count)

    if document_count > 0:
        total_chunks = sum(doc['chunks'] for doc in st.session_state.processed_documents.values())
        st.sidebar.success(f"📄 {document_count} document(s) ready ({total_chunks} chunks)")
    else:
        st.sidebar.info("📄 No documents processed yet")

    # Controls
    st.sidebar.divider()
    st.sidebar.subheader("🎛️ Controls")
    
    col1, col2 = st.sidebar.columns(2)
    with col1:
        if st.button("🗑️ Clear Chat", use_container_width=True):
            st.session_state.messages = [SystemMessage(content=DEFAULT_SYSTEM_MESSAGE)]
            st.rerun()
    
    with col2:
        if st.button("🔄 Clear All", use_container_width=True):
            clear_all_data()
            st.rerun()

    return selected_model, api_key


def clear_all_data():
    """Clear all documents and chat with memory cleanup"""
    st.session_state.processed_documents = {}
    st.session_state.document_retrievers = {}
    st.session_state.document_vector_stores = {}
    st.session_state.document_summaries = {}
    st.session_state.summary_generating = set()
    st.session_state.combined_retriever = None
    if "retriever" in st.session_state:
        del st.session_state["retriever"]
    st.session_state.messages = [SystemMessage(content=DEFAULT_SYSTEM_MESSAGE)]
    st.session_state.selected_document = "All Documents"
    st.session_state.chat_mode = "multi"
    
    # Force garbage collection
    gc.collect()
    st.success("🔄 All data cleared and memory freed!")

