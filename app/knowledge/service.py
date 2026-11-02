import os
import io
import base64
from fastapi import Depends
from PIL import Image
from pypdf import PdfReader
from langchain_community.document_loaders import Docx2txtLoader, PyPDFLoader, TextLoader
from langchain_core.documents import Document as Chunk
from langchain_core.messages import HumanMessage
from langchain_ollama import ChatOllama
from langchain_text_splitters import RecursiveCharacterTextSplitter
from app.knowledge.repository import KnowledgeRepository

chunk_size = int(os.getenv("RAG_CHUNK_SIZE", "1000"))
chunk_overlap = int(os.getenv("RAG_CHUNK_OVERLAP", "150"))
ollama_base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
vision_model = os.getenv("OLLAMA_VISION_MODEL", "qwen2.5vl:3b")
ocr_max_side = int(os.getenv("OCR_MAX_SIDE", "1280"))

text_splitter = RecursiveCharacterTextSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap)

ocr_prompt = "Write out all the text in this image exactly as it appears, keeping headings, lists and tables. Only return the text."

class KnowledgeService():
    def __init__(self, repository: KnowledgeRepository = Depends()):
        self.repository = repository

    def load(self, file_path: str, on_page=None):
        extension = os.path.splitext(file_path)[1].lower()
        if extension == ".pdf":
            return self.load_pdf(file_path, on_page)
        if extension == ".docx":
            return Docx2txtLoader(file_path).load()
        return TextLoader(file_path, autodetect_encoding=True).load()

    def load_pdf(self, file_path: str, on_page=None):
        pages = PyPDFLoader(file_path).load()
        reader = PdfReader(file_path)
        for number, page in enumerate(pages, start=1):
            if not page.page_content.strip():
                # scanned page: it is only a picture, so read its text with the vision model
                images = reader.pages[page.metadata["page"]].images
                page.page_content = "\n".join(self.read_image(image.data) for image in images)
            # tell the caller how far we are, e.g. on_page(7, 38)
            if on_page:
                on_page(number, len(pages))
        return pages

    def read_image(self, image: bytes) -> str:
        # shrink big scans: a full-size page is too many tokens for the model and very slow on CPU
        picture = Image.open(io.BytesIO(image)).convert("RGB")
        picture.thumbnail((ocr_max_side, ocr_max_side))
        buffer = io.BytesIO()
        picture.save(buffer, format="PNG")

        model = ChatOllama(model=vision_model, base_url=ollama_base_url, num_ctx=8192, temperature=0)
        image_url = "data:image/png;base64," + base64.b64encode(buffer.getvalue()).decode()
        message = HumanMessage(content=[
            {"type": "text", "text": ocr_prompt},
            {"type": "image_url", "image_url": image_url},
        ])
        return model.invoke([message]).text

    def ingest_document(self, document, product, on_page=None):
        chunks = text_splitter.split_documents(self.load(document.file_path, on_page))

        prepared = []
        ids = []
        for chunk in chunks:
            if not chunk.page_content.strip():
                continue
            # the product label goes into the text so questions naming the product match its chunks
            text = f"Product: {product.name} (model {product.model_number})\n{chunk.page_content}"
            metadata = {"document_id": document.id, "doc_type": document.doc_type, "title": document.title, "product_id": product.id}
            # only pdf chunks have a page (Chroma metadata cannot hold None)
            if "page" in chunk.metadata:
                metadata["page"] = int(chunk.metadata["page"]) + 1
            prepared.append(Chunk(page_content=text, metadata=metadata))
            ids.append(f"{document.id}-{len(ids)}")

        if not prepared:
            raise ValueError(f"No extractable text in {document.file_name}")
        self.repository.delete_by_document(document.id)
        self.repository.add(prepared, ids)

    def remove_document(self, document_id: int):
        self.repository.delete_by_document(document_id)

    def remove_product(self, product_id: int):
        self.repository.delete_by_product(product_id)

    def search(self, query: str, k: int, doc_types: list = None, product_id: int = None):
        return self.repository.search(query, k, doc_types, product_id)
