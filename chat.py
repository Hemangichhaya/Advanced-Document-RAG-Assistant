# chat.py
import streamlit as st
import json
from datetime import datetime
from config import SUPPORTED_FORMATS
from summary import generate_summary_for_document

from langchain_core.prompts import PromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, AIMessage

@st.cache_resource()
def get_chat_model():
    """Get chat model if API key is available"""
    api_key = st.session_state.get("api_key")
    model_name = st.session_state.get("model", "gemini-2.5-flash")
    
    if not api_key:
        return None
    
    return ChatGoogleGenerativeAI(model=model_name)

def display_chat_messages():
    """Display chat message history"""
    for message in st.session_state.messages[1:]:  # Skip system message
        if isinstance(message, HumanMessage):
            with st.chat_message("user"):
                st.write(message.content)
        elif isinstance(message, AIMessage):
            with st.chat_message("assistant"):
                st.write(message.content)

def process_chat_message(prompt: str, chat_model):
    """Process a chat message (used for both user input and suggested questions)"""
    st.session_state.messages.append(HumanMessage(content=prompt))
    
    # Create different prompt templates for single vs multi-document mode
    if st.session_state.chat_mode == "single":
        # Include summary context if available
        doc_name = st.session_state.selected_document
        summary_context = ""
        if doc_name in st.session_state.document_summaries:
            summary_context = f"\n\nDocument Summary:\n{st.session_state.document_summaries[doc_name]['content']}\n"
        
        prompt_template = PromptTemplate(
            template="""You are answering questions based on a specific document. Here is the relevant content from the document:

            {context}{summary_context}

            Question: {question}
            
            Instructions:
            - Answer based on the provided content from the selected document
            - Use both the document excerpts and summary (if available) to provide comprehensive answers
            - If the answer isn't in the document content provided, clearly state you don't know
            - Be specific and detailed in your response
            - Reference specific sections or parts when relevant""",
            input_variables=["context", "summary_context", "question"],
        )
    else:
        prompt_template = PromptTemplate(
            template="""You have access to content from multiple documents. Based on the following document content:

            {context}

            Question: {question}
            
            Instructions:
            - Answer based on the provided document content from ALL available sources
            - ALWAYS mention which specific document(s) contain the relevant information
            - If information comes from multiple documents, clearly indicate each source
            - If the information spans multiple documents, synthesize appropriately while citing sources
            - If the answer isn't in any of the documents, clearly state you don't know
            - When possible, compare or contrast information across different documents""",
            input_variables=["context", "question"],
        )

    with st.chat_message("user"):
        st.write(prompt)

    # Check if we have any documents
    if not st.session_state.document_retrievers:
        with st.chat_message("assistant"):
            error_msg = "❌ No documents available. Please process documents first."
            st.error(error_msg)
            st.session_state.messages.append(AIMessage(content=error_msg))
            return
            
    with st.chat_message("assistant"):
        # Show search mode
        if st.session_state.chat_mode == "single":
            selected_doc = st.session_state.selected_document
            with st.spinner(f"🔍 Searching in '{selected_doc}'..."):
                try:
                    # Search in specific document
                    retrieved_docs = get_document_specific_context(prompt, selected_doc, k=4)
                    
                    if not retrieved_docs:
                        no_context_msg = f"🤷‍♂️ I couldn't find relevant information about your question in '{selected_doc}'."
                        st.warning(no_context_msg)
                        st.session_state.messages.append(AIMessage(content=no_context_msg))
                        return
                    
                    # Format context from single document
                    context = format_single_document_results(retrieved_docs, selected_doc)
                    
                    # Add summary context if available
                    summary_context = ""
                    if selected_doc in st.session_state.document_summaries:
                        summary_context = f"\n\nDocument Summary:\n{st.session_state.document_summaries[selected_doc]['content']}\n"
                    
                except Exception as e:
                    error_msg = f"❌ Error searching '{selected_doc}': {str(e)}"
                    st.error(error_msg)
                    st.session_state.messages.append(AIMessage(content=error_msg))
                    return
        else:
            with st.spinner("🤔 Searching across all your documents..."):
                try:
                    # Show which documents are being searched
                    doc_names = list(st.session_state.processed_documents.keys())
                    st.info(f"🔍 Searching across {len(doc_names)} documents: {', '.join(doc_names)}")
                    
                    # Use multi-document search
                    retrieved_docs = multi_document_search(prompt, k_per_doc=3)
                    
                    if not retrieved_docs:
                        no_context_msg = "🤷‍♂️ I couldn't find relevant information in your documents for this question."
                        st.warning(no_context_msg)
                        st.session_state.messages.append(AIMessage(content=no_context_msg))
                        return
                    
                    # Format context from multiple documents
                    context = format_multi_document_results(retrieved_docs)
                    
                except Exception as e:
                    error_message = str(e).lower()
                    if "quota" in error_message or "limit" in error_message:
                        error_msg = "📊 API quota exceeded. Please try again later."
                    elif "timeout" in error_message:
                        error_msg = "⏱️ Request timed out. Please try again."
                    else:
                        error_msg = "❌ An error occurred. Please check your API key and try again."

                    st.error(error_msg)
                    st.session_state.messages.append(AIMessage(content=error_msg))
                    return
        
        # Generate response
        try:
            # Create prompt with context
            if st.session_state.chat_mode == "single":
                full_prompt = prompt_template.format(
                    context=context, 
                    summary_context=summary_context,
                    question=prompt
                )
            else:
                full_prompt = prompt_template.format(context=context, question=prompt)
            
            message_placeholder = st.empty()
            full_response = ""

            # Stream response
            for chunk in chat_model.stream(full_prompt):
                if chunk and hasattr(chunk, 'content') and chunk.content.strip():
                    full_response += chunk.content
                    message_placeholder.markdown(full_response + "▌")

            if full_response and full_response.strip():
                message_placeholder.markdown(full_response)
                st.session_state.messages.append(AIMessage(content=full_response))
            else:
                error_msg = "🚫 No response received. Please try a different model."
                message_placeholder.error(error_msg)
                st.session_state.messages.append(AIMessage(content=error_msg))

            st.rerun()

        except Exception as e:
            error_message = str(e).lower()
            if "quota" in error_message or "limit" in error_message:
                error_msg = "📊 API quota exceeded. Please try again later."
            elif "timeout" in error_message:
                error_msg = "⏱️ Request timed out. Please try again."
            else:
                error_msg = "❌ An error occurred. Please check your API key and try again."

            st.error(error_msg)
            st.session_state.messages.append(AIMessage(content=error_msg))

