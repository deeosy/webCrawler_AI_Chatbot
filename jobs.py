import codetrain as ct
from codetrain import call_llm_simple
from utils import scrape_url, chunk_text, embed_texts, VectorStore
from urllib.parse import urlparse
import numpy as np


vector_store = VectorStore()
_retrieved_context = []


class URLInputJob(ct.Job):
    """Accept URLs from user and prepare for indexing."""

    def receive_order(self, manifest):
        return manifest.get("urls", [])

    def prepare_order(self, urls):
        if not urls:
            raise ValueError("No URLs provided")
        return [url.strip() for url in urls if url.strip()]

    def ship_order(self, manifest, urls, result):
        manifest["urls"] = result
        manifest["chat_mode"] = True
        return "default"


class ValidateURLJob(ct.Job):
    """Validate URL format."""

    def receive_order(self, manifest):
        return manifest.get("urls", [])

    def prepare_order(self, urls):
        valid_urls = []
        for url in urls:
            parsed = urlparse(url)
            if parsed.scheme in ("http", "https") and parsed.netloc:
                valid_urls.append(url)
            else:
                raise ValueError(f"Invalid URL: {url}")
        return valid_urls

    def ship_order(self, manifest, urls, result):
        manifest["urls"] = result
        return "default"


class ScrapeJob(ct.Job):
    """Scrape content from URLs."""

    def receive_order(self, manifest):
        return manifest.get("urls", [])

    def prepare_order(self, urls):
        all_content = {}
        for url in urls:
            content = scrape_url(url, max_pages=5)
            all_content.update(content)
        return all_content

    def ship_order(self, manifest, urls, result):
        manifest["indexed_content"] = result
        return "default"


class IndexJob(ct.Job):
    """Index scraped content into vector store."""

    def receive_order(self, manifest):
        return manifest.get("indexed_content", {})

    def prepare_order(self, content):
        global vector_store
        all_chunks = []

        for url, text in content.items():
            chunks = chunk_text(text, chunk_size=400, overlap=50)
            all_chunks.extend(chunks)

        if all_chunks:
            embeddings = embed_texts(all_chunks)
            vector_store.add(all_chunks, embeddings)

        return len(all_chunks)

    def ship_order(self, manifest, content, result):
        manifest["total_chunks"] = result
        return "default"


class ValidateContextJob(ct.Job):
    """Validate if user query is within indexed context."""

    def receive_order(self, manifest):
        return manifest.get("user_query", "")

    def prepare_order(self, query):
        return query

    def ship_order(self, manifest, query, result):
        if not vector_store.is_empty():
            query_embedding = embed_texts([query])[0]
            results = vector_store.search(query_embedding, top_k=3)

            if results:
                manifest["has_context"] = True
                return "retrieve"

        manifest["has_context"] = False
        return "decline"


class RetrieveJob(ct.Job):
    """Retrieve relevant context for user query."""

    def receive_order(self, manifest):
        return manifest.get("user_query", "")

    def prepare_order(self, query):
        global _retrieved_context
        query_embedding = embed_texts([query])[0]
        results = vector_store.search(query_embedding, top_k=5)
        _retrieved_context = results
        return results

    def ship_order(self, manifest, query, result):
        manifest["retrieved_context"] = result
        return "generate"


class GenerateAnswerJob(ct.Job):
    """Generate answer from retrieved context."""

    def receive_order(self, manifest):
        return manifest.get("user_query", "")

    def prepare_order(self, query):
        global _retrieved_context
        context = _retrieved_context
        context_text = "\n\n".join(context)

        prompt = f"""You are a helpful assistant that answers questions based ONLY on the provided context.
If the context contains relevant information, answer the question using only that information.
If the context does not contain relevant information, say so clearly.

Context:
{context_text}

Question: {query}

Answer:"""

        return call_llm_simple(prompt)

    def ship_order(self, manifest, order_data, result):
        manifest["answer"] = result
        return "chat_ready"


class DeclineJob(ct.Job):
    """Generate polite decline message for out-of-context questions."""

    def receive_order(self, manifest):
        return manifest.get("urls", [])

    def prepare_order(self, urls):
        url_list = ", ".join(urls) if urls else "the provided content"
        return url_list

    def ship_order(self, manifest, urls, result):
        manifest["context_limited"] = True
        manifest[
            "answer"
        ] = f"""I apologize, but I can only answer questions based on the content I've indexed from the URLs you provided ({result}).

Your question is outside the scope of the indexed content, so I'm unable to help with this. 

If you have questions about the content from those URLs, please feel free to ask! Otherwise, this conversation is now restricted to the indexed content."""
        return "end"
