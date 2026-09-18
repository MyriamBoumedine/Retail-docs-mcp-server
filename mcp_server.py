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
from databricks import sql as databricks_sql

# Chemin basé sur l'emplacement du script, pas sur le dossier de lancement :
# Claude Desktop lance ce script depuis un dossier différent du tien.
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DB_DIR = os.path.join(SCRIPT_DIR, "chroma_db")
COLLECTION_NAME = "retail_project_docs"
TOP_K = 4

# Connexion Databricks — lues depuis des variables d'environnement, JAMAIS en dur ici
DATABRICKS_SERVER_HOSTNAME = os.environ.get("DATABRICKS_SERVER_HOSTNAME")
DATABRICKS_HTTP_PATH = os.environ.get("DATABRICKS_HTTP_PATH")
DATABRICKS_TOKEN = os.environ.get("DATABRICKS_TOKEN")

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


CATALOG_SCHEMA = "workspace.retail_project"


@mcp.tool()
def query_gold_table(sql: str) -> str:
    """
    Exécute une requête SQL en lecture (SELECT uniquement) sur les tables
    Gold du projet Databricks retail de Myriam, pour répondre à des
    questions chiffrées (chiffre d'affaires, nombre de transactions...).

    Utilise cet outil quand la question porte sur des CHIFFRES RÉELS
    (montants, totaux, comparaisons) plutôt que sur le fonctionnement du
    pipeline (pour ça, utilise search_retail_docs à la place).

    Tables disponibles (catalogue workspace.retail_project) :
    - gold_sales_daily(day, revenue, nb_transactions)
        CA total par jour
    - gold_sales_by_store(store, region, revenue, avg_basket)
        CA par magasin/région + panier moyen
    - gold_sales_by_category(category, revenue, avg_basket)
        CA par catégorie de produit + panier moyen

    Écris toujours le nom de table complet, par exemple :
    SELECT * FROM workspace.retail_project.gold_sales_by_store LIMIT 10

    Args:
        sql: une requête SQL SELECT (lecture uniquement)

    Returns:
        Le résultat de la requête, formaté en texte, ou un message d'erreur.
    """
    if not sql.strip().lower().startswith("select"):
        return (
            "Requête refusée : seules les requêtes SELECT (lecture) sont "
            "autorisées par cet outil, par sécurité."
        )

    if not all([DATABRICKS_SERVER_HOSTNAME, DATABRICKS_HTTP_PATH, DATABRICKS_TOKEN]):
        return (
            "Connexion Databricks non configurée. Variables d'environnement "
            "requises : DATABRICKS_SERVER_HOSTNAME, DATABRICKS_HTTP_PATH, "
            "DATABRICKS_TOKEN."
        )

    try:
        with databricks_sql.connect(
            server_hostname=DATABRICKS_SERVER_HOSTNAME,
            http_path=DATABRICKS_HTTP_PATH,
            access_token=DATABRICKS_TOKEN,
        ) as connection:
            with connection.cursor() as cursor:
                cursor.execute(sql)
                columns = [desc[0] for desc in cursor.description]
                rows = cursor.fetchall()
    except Exception as e:
        return f"Erreur lors de l'exécution de la requête : {e}"

    if not rows:
        return "La requête n'a renvoyé aucune ligne."

    header = " | ".join(columns)
    separator = "-" * len(header)
    lines = [header, separator]
    for row in rows:
        lines.append(" | ".join(str(v) for v in row))

    return "\n".join(lines)


if __name__ == "__main__":
    mcp.run()