def get_document_specific_context(query: str, doc_name: str, k: int = 4):
    """Get context from a specific document"""
    if doc_name not in st.session_state.document_retrievers:
        return []
    
    try:
        retriever = st.session_state.document_retrievers[doc_name]
        return retriever.invoke(query)[:k]
    except Exception as e:
        st.error(f"Error searching {doc_name}: {str(e)}")
        return []

def multi_document_search(query: str, k_per_doc: int = 3):
    """Search across all documents and return results with clear source attribution"""
    all_results = []
    
    for doc_name, retriever in st.session_state.document_retrievers.items():
        try:
            # Search this specific document
            doc_results = retriever.invoke(query)
            
            # Add document name to results and limit results per document
            for result in doc_results[:k_per_doc]:
                result.metadata['source_file'] = doc_name  # Ensure source is set
                all_results.append(result)
                
        except Exception as e:
            st.error(f"Error searching {doc_name}: {str(e)}")
            continue
    
    # Sort by relevance (you could implement more sophisticated ranking here)
    return all_results

def format_single_document_results(retrieved_docs, doc_name):
    """Format search results from a single document"""
    if not retrieved_docs:
        return ""
    
    context_parts = [f"=== DOCUMENT: {doc_name} ==="]
    for i, doc in enumerate(retrieved_docs, 1):
        context_parts.append(f"Excerpt {i}: {doc.page_content}")
    
    return "\n".join(context_parts)

def format_multi_document_results(retrieved_docs):
    """Format search results from multiple documents with clear source attribution"""
    if not retrieved_docs:
        return ""
    
    # Group results by document
    docs_by_source = {}
    for doc in retrieved_docs:
        source = doc.metadata.get('source_file', 'Unknown Source')
        if source not in docs_by_source:
            docs_by_source[source] = []
        docs_by_source[source].append(doc.page_content)
    
    # Format with clear document separation
    context_parts = []
    for source, contents in docs_by_source.items():
        context_parts.append(f"=== DOCUMENT: {source} ===")
        for i, content in enumerate(contents, 1):
            context_parts.append(f"Excerpt {i}: {content}")
        context_parts.append("")  # Empty line between documents
    
    return "\n".join(context_parts)

