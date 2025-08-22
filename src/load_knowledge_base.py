import yaml
from agno.embedder.openai import OpenAIEmbedder
from agno.knowledge.json import JSONKnowledgeBase
from agno.vectordb.qdrant import Qdrant
from agno.vectordb.search import SearchType
from dotenv import load_dotenv
load_dotenv()

# Load configuration from YAML file
with open("config.yaml", "r") as f:
    config = yaml.safe_load(f)

qdrant_config = config.get("qdrant", {})

# Create a knowledge base from the SEO_KnowledgeBase directory
knowledge_base = JSONKnowledgeBase(
    path=qdrant_config.get("path"),
    vector_db=Qdrant(
        collection=qdrant_config.get("collection_name"),
        url=qdrant_config.get("url"),
        api_key=qdrant_config.get("api_key"),
        embedder=OpenAIEmbedder(id="text-embedding-3-small"),
        search_type=SearchType.hybrid,
    )
)

if __name__ == "__main__":
    # Load the knowledge base
    knowledge_base.load(recreate=True)
    print("Knowledge base loaded successfully.")