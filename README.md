# 📄 Document RAG Assistant

> Transform any document into an interactive AI conversation using RAG (Retrieval Augmented Generation)

![Python](https://img.shields.io/badge/python-v3.11+-blue.svg)
![Streamlit](https://img.shields.io/badge/streamlit-v1.32+-red.svg)
![LangChain](https://img.shields.io/badge/langchain-latest-green.svg)
[![Live Demo](https://img.shields.io/badge/demo-online-green.svg)](https://advanced-document-rag-assistant.streamlit.app/)

## 🎯 Overview

Advanced Document RAG Assistant is a Streamlit web app that allows you to chat with your documents.
Upload PDFs, Word, Markdown, CSV, HTML, or text files, and the app will:
        * Process them into vector embeddings
        * Store them in FAISS for retrieval
        * Allow AI-powered conversations with context-aware responses
        * Provide summaries for quick insights

## 🌐 Live Demo

Try it out here: [Document RAG Assistant Live Demo](https://advanced-document-rag-assistant.streamlit.app/)

## ✨ Features

- 📁 **Multi-format Support**: PDF, TXT, DOCX, HTML, Markdown, CSV
- 🤖 **Multiple AI Models**: Choose from gemini-2.5-pro, gemini-2.5-flash, gemini-1.5-pro, etc.
- 💬 **Interactive Chat**: Natural language conversation with document content
- 🔍 **Smart Search**: Vector-based similarity search using FAISS
- 📊 **Summarization**: AI-generated summaries for quick understanding
- 📊 **Session Management**: Chat history, export functionality, and session persistence
- 🎨 **Modern UI**: Clean, responsive Streamlit interface with real-time updates
- 📈 **Progress Tracking**: Visual feedback during document processing
- 🔄 **Streaming Responses**: Real-time AI response streaming with typing indicators
- 🛡️ **Fallback System**: Automatic HuggingFace embeddings if Google quota exceeded

## 🛠️ Tech Stack

- **Frontend**: Streamlit
- **AI/ML**: Google Gemini API, LangChain
- **Vector Store**: FAISS (Facebook AI Similarity Search)
- **Embeddings**: HuggingFace sentence-transformers
- **Document Processing**: PyPDFLoader, TextLoader
- **Environment**: Python 3.11+, Docker support

## 📋 Prerequisites

- Python 3.11 or higher
- Google Gemini API Key ([Get one here](https://makersuite.google.com/app/apikey))
- Internet connection for API access

## 🚀 Quick Start

### 1. Clone the Repository

```bash
git clone https://github.com/Hemangichhaya/Advanced-Document-RAG-Assistant.git
cd Advanced-Document-RAG-Assistant
```

### 2. Install Dependencies

```bash
uv sync
```

### 3. Set Up Environment

```bash
uv venv
# Edit .env and add your Google API key
```

### 4. Run the Application

```bash
streamlit run app.py
```

### 5. Access the App

Open your browser and navigate to `http://localhost:8501`

## 🔧 Configuration

### Environment Variables

Create a `.env` file in the root directory:

```env
GOOGLE_API_KEY=your_google_gemini_api_key_here
```

Alternatively, you can enter your API key directly in the app's sidebar.

### Supported Models

- `gemini-2.5-pro` (Most capable, recommended for complex analysis)
- `gemini-2.5-flash` (Balanced performance and speed)
- `gemini-2.5-flash-lite` (Lightweight and fast)
- `gemini-2.0-flash` (Fast responses, good accuracy)
- `gemini-1.5-pro` (Reliable baseline)
- `gemini-1.5-flash` (Quick processing)

### Configurable Parameters

```python
CHUNK_SIZE = 1000          # Text chunk size for processing
CHUNK_OVERLAP = 100        # Overlap between chunks for context
RETRIEVER_K = 4           # Number of similar chunks to retrieve
EMBEDDING_MODEL = "models/gemini-embedding-exp-03-07"
```

## 📱 How to Use

1. **Enter API Key**: Add your Google Gemini API key in the sidebar
2. **Upload Document**: Click "📁 Upload your document" and select a PDF or TXT file
3. **Process Document**: Click "🚀 Process Document" to extract and index the content
4. **Start chatting in 💬 Chat tab**: Ask questions about the document content in natural language
5. **Generate summaries in 📋 Summaries tab** : Generate AI Summary of the docuemnt
5. **Export Chat**: Download your conversation history anytime using the sidebar

### Example Queries

- "What is the main topic of this document?"
- "Summarize the key findings in chapter 3"
- "What does the author say about machine learning?"
- "List all the recommendations mentioned"
- "Explain the methodology used in this research"

## ⚠️ Current Limitations

- **File Types**: Currently supports only PDF and TXT formats
- **Language**: Optimized for English documents
- **Processing Time**: Large documents (>50 pages) may take longer to process
- **API Limits**: Subject to Google Gemini API rate limits and quotas
- **Scanned PDFs**: Does not support OCR for image-based PDFs

## 🏗️ Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│  File Upload    │───▶│  Text Splitter   │───▶│   Embeddings    │
│  (PDF/TXT)      │    │  (Chunking)      │    │  (Google AI)    │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                                        │
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│  Streamlit UI   │◀───│   Chat Chain     │◀───│   FAISS Store   │
│   (Frontend)    │    │  (LangChain)     │    │ (Vector Search) │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                               │
                       ┌──────────────────┐
                       │  Gemini Models   │
                       │ (Generation AI)  │
                       └──────────────────┘
```

## 🐳 Docker Support

### Using Docker Compose (Recommended)

```bash
# Create .env file with your API key
echo "GOOGLE_API_KEY=your-api-key-here" > .env

# Start the service
docker-compose up -d

# View logs
docker-compose logs -f
```

### Using Docker directly

```bash
# Build image
docker build -t document-qa-rag-system .

# Run container
docker run -p 8501:8501 -e GOOGLE_API_KEY=your_api_key document-qa-rag-system
```

## 📁 Project Structure

```
document-rag-assistant/
│── app.py                 # Main entry point
│── config.py              # Constants & defaults
│── state.py               # Session state management
│── sidebar.py             # Sidebar UI
│── document_processing.py # Document loaders, embeddings, retrievers
│── summary.py             # Summarization logic
│── chat.py                # Chat flow and prompts
│── ui.py                  # Upload & summary UI tabs
│── utils.py               # Utility functions
├── Dockerfile              # Container setup
├── requirements.txt        # Python dependencies
├── .env.example            # Example API key file
├── .gitignore              # Git ignore rules
└── README.md               # Project documentation
```

## 📊 Performance Metrics

- **Processing Speed**: ~2-5 seconds for typical documents (10-50 pages)
- **Memory Usage**: Optimized vector storage with FAISS
- **Accuracy**: High precision with 4-chunk retrieval system
- **Container Size**: ~380MB (optimized Docker image)
- **Response Time**: Sub-second for most queries

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request. For major changes, please open an issue first to discuss what you would like to change.

### Development Setup

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Development with Docker

```bash
# Build development image
docker build -f Dockerfile.dev -t document-rag-dev .

# Run with live reload
docker run -p 8501:8501 -v $(pwd):/app document-rag-dev
```

## 📝 Future Roadmap

- [ ] OCR support for scanned PDFs
- [ ] Multi-language document support
- [ ] Agentic RAG → evolve into Agentic Retrieval-Augmented Generation, where AI agents can:
        Dynamically choose retrieval strategies (hybrid, reranking, keyword + semantic)

        Use external tools (search, calculators, APIs) alongside document context
        
        Perform multi-step reasoning instead of one-shot Q&A
        
        Autonomously decide when to retrieve, summarize, or refine queries
        
        Enable autonomous research assistants over documents

## 🐛 Known Issues

- Large PDF files (>100MB) may cause memory issues
- Some complex PDF layouts may not parse correctly
- API rate limiting may affect performance during peak usage
- Embedded images in PDFs are not processed

## 🔧 Troubleshooting

### Common Issues

**"API key not found" error:**
- Ensure your Google Gemini API key is correctly set
- Check that the key has proper permissions

**Document processing fails:**
- Ensure the file is not corrupted or password-protected

**Slow processing:**
- Try using a smaller document or different model
- Check your internet connection

**Out of memory:**
- Reduce document size or restart the application
- For Docker: increase memory limits


## 🙏 Acknowledgments

- [Streamlit](https://streamlit.io/) for the amazing web framework
- [LangChain](https://langchain.com/) for RAG implementation tools
- [Google AI](https://ai.google.dev/) for Gemini API access
- [FAISS](https://github.com/facebookresearch/faiss) for efficient vector similarity search
- [PyPDFLoader](https://python.langchain.com/docs/modules/data_connection/document_loaders/integrations/pypdf) for PDF processing

---

⭐ **Star this repository if you found it helpful!**

Built with 🖤 using Streamlit and Google Gemini AI
