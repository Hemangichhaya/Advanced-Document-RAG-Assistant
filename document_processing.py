# document_processing.py
import os, tempfile, gc, streamlit as st
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.document_loaders import (
    TextLoader, PyPDFLoader, UnstructuredWordDocumentLoader,
    UnstructuredHTMLLoader, UnstructuredMarkdownLoader, CSVLoader
)
from config import CHUNK_SIZE, CHUNK_OVERLAP, RETRIEVER_K, EMBEDDING_MODEL_OPTIONS, SUPPORTED_FORMATS
from datetime import datetime
import time

def get_document_loader(file_path, file_name):
    ext = file_name.lower().split('.')[-1]
    if ext == "pdf": return PyPDFLoader(file_path, extract_images=False)
    if ext == "txt": return TextLoader(file_path, encoding="utf-8")
    if ext == "docx": return UnstructuredWordDocumentLoader(file_path)
    if ext in ["html","htm"]: return UnstructuredHTMLLoader(file_path)
    if ext == "md": return UnstructuredMarkdownLoader(file_path)
    if ext == "csv": return CSVLoader(file_path)
    st.error(f"Unsupported format: {ext}")
    return None

@st.cache_resource()
def get_free_embeddings(model_name):
    return HuggingFaceEmbeddings(
        model_name=EMBEDDING_MODEL_OPTIONS[model_name],
        model_kwargs={"device": "cpu"},
        encode_kwargs={"normalize_embeddings": True}
    )

# def process_single_document(uploaded_file, embeddings):
#     with tempfile.NamedTemporaryFile(delete=False, suffix=f".{uploaded_file.name.split('.')[-1]}") as tmp:
#         tmp.write(uploaded_file.getvalue())
#         path = tmp.name
#     loader = get_document_loader(path, uploaded_file.name)
#     docs = loader.load()
#     for d in docs:
#         d.metadata["source_file"] = uploaded_file.name
#     splitter = RecursiveCharacterTextSplitter(chunk_size=CHUNK_SIZE, chunk_overlap=CHUNK_OVERLAP)
#     chunks = splitter.split_documents(docs)
#     vs = FAISS.from_documents(chunks, embeddings)
#     retriever = vs.as_retriever(search_type="similarity", search_kwargs={"k": RETRIEVER_K})
#     os.unlink(path)
#     return retriever, vs, len(chunks)

def process_single_document(uploaded_file, embeddings, progress_callback=None):
    """Process a single document with enhanced error handling"""
    try:
        with tempfile.NamedTemporaryFile(
            delete=False, suffix=f".{uploaded_file.name.split('.')[-1]}"
        ) as tmp_file:
            tmp_file.write(uploaded_file.getvalue())
            tmp_file_path = tmp_file.name

        if progress_callback:
            progress_callback(f"Loading {uploaded_file.name}...")

        loader = get_document_loader(tmp_file_path, uploaded_file.name)
        if not loader:
            return None, None, 0
        
        # Load documents with error handling for complex PDFs
        try:
            documents = loader.load()
        except Exception as e:
            if uploaded_file.name.lower().endswith('.pdf'):
                st.error(f"❌ PDF parsing failed for {uploaded_file.name}. This might be due to complex layout, scanned content, or corrupted file.")
                st.info("💡 Try: 1) Converting to text format, 2) Using OCR software, 3) Simplifying the PDF")
                return None, None, 0
            else:
                raise e
        
        # Check if documents were loaded successfully
        if not documents:
            st.error(f"❌ No content extracted from {uploaded_file.name}")
            return None, None, 0
        
        # Add source metadata
        for doc in documents:
            doc.metadata['source_file'] = uploaded_file.name
            doc.metadata['file_format'] = uploaded_file.name.split('.')[-1].lower()
            doc.metadata['file_size'] = uploaded_file.size

        if progress_callback:
            progress_callback(f"Splitting {uploaded_file.name} into chunks...")

        splitter = RecursiveCharacterTextSplitter(
            chunk_size=CHUNK_SIZE,
            chunk_overlap=CHUNK_OVERLAP,
        )
        chunks = splitter.split_documents(documents)

        if progress_callback:
            progress_callback(f"Creating embeddings for {uploaded_file.name} ({len(chunks)} chunks)...")

        # Process embeddings in batches for large documents
        batch_size = 50 if len(chunks) > 100 else len(chunks)
        
        if len(chunks) > batch_size:
            st.info(f"📊 Processing {len(chunks)} chunks in batches to optimize memory usage...")
            
            # Create vector store in batches
            vector_store = None
            for i in range(0, len(chunks), batch_size):
                batch_chunks = chunks[i:i + batch_size]
                
                if vector_store is None:
                    vector_store = FAISS.from_documents(batch_chunks, embeddings)
                else:
                    batch_vs = FAISS.from_documents(batch_chunks, embeddings)
                    vector_store.merge_from(batch_vs)
                
                # Force garbage collection between batches
                gc.collect()
                
                if progress_callback:
                    progress_callback(f"Processed {min(i + batch_size, len(chunks))}/{len(chunks)} chunks...")
        else:
            vector_store = FAISS.from_documents(chunks, embeddings)
        
        retriever = vector_store.as_retriever(
            search_type="similarity", 
            search_kwargs={"k": RETRIEVER_K}
        )

        # Clean up temporary file
        os.unlink(tmp_file_path)
        
        return retriever, vector_store, len(chunks)

    except Exception as e:
        st.error(f"Error processing {uploaded_file.name}: {str(e)}")
        # Clean up on error
        if 'tmp_file_path' in locals():
            try:
                os.unlink(tmp_file_path)
            except:
                pass
        gc.collect()
        return None, None, 0

