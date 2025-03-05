import os
import json
import re
import fitz  # PyMuPDF
import openai
from langchain_openai import OpenAIEmbeddings
from dotenv import load_dotenv
from django.http import JsonResponse, HttpResponse
from django.shortcuts import render
from qdrant_client import QdrantClient
from qdrant_client.models import PointStruct, Distance, VectorParams
from .forms import UploadPDFForm

# Load environment variables
load_dotenv()
QDRANT_HOST = os.getenv("QDRANT_HOST", "localhost")
QDRANT_PORT = int(os.getenv("QDRANT_PORT", 6333))
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
COLLECTION_NAME = os.getenv("QDRANT_COLLECTION", "kanun")

# Validate environment variables
if not all([QDRANT_HOST, QDRANT_PORT, OPENAI_API_KEY, COLLECTION_NAME]):
    raise EnvironmentError("Missing required environment variables.")

# Initialize LangChain embeddings
embeddings = OpenAIEmbeddings()

# Set OpenAI API key
openai.api_key = OPENAI_API_KEY

# Initialize Qdrant client
client = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)

# Verify if collection exists, else create it
collections = client.get_collections().collections
if COLLECTION_NAME not in [c.name for c in collections]:
    print(f"Creating new Qdrant collection: {COLLECTION_NAME}")
    client.create_collection(
        collection_name=COLLECTION_NAME,
        vectors_config=VectorParams(size=1536, distance=Distance.COSINE)
    )

    # Ensure collection is created
    collections = client.get_collections().collections
    if COLLECTION_NAME not in [c.name for c in collections]:
        raise RuntimeError(f"Failed to create collection {COLLECTION_NAME}")

print(f"Collection {COLLECTION_NAME} is ready.")

# PDF Processing Functions
def extract_text_from_pdf(pdf_path):
    doc = fitz.open(pdf_path)
    text = ""
    for page_num in range(len(doc)):
        page = doc.load_page(page_num)
        text += page.get_text("text")
    return text

def convert_to_json_with_subclause_indexing(text):
    json_data = {}
    part_pattern = re.compile(r"(Part-\d+)\s*(.*?)\n", re.DOTALL)
    article_pattern = re.compile(r"(\d+)\.\s*([A-Za-z0-9\s\-\:]+?):\s*(.*?)(?=\n\d+\.\s|$)", re.DOTALL)
    parts = re.findall(part_pattern, text)
    for part_number, part_title in parts:
        part_key = f"Part {part_number.split('-')[1].strip()}"
        part_data = {"title": part_title.strip(), "Articles": {}}
        part_start = text.index(part_number)
        next_part_start = text.find("Part-", part_start + len(part_number))
        part_content = text[part_start: next_part_start if next_part_start != -1 else None]
        articles = re.findall(article_pattern, part_content)
        for article_number, article_title, article_text in articles:
            article_key = f"Article {article_number.strip()}"
            part_data["Articles"][article_key] = {"title": article_title.strip(), "Text": article_text.strip()}
        json_data[part_key] = part_data
    return json_data

def process_pdf_to_json(pdf_file):
    temp_path = f"temp_{pdf_file.name}"
    with open(temp_path, "wb") as temp_file:
        for chunk in pdf_file.chunks():
            temp_file.write(chunk)
    try:
        text = extract_text_from_pdf(temp_path)
        json_output = convert_to_json_with_subclause_indexing(text)
        os.remove(temp_path)
        return json_output
    except Exception as e:
        if os.path.exists(temp_path):
            os.remove(temp_path)
        raise e

def chunk_articles_from_json(json_data):
    chunks = []
    for part_key, part_data in json_data.items():
        for article_key, article_data in part_data["Articles"].items():
            chunk_text = f"{article_data['title']}\n{article_data['Text']}"
            chunks.append({"id": f"{part_key}_{article_key}", "text": chunk_text.strip()})
    return chunks

def embed_text(text):
    return embeddings.embed_query(text)

def ingest_document_into_vector_store(json_data):
    # Verify collection again before inserting vectors
    collections = client.get_collections().collections
    if COLLECTION_NAME not in [c.name for c in collections]:
        raise RuntimeError(f"Collection {COLLECTION_NAME} does not exist. Please restart Qdrant and try again.")

    chunks = chunk_articles_from_json(json_data)
    points = []
    for chunk in chunks:
        embedding = embed_text(chunk['text'])
        points.append(PointStruct(id=len(points) + 1, vector=embedding, payload={"text": chunk['text']}))
    
    client.upsert(collection_name=COLLECTION_NAME, points=points)
    return len(points)

def upload_pdf_view(request):
    if request.method == "POST":
        form = UploadPDFForm(request.POST, request.FILES)
        if form.is_valid():
            pdf_file = request.FILES["pdf_file"]
            try:
                json_output = process_pdf_to_json(pdf_file)
                num_vectors = ingest_document_into_vector_store(json_output)
                
                # Prepare JSON for download
                response = HttpResponse(json.dumps(json_output, indent=4), content_type="application/json")
                response["Content-Disposition"] = f"attachment; filename={pdf_file.name}.json"
                
                return response
            except Exception as e:
                return JsonResponse({"error": str(e)}, status=500)
    else:
        form = UploadPDFForm()
    return render(request, "injest.html", {"form": form})
