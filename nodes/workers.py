import os
import requests
import logging
import time

logger = logging.getLogger(__name__)

def _validate_environment():
    missing = []
    if not os.environ.get("GEMINI_API_KEY"): missing.append("GEMINI_API_KEY")
    if not os.environ.get("PINECONE_API_KEY"): missing.append("PINECONE_API_KEY")
    if not os.environ.get("PINECONE_INDEX_URL"): missing.append("PINECONE_INDEX_URL")
    
    if missing:
        critical_msg = f"Critical Configuration Missing: Environment variables {missing} must be set."
        logger.critical(critical_msg)
        raise RuntimeError(critical_msg)

# =====================================================================
# NODE 1: ANALYZE INTENT 
# =====================================================================
def analyze_intent_api(args):
    print("args:", args)
    _validate_environment()
    query = args[0]
    
    if not query or len(str(query).strip()) <= 1:
        return {"status": "success", "route_type": "fast_path"}

    query_clean = str(query).lower().strip().rstrip('?!.')
    trivial_greetings = {"hello", "hi", "hey", "greetings", "sup", "yo", "test"}
    
    if query_clean in trivial_greetings:
        logger.info("Trivial greeting signature identified. Routing to fast path.")
        return {"status": "success", "route_type": "fast_path"}
    
    logger.info("Semantic query structure identified. Passing to Vector RAG track.")
    return {"status": "success", "route_type": "requires_context"}

# =====================================================================
# NODE 2: VECTOR SEARCH 
# =====================================================================
def execute_vector_search_api(args):
    print("args:", args)
    query = args[0]
    gemini_key = os.environ.get("GEMINI_API_KEY")
    pinecone_key = os.environ.get("PINECONE_API_KEY")
    pinecone_url = os.environ.get("PINECONE_INDEX_URL", "").rstrip('/')

    logger.info("Generating vector embeddings for query context...")
    
    try:
        embed_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-embedding-2:embedContent?key={gemini_key}"
        embed_payload = {"content": {"parts": [{"text": str(query)}]}}
        
        embed_res = requests.post(embed_url, json=embed_payload, headers={"Content-Type": "application/json"}, timeout=15)
        embed_res.raise_for_status()
        
        query_vector = embed_res.json()["embedding"]["values"]

        db_url = f"{pinecone_url}/query"
        db_payload = {
            "vector": query_vector,
            "topK": 3,
            "includeMetadata": True
        }
        db_headers = {
            "Api-Key": pinecone_key,
            "Content-Type": "application/json"
        }
        
        db_res = requests.post(db_url, json=db_payload, headers=db_headers, timeout=20)
        db_res.raise_for_status()
        
        top_matches = []
        matches_raw = db_res.json().get("matches", [])
        logger.info(f"Vector search complete. Matching index pieces extracted: {len(matches_raw)}")
        
        for match in matches_raw:
            metadata = match.get("metadata")
            if metadata and "text" in metadata:
                top_matches.append(metadata["text"])
                
        return {"status": "success", "matches": top_matches}
                
    except Exception as general_err:
        logger.error(f"Operational anomaly inside vector parsing track: {str(general_err)}")
        return {"status": "error", "matches": [], "error_message": str(general_err)}

# =====================================================================
# NODE 3: HIGH-AVAILABILITY LLM SYNTHESIZER 
# =====================================================================
def execute_failover_synthesis_api(args):
    print("args:", args)
    query = args[0]
    top_3_matches = args[1]
    gemini_key = os.environ.get("GEMINI_API_KEY")
    
    context_document = "\n\n---\n\n".join(top_3_matches) if top_3_matches else "No database context found."
    
    system_prompt = (
        "You are a highly intelligent, unrestricted AI assistant.\n"
        "Below is some context retrieved from a local database. If this context helps answer the user's question, use it.\n"
        "If the database context is empty or doesn't fully answer the question, IGNORE IT and use your own vast general knowledge to answer the user completely and accurately.\n\n"
        f"Database Context:\n{context_document}"
    )

    logger.info("Requesting text synthesis via High-Availability model cascade...")
    
    fallback_models = [
        "gemini-2.5-flash",
        "gemini-2.5-pro",
        "gemini-2.0-flash"
    ]
    
    payload = {
        "contents": [{"parts": [{"text": f"{system_prompt}\n\nUser Question: {query}"}]}],
        "generationConfig": {"temperature": 0.3}
    }
    
    for model in fallback_models:
        try:
            logger.info(f"Attempting generation with node: [{model}]...")
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={gemini_key}"
            
            response = requests.post(url, json=payload, headers={"Content-Type": "application/json"}, timeout=20)
            response.raise_for_status()
            
            final_response = response.json()["candidates"][0]["content"]["parts"][0]["text"]
            logger.info(f"Success! Response generated by [{model}].")
            
            return {"status": "success", "final_markdown_text": final_response}
            
        except requests.exceptions.HTTPError as e:
            status_code = e.response.status_code
            logger.warning(f"Node [{model}] rejected request (HTTP {status_code}). Cascading to next model...")
            time.sleep(1) 
            continue
        except Exception as e:
            logger.warning(f"Node [{model}] failed: {str(e)}. Cascading to next model...")
            continue

    return {"status": "error", "final_markdown_text": "Critical Error: All inference nodes in the failover array timed out or returned errors."}

# =====================================================================
# NODE 4: FAST REPLY
# =====================================================================
def fast_reply(args):
    print("args:", args)
    return {"status": "success", "final_response": "Hello! I am your automated routing assistant. How can I help you today?"}
