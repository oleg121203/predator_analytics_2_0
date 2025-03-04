import os
import json
import psycopg2
import requests
from flask import Flask, request, jsonify
from langchain.embeddings import OllamaEmbeddings
from langchain.vectorstores import OpenSearch
from langchain.prompts import PromptTemplate
from langchain.chains import RetrievalQA
from langchain.document_loaders import (
    UnstructuredPDFLoader, UnstructuredImageLoader, UnstructuredWordDocumentLoader
)
from langchain.text_splitter import RecursiveCharacterTextSplitter
from redis import Redis

app = Flask(__name__)

REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
POSTGRES_HOST = os.getenv("POSTGRES_HOST", "localhost")
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
OPENSEARCH_HOSTS = os.getenv("OPENSEARCH_HOSTS", "http://localhost:9200").split(",")

redis_client = Redis(host=REDIS_HOST, port=6379, decode_responses=True)

db_conn = psycopg2.connect(
    dbname="predator_db",
    user="predator",
    password="strong_password",
    host=POSTGRES_HOST
)

embeddings = OllamaEmbeddings(model="mistral", ollama_url=OLLAMA_HOST)

vectorstore = OpenSearch(
    index_name="predator_index",
    opensearch_url=OPENSEARCH_HOSTS[0],
    http_auth=("admin", "strong_password"),
    use_ssl=False
)

RAG_PROMPT_TEMPLATE = """
Ти аналітик митних схем та фінансових махінацій. Проаналізуй наступні дані та відповідай на питання.
Дані:
{context}
Питання: {question}
Відповідь:
"""
prompt = PromptTemplate(template=RAG_PROMPT_TEMPLATE, input_variables=["context", "question"])

@app.route('/process_query', methods=['POST'])
def process_query():
    try:
        query = request.json.get("query")
        if not query:
            return jsonify({"error": "Query is required"}), 400

        cache_key = f"query_cache:{query}"
        if cached := redis_client.get(cache_key):
            return jsonify({"source": "cache", "response": json.loads(cached)})

        query_embedding = embeddings.embed_query(query)
        docs = vectorstore.similarity_search_by_vector(query_embedding, k=5)

        context = "\n".join(doc.page_content for doc in docs)
        qa_chain = RetrievalQA.from_chain_type(
            llm=embeddings.client,
            retriever=vectorstore.as_retriever(),
            return_source_documents=True,
            chain_type_kwargs={"prompt": prompt}
        )
        response = qa_chain({"query": query, "context": context})

        final_response = {"answer": response["result"], "sources": [doc.metadata for doc in docs]}
        redis_client.setex(cache_key, 3600, json.dumps(final_response))

        log_query(query, final_response["answer"])

        return jsonify({"source": "rag", "response": final_response})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/upload_document', methods=['POST'])
def upload_document():
    try:
        if 'file' not in request.files:
            return jsonify({"error": "Файл не надано"}), 400

        file = request.files['file']
        filename = file.filename.lower()

        temp_path = f"/tmp/{filename}"
        file.save(temp_path)

        if filename.endswith(".pdf"):
            loader = UnstructuredPDFLoader(temp_path)
        elif filename.endswith((".jpeg", ".jpg", ".png")):
            loader = UnstructuredImageLoader(temp_path)
        elif filename.endswith(".docx"):
            loader = UnstructuredWordDocumentLoader(temp_path)
        else:
            return jsonify({"error": "Непідтримуваний формат файлу"}), 400

        documents = loader.load()

        text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
        split_docs = text_splitter.split_documents(documents)

        for doc in split_docs:
            vectorstore.add_texts([doc.page_content], metadatas=[{"filename": filename}])

        return jsonify({"status": "ok", "message": f"Файл {filename} успішно оброблено."})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

def log_query(query, answer):
    try:
        with db_conn.cursor() as cur:
            cur.execute(
                "INSERT INTO query_log (query, response) VALUES (%s, %s)",
                (query, answer)
            )
            db_conn.commit()
    except Exception as e:
        print(f"Помилка логування: {e}")

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({"status": "ok"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001)