# Assisto Triage Routing & Ingestion Engine

An enterprise-grade, high-availability Retrieval-Augmented Generation (RAG) routing engine and data ingestion pipeline designed for seamless integration with visual DAG orchestrators.

## 🏗 Architectural Standards

This repository strictly adheres to standard enterprise orchestrator constraints. All Python worker nodes are built to run agnostically within a generic function manager.

### 1. Positional Array Parameterization
To support language-agnostic workflow orchestration, explicit parameter naming (e.g., `def task(query: str)`) is deprecated. All inputs are passed sequentially from the workflow JSON into a single generic wrapper and unpacked via positional indices:

    def function_name(args):
        print("args:", args) # Mandatory framework logging
        query = args[0]
        context = args[1]
