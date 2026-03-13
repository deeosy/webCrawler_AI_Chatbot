# Design Doc: Website RAG Chatbot

## Requirements

Build a chatbot that:
1. Accepts one or more URLs from the user
2. Scrapes and indexes all pages from those URLs
3. Answers user queries strictly from the indexed content
4. Politely declines questions outside the URL context and restricts further questions

## Hustle Design

### Pattern: RAG (Retrieval Augmented Generation)

### Flow:
```mermaid
flowchart TD
    start[Start] --> url_input[URLInputJob]
    url_input --> validate_url[ValidateURLJob]
    validate_url --> scrape[ScrapeJob]
    scrape --> index[IndexJob]
    index --> chat[ChatLoop]
    
    chat --> user_query{User Query?}
    user_query --> validate_context[ValidateContextJob]
    validate_context -->|"in context"| retrieve[RetrieveJob]
    validate_context -->|"out of context"| decline[DeclineJob]
    retrieve --> generate[GenerateAnswerJob]
    generate --> chat
    
    decline --> end[End]
```

## Utilities

1. **Web Scraper** (`utils/scraper.py`)
   - Uses: `requests`, `beautifulsoup4`
   - Purpose: Fetch and parse HTML from URLs
   - Also handles crawling internal links

2. **Embedder** (`utils/embedder.py`)
   - Uses: `sentence-transformers`
   - Purpose: Generate embeddings for text chunks

3. **Vector Store** (`utils/vectorstore.py`)
   - Uses: In-memory dictionary (simple) or `numpy`
   - Purpose: Store and search embeddings

4. **LLM Caller** (`utils/call_llm.py`)
   - Uses: `codetrain.call_llm_simple`
   - Purpose: Generate answers from context

## Manifest Design

```python
manifest = {
    "urls": [],                    # List of URLs to index
    "indexed_content": {},         # URL -> list of text chunks
    "embeddings": [],              # List of (chunk, embedding) tuples
    "chat_mode": False,           # Whether we're in chat mode
    "context_limited": False,     # If user asked out-of-context question
    "user_query": "",             # Current user query
    "retrieved_context": [],      # Retrieved relevant chunks
    "answer": "",                  # Generated answer
    "error": None                  # Error messages
}
```

## Job Design

1. **URLInputJob**
   - receive_order: Read user input for URLs
   - prepare_order: Parse and validate URL format
   - ship_order: Store URLs in manifest, set chat_mode=True

2. **ValidateURLJob**
   - receive_order: Read URLs from manifest
   - prepare_order: Validate URL format
   - ship_order: Store validated URLs or error

3. **ScrapeJob**
   - receive_order: Read URLs from manifest
   - prepare_order: Fetch HTML and extract text
   - ship_order: Store indexed_content in manifest

4. **IndexJob**
   - receive_order: Read indexed_content
   - prepare_order: Chunk text and generate embeddings
   - ship_order: Store embeddings in manifest

5. **ValidateContextJob**
   - receive_order: Read user_query and embeddings
   - prepare_order: Search for relevant context
   - ship_order: Set context_limited=True if no relevant content found

6. **RetrieveJob**
   - receive_order: Read user_query and embeddings
   - prepare_order: Find most relevant chunks
   - ship_order: Store retrieved_context

7. **GenerateAnswerJob**
   - receive_order: Read retrieved_context and user_query
   - prepare_order: Call LLM with context
   - ship_order: Store answer in manifest

8. **DeclineJob**
   - receive_order: Read manifest
   - prepare_order: Generate polite refusal message
   - ship_store: Set context_limited=True, store refusal message