def export_chat_history():
    """Export chat history as JSON or Markdown"""
    if len(st.session_state.messages) <= 1:  # Only system message
        st.warning("No chat history to export!")
        return None, None
    
    # Prepare chat data
    chat_data = {
        'export_date': datetime.now().isoformat(),
        'selected_document': st.session_state.selected_document,
        'chat_mode': st.session_state.chat_mode,
        'model_used': st.session_state.get('model', 'gemini-2.5-flash'),
        'total_messages': len(st.session_state.messages) - 1,  # Exclude system message
        'messages': []
    }
    
    # Convert messages to exportable format
    for msg in st.session_state.messages[1:]:  # Skip system message
        if isinstance(msg, HumanMessage):
            chat_data['messages'].append({
                'type': 'user',
                'content': msg.content,
                'timestamp': datetime.now().isoformat()  # You could store actual timestamps
            })
        elif isinstance(msg, AIMessage):
            chat_data['messages'].append({
                'type': 'assistant', 
                'content': msg.content,
                'timestamp': datetime.now().isoformat()
            })
    
    # Create JSON export
    json_content = json.dumps(chat_data, indent=2, ensure_ascii=False)
    
    # Create Markdown export
    md_lines = [
        f"# Chat Export - {chat_data['export_date'][:10]}",
        f"",
        f"**Document:** {chat_data['selected_document']}",
        f"**Mode:** {chat_data['chat_mode']}",
        f"**Model:** {chat_data['model_used']}",
        f"**Messages:** {chat_data['total_messages']}",
        f"",
        "---",
        ""
    ]
    
    for msg in chat_data['messages']:
        if msg['type'] == 'user':
            md_lines.extend([
                f"## User",
                f"{msg['content']}",
                ""
            ])
        else:
            md_lines.extend([
                f"## Assistant", 
                f"{msg['content']}",
                ""
            ])
    
    md_content = "\n".join(md_lines)
    
    return json_content, md_content

