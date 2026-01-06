# Ingestion Pipeline

This document explains how documents are ingested into the vector store, from API call to searchable chunks.

## Overview

The ingestion pipeline transforms raw markdown documents into vectorized chunks that can be semantically searched.

```mermaid
flowchart LR
    A[POST /documents/ingest] --> B[IngestionPipeline]
    B --> C[DocumentLoader]
    C --> D[DocumentChunker]
    D --> E[VectorStore]
    E --> F[Searchable Index]
    
    style A fill:#4a90d9,stroke:#2d5a8a,color:#fff
    style F fill:#90EE90,stroke:#2d5a2d,color:#1a1a1a
```

---

## Complete Flow

```mermaid
flowchart TD
    subgraph API["API Layer"]
        A[POST /documents/ingest]
    end

    subgraph Pipeline["IngestionPipeline"]
        B[Initialize Pipeline]
        C[DocumentLoader.load_all]
        D[DocumentChunker.chunk_document]
    end

    subgraph Loader["DocumentLoader"]
        E[Scan knowledge_base/]
        F[Read .md files]
        G[Extract metadata]
        H[Create Document objects]
    end

    subgraph Chunker["DocumentChunker"]
        I[Get chunk config by doc_type]
        J[Split into paragraphs]
        K[Count tokens per paragraph]
        L{Paragraph > chunk_size?}
        M[Split by sentences]
        N[Merge into chunks]
        O[Add overlap]
        P[Create Chunk objects]
    end

    subgraph Store["VectorStore"]
        Q[Generate embeddings]
        R[Store in FAISS/Pinecone]
        S[Save index to disk]
    end

    A --> B
    B --> C
    C --> E --> F --> G --> H
    H --> D
    D --> I --> J --> K --> L
    L -->|Yes| M --> N
    L -->|No| N
    N --> O --> P
    P --> Q --> R --> S

    style A fill:#4a90d9,stroke:#2d5a8a,color:#fff
    style S fill:#90EE90,stroke:#2d5a2d,color:#1a1a1a
```
