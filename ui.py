# ui.py
import streamlit as st
from datetime import datetime
import time
# from chat import get_chat_model
from summary import create_summary_download
import asyncio
from config import SUPPORTED_FORMATS
from document_processing import process_documents, remove_document
from summary import generate_summary_for_document, display_document_summary, generate_all_summaries

# def document_upload_tab():
#     st.header("📁 Upload")
#     uploaded = st.file_uploader("Upload docs", type=list(SUPPORTED_FORMATS.keys()), accept_multiple_files=True)
#     if uploaded and st.button("Process"):
#         process_documents(uploaded)
#     if st.session_state.get("processed_documents"):
#         for doc in st.session_state.processed_documents:
#             st.write(f"✅ {doc}")
#             if st.button(f"📝 Summary {doc}"): generate_summary_for_document(doc)
#             if st.button(f"❌ Remove {doc}"): remove_document(doc)


def document_upload_tab():
    """Document upload and management tab"""
    st.header("📁 Document Upload & Management")
    
    # Show supported formats
    st.info("**Supported formats:** " + " | ".join(SUPPORTED_FORMATS.values()))
    
    # File uploader
    uploaded_files = st.file_uploader(
        "Choose your documents",
        type=list(SUPPORTED_FORMATS.keys()),
        help="Upload multiple files at once. All supported formats can be mixed.",
        accept_multiple_files=True,
        key="document_uploader"
    )
    
    # Display uploaded files
    if uploaded_files:
        st.subheader("📋 Selected Files")
        
        for i, file in enumerate(uploaded_files):
            format_icon = SUPPORTED_FORMATS.get(file.name.split('.')[-1].lower(), '📄')
            is_processed = file.name in st.session_state.processed_documents
            
            status = "✅ Processed" if is_processed else "⏳ Ready"
            
            col1, col2, col3 = st.columns([3, 2, 2])
            with col1:
                st.write(f"{format_icon} **{file.name}**")
            with col2:
                st.write(f"📊 {file.size/(1024*1024):.1f}MB")
            with col3:
                if is_processed:
                    st.success(status)
                else:
                    st.info(status)
    
        # Process button
        if st.button("🚀 Process All Documents", type="primary", use_container_width=True):
            process_documents(uploaded_files)
    
    # Display currently processed documents
    if st.session_state.processed_documents:
        st.divider()
        st.subheader("📚 Processed Documents")
        
        for doc_name, doc_info in st.session_state.processed_documents.items():
            with st.container():
                col1, col2, col3, col4, col5, col6 = st.columns([3, 1, 1, 1, 1, 1])
                
                with col1:
                    format_icon = SUPPORTED_FORMATS.get(doc_info['format'], '📄')
                    st.write(f"{format_icon} **{doc_name}**")
                
                with col2:
                    st.write(f"📊 {doc_info['chunks']} chunks")
                
                with col3:
                    st.write(f"📁 {doc_info['format'].upper()}")
                
                with col4:
                    st.write(f"💾 {doc_info['size']/(1024*1024):.1f}MB")
                
                with col5:
                    # Summary button
                    has_summary = doc_name in st.session_state.document_summaries
                    is_generating = doc_name in st.session_state.summary_generating
                    
                    if is_generating:
                        st.button("⏳", key=f"summary_{doc_name}", disabled=True, help="Generating summary...")
                    elif has_summary:
                        if st.button("📋", key=f"summary_{doc_name}", help="View summary"):
                            st.session_state.selected_summary = doc_name
                    else:
                        if st.button("📝", key=f"summary_{doc_name}", help="Generate summary"):
                            generate_summary_for_document(doc_name)
                
                with col6:
                    if st.button("🗑️", key=f"delete_{doc_name}", help=f"Remove {doc_name}"):
                        remove_document(doc_name)
                        st.rerun()
    
    else:
        st.info("👆 Upload documents above to get started")
    
    # Display selected summary
    if hasattr(st.session_state, 'selected_summary') and st.session_state.selected_summary:
        display_document_summary(st.session_state.selected_summary)


