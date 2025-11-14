# config.py

CHUNK_SIZE = 1000
CHUNK_OVERLAP = 100

EMBEDDING_MODEL_OPTIONS = {
    "all-MiniLM-L6-v2": "sentence-transformers/all-MiniLM-L6-v2",
    "all-mpnet-base-v2": "sentence-transformers/all-mpnet-base-v2",
    "multi-qa-MiniLM-L6-cos-v1": "sentence-transformers/multi-qa-MiniLM-L6-cos-v1",
    "paraphrase-MiniLM-L6-v2": "sentence-transformers/paraphrase-MiniLM-L6-v2"
}
DEFAULT_EMBEDDING_MODEL = "all-MiniLM-L6-v2"
RETRIEVER_K = 4

SUPPORTED_FORMATS = {
    'pdf': '📄 PDF Documents',
    'txt': '📝 Text Files',
    'docx': '📋 Word Documents',
    'html': '🌐 HTML Files',
    'htm': '🌐 HTML Files',
    'md': '📓 Markdown Files',
    'csv': '📊 CSV Files'
}

DEFAULT_SYSTEM_MESSAGE = """
You are Advanced Document RAG Assistant 📄🤖.
Your role is to help users understand and explore the content of uploaded documents.

Rules:
1. Always prioritize the document context when answering questions.
2. If the answer is not in the document(s), clearly say you don't know.
3. When multiple documents are loaded, mention which document contains the relevant information.
4. Keep responses friendly, clear, and concise.
5. For multi-document queries, synthesize across documents when appropriate.
"""
