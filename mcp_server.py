"""
Serveur MCP — expose le retrieval RAG comme un outil que Claude (Desktop ou
Code) peut appeler pendant une conversation.

C'est la même logique de retrieval que dans query.py (étape 5 du RAG) :
chunking et embeddings déjà faits par ingest.py, stockés dans chroma_db/.
Ici, on ne fait QUE le retrieval — pas de génération, pas de clé API :
c'est Claude (ton abonnement, via Desktop/Code) qui génère la réponse
finale à partir de ce que cet outil lui renvoie.

Lancement (généralement fait automatiquement par Claude Desktop/Code,
pas à la main) :
    python mcp_server.py
"""

import os
import chromadb
from mcp.server.fastmcp import FastMCP

# Chemin basé sur l'emplacement du script, pas sur le dossier de lancement :
# Claude Desktop lance ce script depuis un dossier différent du tien.
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DB_DIR = os.path.join(SCRIPT_DIR, "chroma_db")
COLLECTION_NAME = "retail_project_docs"
TOP_K = 4

# Le nom "retail-docs" apparaîtra dans Claude Desktop/Code comme identifiant du serveur
mcp = FastMCP("retail-docs")


@mcp.tool()
def search_retail_docs(question: str) -> str:
    """
    Recherche dans la documentation du projet Databricks retail de Myriam
    (pipeline Bronze/Silver/Gold, gouvernance, CI/CD) les passages les plus
    pertinents pour répondre à une question.

    Utilise cet outil pour toute question sur le fonctionnement, les choix
    techniques ou l'état d'avancement de ce projet spécifique.

    Args:
        question: la question posée par l'utilisateur, en langage naturel

    Returns:
        Les extraits de documentation les plus pertinents, avec leur source.
    """
    client = chromadb.PersistentClient(path=DB_DIR)
    try:
        collection = client.get_collection(COLLECTION_NAME)
    except Exception:
        return (
            "Aucun index trouvé. L'utilisateur doit d'abord lancer "
            "`python ingest.py` pour construire la base vectorielle."
        )

    results = collection.query(query_texts=[question], n_results=TOP_K)
    docs = results["documents"][0]
    metas = results["metadatas"][0]

    if not docs:
        return "Aucun passage pertinent trouvé dans la documentation."

    blocks = [
        f"[Source: {meta['source']}]\n{doc}"
        for doc, meta in zip(docs, metas)
    ]
    return "\n\n---\n\n".join(blocks)


if __name__ == "__main__":
    mcp.run()
