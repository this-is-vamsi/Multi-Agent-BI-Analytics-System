from pathlib import Path
import os

os.environ.setdefault("USE_TF", "0")
os.environ.setdefault("TF_CPP_MIN_LOG_LEVEL", "3")

from langchain_chroma import Chroma
from langchain_community.document_loaders import Docx2txtLoader, PyPDFLoader, TextLoader
from langchain_openai import OpenAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter

from app.core.config import get_settings


class RAGService:
    # RAG service owns document ingestion and retrieval.
    # It gives agents business memory without hardcoding everything into the prompt.
    def __init__(self) -> None:
        self.settings = get_settings()

    def _embeddings(self) -> OpenAIEmbeddings | None:
        # If no API key is configured, skip RAG safely so local deterministic testing still runs.
        if not self.settings.openai_api_key:
            return None
        return OpenAIEmbeddings(
            model=self.settings.openai_embedding_model,
            api_key=self.settings.openai_api_key,
        )

    def ingest_file(self, path: str, collection_name: str = "client_context") -> int:
        # Load the document, split it into searchable chunks, and persist it in Chroma.
        embeddings = self._embeddings()
        if embeddings is None:
            return 0

        file_path = Path(path)
        suffix = file_path.suffix.lower()
        if suffix == ".pdf":
            docs = PyPDFLoader(str(file_path)).load()
        elif suffix == ".docx":
            docs = Docx2txtLoader(str(file_path)).load()
        else:
            docs = TextLoader(str(file_path), encoding="utf-8").load()

        splitter = RecursiveCharacterTextSplitter(chunk_size=1200, chunk_overlap=180)
        chunks = splitter.split_documents(docs)
        vectorstore = Chroma(
            collection_name=collection_name,
            embedding_function=embeddings,
            persist_directory=str(self.settings.rag_dir),
        )
        vectorstore.add_documents(chunks)
        return len(chunks)

    def retrieve(self, query: str, collection_name: str = "client_context", k: int = 5) -> list[str]:
        # Retrieve only the most relevant chunks for the user's current business request.
        embeddings = self._embeddings()
        if embeddings is None:
            return []

        try:
            vectorstore = Chroma(
                collection_name=collection_name,
                embedding_function=embeddings,
                persist_directory=str(self.settings.rag_dir),
            )
            docs = vectorstore.similarity_search(query, k=k)
            return [doc.page_content for doc in docs]
        except Exception:
            return []