def summary_tab():
    """Dedicated tab for document summaries"""
    st.header("📋 Document Summaries")
    
    if not st.session_state.processed_documents:
        st.warning("⚠️ No documents processed yet! Please upload and process documents first.")
        return
    
    if not st.session_state.get("api_key"):
        st.warning("⚠️ Please enter your Google Gemini API key in the sidebar to generate summaries.")
        return
    
    # Summary overview
    total_docs = len(st.session_state.processed_documents)
    total_summaries = len(st.session_state.document_summaries)
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Documents", total_docs)
    with col2:
        st.metric("Summaries Generated", total_summaries)
    with col3:
        completion = (total_summaries / total_docs * 100) if total_docs > 0 else 0
        st.metric("Completion", f"{completion:.0f}%")
    
    st.divider()
    
    # Bulk actions
    if total_summaries < total_docs:
        st.subheader("🚀 Bulk Actions")
        unsummarized_docs = [doc for doc in st.session_state.processed_documents.keys() 
                           if doc not in st.session_state.document_summaries]
        
        col1, col2 = st.columns(2)
        with col1:
            st.info(f"📝 {len(unsummarized_docs)} documents without summaries")
        with col2:
            if st.button("📝 Generate All Missing Summaries", type="primary"):
                generate_all_summaries(unsummarized_docs)
        
        st.divider()
    
    # Individual document summaries
    st.subheader("📚 Individual Document Summaries")
    
    for doc_name, doc_info in st.session_state.processed_documents.items():
        format_icon = SUPPORTED_FORMATS.get(doc_info['format'], '📄')
        has_summary = doc_name in st.session_state.document_summaries
        is_generating = doc_name in st.session_state.summary_generating
        
        with st.container():
            # Document header
            col1, col2, col3 = st.columns([3, 1, 1])
            with col1:
                st.subheader(f"{format_icon} {doc_name}")
                st.caption(f"{doc_info['chunks']} chunks • {doc_info['size']/(1024*1024):.1f}MB • {doc_info['format'].upper()}")
            with col2:
                if is_generating:
                    st.button("⏳ Generating...", disabled=True)
                elif has_summary:
                    if st.button("🔄 Regenerate", key=f"regen_{doc_name}"):
                        generate_summary_for_document(doc_name)
                else:
                    if st.button("📝 Generate Summary", key=f"gen_{doc_name}", type="primary"):
                        generate_summary_for_document(doc_name)
            with col3:
                if has_summary:
                    if st.button("💬 Chat About", key=f"chat_{doc_name}"):
                        st.session_state.selected_document = doc_name
                        st.session_state.chat_mode = "single"
            
            # Display summary if available
            if has_summary:
                summary_data = st.session_state.document_summaries[doc_name]
                
                with st.expander("📋 View Summary", expanded=True):
                    st.markdown(summary_data['content'])
                    
                    col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
                    with col1:
                        st.caption(f"Generated: {datetime.fromisoformat(summary_data['generated_at']).strftime('%Y-%m-%d %H:%M')} | Model: {summary_data['model']}")
                    with col2:
                        if st.button("📋 Copy", key=f"copy_{doc_name}"):
                            st.code(summary_data['content'], language="markdown")
                    with col3:
                        # Download summary button
                        summary_download = create_summary_download(doc_name, summary_data)
                        st.download_button(
                            label="⬇️ Download",
                            data=summary_download,
                            file_name=f"summary_{doc_name}_{datetime.now().strftime('%Y%m%d')}.md",
                            mime="text/markdown",
                            key=f"download_{doc_name}"
                        )
                    with col4:
                        if st.button("🗑️ Delete Summary", key=f"del_sum_{doc_name}"):
                            del st.session_state.document_summaries[doc_name]
                            st.rerun()
            
            st.divider()