# def process_documents(uploaded_files):
#     embeddings = get_free_embeddings(st.session_state.embedding_model)
#     for f in uploaded_files:
#         if f.name not in st.session_state.processed_documents:
#             retriever, vs, count = process_single_document(f, embeddings)
#             st.session_state.processed_documents[f.name] = {
#                 "format": f.name.split(".")[-1], "chunks": count, "size": f.size,
#                 "processed_at": datetime.now().isoformat()
#             }
#             st.session_state.document_retrievers[f.name] = retriever
#             st.session_state.document_vector_stores[f.name] = vs
#     st.success("✅ Documents processed!")
#     st.rerun()

# def remove_document(doc_name):
#     for store in ["processed_documents","document_retrievers","document_vector_stores","document_summaries"]:
#         if doc_name in st.session_state.get(store, {}):
#             del st.session_state[store][doc_name]
#     gc.collect()
#     st.success(f"✅ Removed {doc_name}")

def process_documents(uploaded_files):
    """Process uploaded documents"""
    new_files = [f for f in uploaded_files if f.name not in st.session_state.processed_documents]
    
    if not new_files:
        st.info("ℹ️ All uploaded documents are already processed!")
        return
    
    with st.spinner(f"Processing {len(new_files)} document(s)..."):
        progress_bar = st.progress(0)
        status_text = st.empty()

        try:
            embeddings = get_free_embeddings(st.session_state.embedding_model)
            total_files = len(new_files)
            processed_count = 0
            
            for i, uploaded_file in enumerate(new_files):
                def progress_callback(message):
                    status_text.text(f"📄 Step {i+1}/{total_files}: {message}")
                    progress_bar.progress((i + 0.5) / total_files)
                
                retriever, vector_store, chunk_count = process_single_document(
                    uploaded_file, embeddings, progress_callback
                )
                
                if retriever and vector_store:
                    # Store document info
                    st.session_state.processed_documents[uploaded_file.name] = {
                        'format': uploaded_file.name.split('.')[-1].lower(),
                        'chunks': chunk_count,
                        'size': uploaded_file.size,
                        'processed_at': datetime.now().isoformat()
                    }
                    # Store both retriever and vector store separately
                    st.session_state.document_retrievers[uploaded_file.name] = retriever
                    st.session_state.document_vector_stores[uploaded_file.name] = vector_store
                    processed_count += 1
                
                progress_bar.progress((i + 1) / total_files)
                
                # Memory management between files
                if i < len(new_files) - 1:  # Not the last file
                    gc.collect()
            
            progress_bar.empty()
            status_text.empty()

            if processed_count > 0:
                st.success(f"✅ {processed_count} document(s) processed successfully! Switch to the Chat tab to start asking questions.")
                st.info("💡 You can now generate summaries by clicking the 📝 button next to each document.")
                time.sleep(2)
                st.rerun()
            else:
                st.error("❌ No documents could be processed successfully.")

        except Exception as e:
            st.error(f"❌ Error processing documents: {str(e)}")
            gc.collect()  # Clean up on error    gc.collect()
            
            progress_bar.empty()
            status_text.empty()

            if processed_count > 0:
                st.success(f"✅ {processed_count} document(s) processed successfully! Switch to the Chat tab to start asking questions.")
                st.info("💡 You can now generate summaries by clicking the 📝 button next to each document.")
                time.sleep(2)
                st.rerun()
            else:
                st.error("❌ No documents could be processed successfully.")

        except Exception as e:
            st.error(f"❌ Error processing documents: {str(e)}")
            gc.collect()  # Clean up on error


def remove_document(doc_name: str):
    """Remove a specific document from the collection with cleanup"""
    if doc_name in st.session_state.processed_documents:
        del st.session_state.processed_documents[doc_name]
    if doc_name in st.session_state.document_retrievers:
        del st.session_state.document_retrievers[doc_name]
    if doc_name in st.session_state.document_vector_stores:
        del st.session_state.document_vector_stores[doc_name]
    if doc_name in st.session_state.document_summaries:
        del st.session_state.document_summaries[doc_name]
    
    # Reset selected document if the removed document was selected
    if st.session_state.selected_document == doc_name:
        st.session_state.selected_document = "All Documents"
        st.session_state.chat_mode = "multi"
    
    # Clean up summary view if showing this document
    if hasattr(st.session_state, 'selected_summary') and st.session_state.selected_summary == doc_name:
        delattr(st.session_state, 'selected_summary')
    
    # Force garbage collection
    gc.collect()
    st.success(f"✅ {doc_name} removed successfully!")