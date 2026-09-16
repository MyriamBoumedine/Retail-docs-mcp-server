# Retail Docs MCP Server

Serveur MCP (Model Context Protocol) exposant un système RAG comme outil
utilisable par Claude Desktop ou Claude Code — un agent Claude peut interroger
la documentation d'un projet Databricks retail (pipeline Bronze/Silver/Gold)
et répondre à des questions en citant les sources.

## Ce que ça fait

- Indexe des documents markdown dans une base vectorielle (Chroma), après
  découpage en chunks et calcul d'embeddings
- Expose un outil `search_retail_docs` via le protocole MCP
- Claude (Desktop/Code) décide seul quand appeler cet outil pendant une
  conversation, puis rédige sa réponse à partir des extraits retournés

Aucune clé API requise : la génération de la réponse passe par l'abonnement
Claude Desktop/Code de l'utilisateur, pas par un appel API séparé.

## Architecture

```
Utilisateur (Claude Desktop)
   │ pose une question
   ▼
Claude ─── décide d'appeler l'outil ───▶ mcp_server.py
   │                                         │ retrieval (chromadb)
   │◀──────── extraits pertinents ───────────┘
   ▼
Réponse générée, sourcée
```

## Installation

```bash
pip install -r requirements.txt --break-system-packages
```

## Utilisation

**1. Indexer la documentation** (à refaire à chaque changement des fichiers dans `data/`) :

```bash
python ingest.py
```

**2. Connecter le serveur à Claude Desktop**

Ajoute ceci dans le fichier de config de Claude Desktop (`claude_desktop_config.json` — emplacement variable selon l'installation, voir Paramètres > Développeur > "Modifier la configuration" dans Claude Desktop) :

```json
{
  "mcpServers": {
    "retail-docs": {
      "command": "/chemin/vers/python",
      "args": ["/chemin/absolu/vers/mcp_server.py"]
    }
  }
}
```

Redémarre complètement Claude Desktop, puis vérifie dans Paramètres > Développeur que `retail-docs` apparaît avec le statut "En cours".

**3. Poser une question**

Dans une conversation Claude Desktop : *"Comment fonctionne la couche Bronze de mon projet retail ?"*

## Structure

```
├── ingest.py          # Chunking + embeddings + indexation (à lancer une fois)
├── mcp_server.py       # Serveur MCP : expose le retrieval comme outil
├── requirements.txt
└── data/               # Documents source (markdown)
```

## Stack

- [Model Context Protocol](https://modelcontextprotocol.io/) (SDK Python, `mcp`)
- [Chroma](https://www.trychroma.com/) — base vectorielle locale, embeddings ONNX intégrés
- Claude Desktop / Claude Code comme client

## Pistes d'évolution

- Ajouter un outil `query_gold_table` pour interroger directement les tables
  Gold Databricks via SQL (agent multi-outils : RAG + accès données)
- Jeu de questions/réponses pour évaluer la qualité du retrieval
