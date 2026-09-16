"""
Ingestion des documents du projet retail dans une base vectorielle Chroma.

Étapes :
1. Lit tous les .md du dossier data/
2. Découpe chaque doc en chunks (par section ## / ### pour rester cohérent sémantiquement)
3. Stocke les chunks dans Chroma (embeddings calculés automatiquement, modèle
   ONNX léger intégré — pas besoin de PyTorch ni de clé API pour cette étape)

Usage : python ingest.py
"""

import os
import re
import chromadb

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(SCRIPT_DIR, "data")
DB_DIR = os.path.join(SCRIPT_DIR, "chroma_db")
COLLECTION_NAME = "retail_project_docs"


def chunk_markdown(text: str, source: str, min_chunk_chars: int = 200) -> list[dict]:
    """
    Découpe un markdown en chunks au niveau des titres (## ou ###).
    Fusionne les sections trop courtes avec la précédente pour éviter
    des chunks trop petits et peu informatifs.
    """
    # Découpe sur les titres de niveau 2 ou 3, en gardant le titre dans le chunk suivant
    parts = re.split(r"(?=^#{1,3} )", text, flags=re.MULTILINE)

    chunks = []
    buffer = ""
    for part in parts:
        part = part.strip()
        if not part:
            continue
        buffer = f"{buffer}\n\n{part}".strip() if len(buffer) < min_chunk_chars else part
        if len(buffer) >= min_chunk_chars:
            chunks.append(buffer)
            buffer = ""
    if buffer:
        chunks.append(buffer)

    return [
        {
            "id": f"{source}::chunk_{i}",
            "text": c,
            "source": source,
        }
        for i, c in enumerate(chunks)
    ]


def main():
    if not os.path.isdir(DATA_DIR):
        raise SystemExit(f"Dossier '{DATA_DIR}' introuvable. Mets tes .md dedans d'abord.")

    md_files = [f for f in os.listdir(DATA_DIR) if f.endswith(".md")]
    if not md_files:
        raise SystemExit(f"Aucun fichier .md trouvé dans '{DATA_DIR}'.")

    all_chunks = []
    for fname in md_files:
        path = os.path.join(DATA_DIR, fname)
        with open(path, "r", encoding="utf-8") as f:
            text = f.read()
        chunks = chunk_markdown(text, source=fname)
        all_chunks.extend(chunks)
        print(f"  {fname} -> {len(chunks)} chunks")

    print(f"\nTotal : {len(all_chunks)} chunks à indexer depuis {len(md_files)} fichier(s).")

    client = chromadb.PersistentClient(path=DB_DIR)
    # On repart d'une collection propre à chaque ingestion (simple pour un prototype)
    try:
        client.delete_collection(COLLECTION_NAME)
    except Exception:
        pass
    collection = client.create_collection(COLLECTION_NAME)

    collection.add(
        ids=[c["id"] for c in all_chunks],
        documents=[c["text"] for c in all_chunks],
        metadatas=[{"source": c["source"]} for c in all_chunks],
    )

    print(f"\n✅ Index créé dans '{DB_DIR}/' avec {collection.count()} chunks.")


if __name__ == "__main__":
    main()