def chat_tab():
    """Chat interface tab with document selection and summary integration"""
    st.header("💬 Chat with Your Documents")
    
    # Check if documents are processed
    if not st.session_state.processed_documents:
        st.warning("⚠️ No documents processed yet! Please upload and process documents in the 'Upload Documents' tab first.")
        return
    
    # NEW: Document selection section
    st.subheader("📋 Select Document(s) to Chat With")
    
    # Create document options
    doc_options = ["All Documents"] + list(st.session_state.processed_documents.keys())
    
    # Document selection with additional info
    col1, col2 = st.columns([2, 3])
    
    with col1:
        selected_doc = st.selectbox(
            "Choose Document",
            options=doc_options,
            index=doc_options.index(st.session_state.selected_document) if st.session_state.selected_document in doc_options else 0,
            help="Select a specific document or 'All Documents' to search across all uploaded documents"
        )
        
        # Update session state when selection changes
        if selected_doc != st.session_state.selected_document:
            st.session_state.selected_document = selected_doc
            st.session_state.chat_mode = "multi" if selected_doc == "All Documents" else "single"
    
    with col2:
        # Show selection info with summary status
        if selected_doc == "All Documents":
            summary_count = len(st.session_state.document_summaries)
            st.info(f"🌐 **Multi-Document Mode**: Searching across all {len(st.session_state.processed_documents)} document(s) | {summary_count} summaries available")
        else:
            doc_info = st.session_state.processed_documents[selected_doc]
            format_icon = SUPPORTED_FORMATS.get(doc_info['format'], '📄')
            has_summary = selected_doc in st.session_state.document_summaries
            summary_status = "📋 Summary available" if has_summary else "📝 No summary yet"
            st.success(f"{format_icon} **Single Document Mode**: {selected_doc} ({doc_info['chunks']} chunks) | {summary_status}")
    
    # Quick summary access for single document mode
    if (st.session_state.chat_mode == "single" and 
        st.session_state.selected_document in st.session_state.document_summaries):
        
        with st.expander(f"📋 Quick Summary: {st.session_state.selected_document}", expanded=False):
            summary_data = st.session_state.document_summaries[st.session_state.selected_document]
            st.markdown(summary_data['content'])
            st.caption(f"Generated: {datetime.fromisoformat(summary_data['generated_at']).strftime('%Y-%m-%d %H:%M')}")
    
    # Suggested questions based on document type and summaries
    if st.session_state.chat_mode == "single" and st.session_state.selected_document != "All Documents":
        st.subheader("💡 Suggested Questions")
        doc_format = st.session_state.processed_documents[st.session_state.selected_document]['format']
        
        # Format-specific suggestions
        if doc_format == 'pdf':
            suggestions = [
                "What are the main topics covered in this document?",
                "Summarize the key findings or conclusions",
                "What data or statistics are mentioned?",
                "Are there any recommendations or action items?"
            ]
        elif doc_format == 'csv':
            suggestions = [
                "What columns are in this dataset?", 
                "What are the main trends in the data?",
                "Show me some statistics about the data",
                "What patterns can you identify?"
            ]
        else:
            suggestions = [
                "What is this document about?",
                "What are the key points?",
                "Explain the main concepts",
                "What should I know from this document?"
            ]
        
        # Display suggestions as clickable buttons
        cols = st.columns(2)
        for i, suggestion in enumerate(suggestions[:4]):
            with cols[i % 2]:
                if st.button(f"💭 {suggestion}", key=f"suggestion_{i}", use_container_width=True):
                    # Auto-fill the chat input (simulate user input)
                    st.session_state.suggested_question = suggestion
                    st.rerun()
    
    st.divider()
    
    # Show current document status
    with st.expander("📚 Document Library", expanded=False):
        for doc_name, doc_info in st.session_state.processed_documents.items():
            format_icon = SUPPORTED_FORMATS.get(doc_info['format'], '📄')
            is_selected = doc_name == st.session_state.selected_document
            has_summary = doc_name in st.session_state.document_summaries
            
            status_icon = "🎯" if is_selected else "📄"
            summary_icon = "📋" if has_summary else "📝"
            
            col1, col2 = st.columns([3, 1])
            with col1:
                st.write(f"{status_icon} {format_icon} **{doc_name}** - {doc_info['chunks']} chunks ({doc_info['format'].upper()})")
            with col2:
                if has_summary:
                    if st.button(summary_icon, key=f"view_summary_{doc_name}", help=f"View summary of {doc_name}"):
                        st.session_state.selected_summary_in_chat = doc_name
                else:
                    if st.button(summary_icon, key=f"gen_summary_{doc_name}", help=f"Generate summary for {doc_name}"):
                        generate_summary_for_document(doc_name)
    
    # Display inline summary if requested
    if hasattr(st.session_state, 'selected_summary_in_chat') and st.session_state.selected_summary_in_chat:
        doc_name = st.session_state.selected_summary_in_chat
        if doc_name in st.session_state.document_summaries:
            with st.container():
                col1, col2 = st.columns([4, 1])
                with col1:
                    st.subheader(f"📋 Summary: {doc_name}")
                with col2:
                    if st.button("❌", key="close_inline_summary"):
                        delattr(st.session_state, 'selected_summary_in_chat')
                        st.rerun()
                
                summary_data = st.session_state.document_summaries[doc_name]
                with st.container():
                    st.markdown(summary_data['content'])
                    st.caption(f"Generated: {datetime.fromisoformat(summary_data['generated_at']).strftime('%Y-%m-%d %H:%M')}")
                st.divider()
    
    # Chat interface
    chat_model = get_chat_model() if st.session_state.get("api_key") else None
    
    if not chat_model:
        st.warning("⚠️ Please enter your Google Gemini API key in the sidebar to start chatting.")
        return
    
    # Display chat messages
    display_chat_messages()
    
    # Handle suggested question
    suggested_question = st.session_state.get('suggested_question', '')
    if suggested_question:
        # Clear the suggested question and process it
        delattr(st.session_state, 'suggested_question')
        process_chat_message(suggested_question, chat_model)
    else:
        # Chat input
        handle_user_input(chat_model)

    # Export chat functionality
    if len(st.session_state.messages) > 1:  # Has chat history
        st.divider()
        st.subheader("📤 Export Chat")
        
        col1, col2, col3 = st.columns([1, 1, 2])
        
        with col1:
            if st.button("📄 Export as JSON", use_container_width=True):
                json_content, _ = export_chat_history()
                if json_content:
                    st.download_button(
                        label="⬇️ Download JSON",
                        data=json_content,
                        file_name=f"chat_export_{datetime.now().strftime('%Y%m%d_%H%M')}.json",
                        mime="application/json",
                        use_container_width=True
                    )
        
        with col2:
            if st.button("📝 Export as Markdown", use_container_width=True):
                _, md_content = export_chat_history()
                if md_content:
                    st.download_button(
                        label="⬇️ Download MD",
                        data=md_content,
                        file_name=f"chat_export_{datetime.now().strftime('%Y%m%d_%H%M')}.md",
                        mime="text/markdown",
                        use_container_width=True
                    )
        
        with col3:
            st.info(f"💬 {len(st.session_state.messages)-1} messages ready to export")


def handle_user_input(chat_model):
    """Handle user input in chat with document selection support"""
    if prompt := st.chat_input("Ask a question about your documents..."):
        if not prompt.strip():
            st.warning("Please type a message before sending!")
            return
        
        process_chat_message(prompt, chat_model)