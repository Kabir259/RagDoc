from langchain.vectorstores.chroma import Chroma
from langchain.prompts import ChatPromptTemplate
from langchain_community.llms.ollama import Ollama
from get_embedding_function import get_embedding_function

CHROMA_PATH = "chroma"
PROMPT_TEMPLATE = """
Answer the question based only on the following context:
{context}
---
Answer the question based on the above context: {question}
"""

def query_rag(query_text: str, k: int, similarity_threshold: float) -> tuple[str, list]:
    embedding_function = get_embedding_function()
    db = Chroma(persist_directory=CHROMA_PATH, embedding_function=embedding_function)
    
    # Search the DB
    results = db.similarity_search_with_score(query_text, k=k)
    
    def distance_to_similarity(distance):
        from math import exp
        # Normalize to 0-1 range
        normalized_distance = (distance - 100) / (600 - 100)  # Shift and scale to account for min distance
        # Sigmoid function: 1/(1 + e^(ax)) where a controls steepness
        return 1 / (1 + exp(0.25 * normalized_distance))

# Convert the score
    similarity_score = distance_to_similarity(results[0][1]) if results else 0.0
    
    if not results or (similarity_score < similarity_threshold):
        return f"Sorry, I didn't understand your question (Similarity: {similarity_score:.3f} < {similarity_threshold}). Do you want to connect with a live agent?", []
    else:
        context_text = "\n\n---\n\n".join([doc.page_content for doc, _score in results])
        
        prompt_template = ChatPromptTemplate.from_template(PROMPT_TEMPLATE)
        messages = prompt_template.format_messages(context=context_text, question=query_text)
        
        llm = Ollama(model="llama3.1")
        response = llm.invoke(messages)
        
        response = f"{response}\n\n*Similarity: {similarity_score:.3f}*"
        
        # Extract sources
        sources = [
            {
                "id": doc.metadata.get("id"),
                "source": doc.metadata.get("source"), 
                "page": doc.metadata.get("page")
            }
            for doc, _score in results
        ]
        
        return response, sources

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("query_text", type=str, help="The query text.")
    parser.add_argument("k", type=int, help="Number of references.")
    parser.add_argument("similarity_threshold", type=float, help="Similarity threshold.")
    args = parser.parse_args()
    print(query_rag(args.query_text, args.k, args.similarity_threshold))

if __name__ == "__main__":
    main()