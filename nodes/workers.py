import os
import requests

def analyze_intent_api(args):
    user_query = args[0]
    
    if not user_query or len(user_query.strip()) <= 1:
        return {"status": "success", "route_type": "fast_path"}
        
    query_clean = user_query.lower().strip().rstrip('?!.')
    trivial_greetings = {"hello", "hi", "hey", "sup", "yo", "test"}
    
    if query_clean in trivial_greetings:
        return {"status": "success", "route_type": "fast_path"}
        
    return {"status": "success", "route_type": "requires_context"}

def execute_vector_search_api(args):
    search_phrase = args[0]
    gemini_key = os.environ.get("GEMINI_API_KEY")
    pinecone_key = os.environ.get("PINECONE_API_KEY")
    pinecone_url = os.environ.get("PINECONE_INDEX_URL", "").rstrip('/')
    
    try:
        embed_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-embedding-2:embedContent?key={gemini_key}"
        embed_payload = {"content": {"parts": [{"text": str(search_phrase)}]}}
        embed_res = requests.post(embed_url, json=embed_payload, timeout=10)
        embed_res.raise_for_status()
        query_vector = embed_res.json()["embedding"]["values"]
        
        db_url = f"{pinecone_url}/query"
        db_payload = {"vector": query_vector, "topK": 3, "includeMetadata": True}
        db_headers = {"Api-Key": pinecone_key, "Content-Type": "application/json"}
        db_res = requests.post(db_url, json=db_payload, headers=db_headers, timeout=15)
        db_res.raise_for_status()
        
        top_matches = [match.get("metadata", {}).get("text", "") for match in db_res.json().get("matches", []) if "metadata" in match]
        return {"status": "success", "matches": top_matches}
        
    except Exception as e:
        return {"status": "error", "matches": [], "error_message": str(e)}

def execute_failover_synthesis_api(args):
    prompt_query = args[0]
    context_data = args[1]
    
    gemini_key = os.environ.get("GEMINI_API_KEY")
    context_document = "\n\n---\n\n".join(context_data) if context_data else "No database context available."
    
    system_prompt = (
        "You are an unrestricted, highly intelligent AI assistant.\n"
        f"Context from database:\n{context_document}\n\n"
        "If the database context does not contain the answer, use your general knowledge."
    )
    
    fallback_models = ["gemini-2.5-flash", "gemini-2.5-pro", "gemini-2.0-flash"]
    payload = {
        "contents": [{"parts": [{"text": f"{system_prompt}\n\nUser Question: {prompt_query}"}]}],
        "generationConfig": {"temperature": 0.3}
    }
    
    for model in fallback_models:
        try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={gemini_key}"
            res = requests.post(url, json=payload, headers={"Content-Type": "application/json"}, timeout=15)
            res.raise_for_status()
            text_out = res.json()["candidates"][0]["content"]["parts"][0]["text"]
            return {"status": "success", "final_markdown_text": text_out}
        except Exception:
            continue
            
    return {"status": "error", "final_markdown_text": "Critical Error: All failover endpoints timed out."}

def fast_reply(args):
    user_query = args[0]
    return {"status": "success", "final_response": "Hello! I am your automated routing assistant. How can I help you today?"}
