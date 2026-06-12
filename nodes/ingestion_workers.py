import os
import uuid
import requests
import PyPDF2

def extract_pdf_text(args):
    print("args:", args)
    file_path = args[0]
    
    try:
        text = ""
        with open(file_path, "rb") as f:
            reader = PyPDF2.PdfReader(f)
            for page in reader.pages:
                extracted = page.extract_text()
                if extracted:
                    text += extracted + "\n"
                    
        return {
            "status": "success",
            "document_text": text
        }
    except Exception as e:
        return {
            "status": "error",
            "document_text": "",
            "error_message": str(e)
        }

def chunk_text(args):
    print("args:", args)
    document_text = args[0]
    
    if not document_text:
        return {
            "status": "error",
            "text_chunks": []
        }
        
    chunk_size = 1000
    chunks = [document_text[i:i+chunk_size] for i in range(0, len(document_text), chunk_size)]
    
    return {
        "status": "success",
        "text_chunks": chunks
    }

def embed_and_upsert(args):
    print("args:", args)
    text_chunks = args[0]
    
    if not text_chunks:
        return {
            "status": "error",
            "upsert_count": 0
        }
        
    gemini_key = os.environ.get("GEMINI_API_KEY")
    pinecone_key = os.environ.get("PINECONE_API_KEY")
    pinecone_url = os.environ.get("PINECONE_INDEX_URL", "").rstrip('/')
    
    vectors = []
    
    try:
        for chunk in text_chunks:
            embed_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-embedding-2:embedContent?key={gemini_key}"
            embed_payload = {"content": {"parts": [{"text": str(chunk)}]}}
            res = requests.post(embed_url, json=embed_payload, timeout=10)
            res.raise_for_status()
            
            embedding = res.json()["embedding"]["values"]
            vector_id = str(uuid.uuid4())
            
            vectors.append({
                "id": vector_id,
                "values": embedding,
                "metadata": {"text": chunk}
            })
            
        db_url = f"{pinecone_url}/vectors/upsert"
        db_payload = {"vectors": vectors}
        db_headers = {"Api-Key": pinecone_key, "Content-Type": "application/json"}
        db_res = requests.post(db_url, json=db_payload, headers=db_headers, timeout=15)
        db_res.raise_for_status()
        
        return {
            "status": "success",
            "upsert_count": len(vectors)
        }
        
    except Exception as e:
        return {
            "status": "error",
            "upsert_count": 0,
            "error_message": str(e)
        }
