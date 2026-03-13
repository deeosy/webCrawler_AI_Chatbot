from hustle import create_indexing_hustle, create_chat_hustle
from jobs import vector_store
import sys


def index_urls(urls):
    """Index URLs and return the number of chunks indexed."""
    manifest = {"urls": urls}
    hustle = create_indexing_hustle()
    hustle.run(manifest)
    return manifest.get("total_chunks", 0)


def chat(query):
    """Process a chat query."""
    manifest = {"user_query": query}
    hustle = create_chat_hustle()
    hustle.run(manifest)
    return manifest.get("answer", ""), manifest.get("context_limited", False)


def main():
    print("=" * 60)
    print("Website RAG Chatbot")
    print("=" * 60)
    print("\nThis chatbot can answer questions about content from URLs you provide.")
    print("It will only answer questions within the context of the indexed content.")
    print("\n" + "=" * 60)

    while True:
        print("\n--- MENU ---")
        print("1. Add URL(s) to index")
        print("2. Ask a question")
        print("3. Exit")

        choice = input("\nEnter your choice (1-3): ").strip()

        if choice == "1":
            print("\n--- Add URL(s) ---")
            url_input = input("Enter URL(s) separated by commas: ").strip()
            if not url_input:
                print("No URLs provided.")
                continue

            urls = [u.strip() for u in url_input.split(",") if u.strip()]
            print(f"\nIndexing {len(urls)} URL(s)... This may take a while.")
            print("(Scanning up to 5 pages per URL)")

            try:
                chunks = index_urls(urls)
                print(f"\nSuccessfully indexed {chunks} chunks of content!")
            except Exception as e:
                print(f"\nError indexing URLs: {e}")
                continue

            print("\nYou can now ask questions about the indexed content.")

        elif choice == "2":
            if vector_store.is_empty():
                print("\nPlease add URL(s) first (option 1).")
                continue

            print("\n--- Ask a Question ---")
            print("(Type 'exit' to return to menu)")

            while True:
                query = input("\nYou: ").strip()
                if not query:
                    continue
                if query.lower() in ("exit", "quit"):
                    break

                answer, limited = chat(query)
                print(f"\nBot: {answer}")

                if limited:
                    print("\nConversation restricted. Returning to menu.")
                    break

        elif choice == "3":
            print("\nGoodbye!")
            break

        else:
            print("\nInvalid choice. Please enter 1-3.")


if __name__ == "__main__":
    main()
