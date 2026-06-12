# Triage Routing Engine

A high-availability, Retrieval-Augmented Generation (RAG) routing pipeline engineered for seamless integration with enterprise low-code workflow orchestration platforms.

This engine is built on a strict **Service-Oriented Architecture (SOA)**, breaking down complex LLM and vector database operations into isolated, parameterized micro-tasks that communicate via rigid JSON data contracts.

## Architectural Core Principles

To ensure zero-downtime execution and complete compatibility with visual DAG (Directed Acyclic Graph) engines, this pipeline enforces three core production standards:

1. **Strict JSON Data Contracts:** Every worker node accepts explicit parameter mappings and returns a standardized JSON object. No raw strings, unformatted objects, or tuples are passed across state boundaries, completely eliminating serialization crashes inside the workflow execution engine.
2. **High-Availability (HA) Fallback Cascade:** LLM APIs are inherently volatile. The synthesis node implements a try-catch failover loop. If the primary model (`gemini-2.5-flash`) returns a rate-limit, 503, or 404 error, the engine instantly cascades to alternative computing nodes (`gemini-2.5-pro` -> `gemini-2.0-flash`) within milliseconds without dropping the active user session.
3. **Stateless Execution:** Each worker node evaluates its inputs independently without relying on hidden global application states, making the micro-services highly scalable, thread-safe, and ready for containerized cloud deployments.

## Node Breakdown & Execution Flow

The core backend functions are implemented in `nodes/workers.py` and map directly to your visual workflow canvas layout:

### 1. Intent Gatekeeper (`analyze_intent_api`)
* **Purpose:** Evaluates the semantic structure of the raw incoming query. 
* **Logic:** Routes trivial greetings, basic test strings, or single-word queries directly to a low-latency fast path. This reserves expensive vector embeddings and heavy LLM compute tokens exclusively for deep contextual questions.
* **Output Contract:** Returns `{"route_type": "fast_path"}` or `{"route_type": "requires_context"}`.

### 2. Vector RAG Search (`execute_vector_search_api`)
* **Purpose:** Performs low-latency context retrieval from the vector database.
* **Logic:** Converts the raw text query into a 3072-dimensional vector using `gemini-embedding-2` via an optimized direct HTTP call, then executes a cosine-similarity search against a serverless **Pinecone** index to fetch the top 3 matching documentation context blocks.
* **Output Contract:** Returns `{"matches": ["context_str_1", "context_str_2", "context_str_3"]}`.

### 3. HA Synthesizer (`execute_failover_synthesis_api`)
* **Purpose:** Ingests retrieved data and generates the final response.
* **Logic:** Combines the user query with the extracted context blocks into a grounded system prompt. If the database match array is empty, it dynamically falls back to utilizing secure general knowledge to fulfill the request. It runs the prompt through the three-tier model fallback cascade to guarantee generation delivery.
* **Output Contract:** Returns `{"final_markdown_text": "..."}`.

### 4. Fast Reply Bypass (`fast_reply`)
* **Purpose:** Instantaneous execution block for non-technical conversation overhead.
* **Output Contract:** Returns `{"final_response": "..."}`.

<img width="2880" height="1601" alt="image" src="https://github.com/user-attachments/assets/d92aa6bf-f60b-4cd4-b61d-0bf7fd4ddf7f" />



## Quickstart & Local Deployment

### 1. Project Setup
Clone this repository to your local runtime environment and navigate to the project root directory:

```bash
git clone [https://github.com/LuminaX-alt/assisto_triage_routing_engine.git](https://github.com/LuminaX-alt/assisto_triage_routing_engine.git)
cd assisto_triage_routing_engine

<img width="2880" height="1800" alt="image" src="https://github.com/user-attachments/assets/0414b116-3920-49dd-9899-47c880cb7d96" />

