# Assisto Triage Engine

Parameterized micro-task orchestration pipeline for Assisto integration. 
Features High-Availability LLM failover and 3072-dimensional vector RAG search.

### Architecture Overview
* **Node 1:** Intent routing
* **Node 2:** Pinecone Vector Search
* **Node 3:** Gemini High-Availability Synthesizer (2.5 & 2.0 fallback loop)
* **Node 4:** Fast Reply bypass
