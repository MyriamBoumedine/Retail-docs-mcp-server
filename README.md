# Retail Docs MCP Server

Serveur MCP (Model Context Protocol) exposant un système RAG comme outil
utilisable par Claude Desktop ou Claude Code — un agent Claude peut interroger
la documentation d'un projet Databricks retail (pipeline Bronze/Silver/Gold)
et répondre à des questions en citant les sources. Une Skill complète le
projet en donnant à Claude la méthode précise pour bien utiliser cet outil.

## Ce que ça fait

- Indexe des documents markdown dans une base vectorielle (Chroma), après
  découpage en chunks et calcul d'embeddings
- Expose deux outils via le protocole MCP :
  - `search_retail_docs` — RAG sur la documentation du projet
  - `query_gold_table` — requêtes SQL en lecture (SELECT uniquement) sur les
    tables Gold Databricks réelles (`gold_sales_daily`, `gold_sales_by_store`,
    `gold_sales_by_category`)
- Claude (Desktop/Code) décide seul quand appeler cet outil pendant une
  conversation, puis rédige sa réponse à partir des extraits retournés
- Une **Skill** (`skills/retail-project-assistant/`) donne à Claude la
  méthode à suivre pour bien utiliser cet outil : toujours citer la source,
  ne jamais inventer, distinguer clairement passé/présent dans les réponses

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
      "args": ["/chemin/absolu/vers/mcp_server.py"],
      "env": {
        "DATABRICKS_SERVER_HOSTNAME": "xxx.cloud.databricks.com",
        "DATABRICKS_HTTP_PATH": "/sql/1.0/warehouses/xxx",
        "DATABRICKS_TOKEN": "xxx"
      }
    }
  }
}
```

⚠️ **Sécurité — important** : les 3 variables `DATABRICKS_*` (dont le token
d'accès personnel) ne doivent **jamais** être écrites dans `mcp_server.py`
ni dans aucun fichier versionné sur GitHub — uniquement dans ce fichier de
config, qui reste local à ta machine. Le bloc `"env"` ci-dessus permet à
Claude Desktop de les transmettre au script sans qu'elles apparaissent dans
le code. Si `query_gold_table` n'est pas nécessaire (tu veux juste le RAG),
omets simplement le bloc `"env"` — l'outil renverra un message clair
indiquant que la connexion n'est pas configurée, sans planter.

Redémarre complètement Claude Desktop, puis vérifie dans Paramètres > Développeur que `retail-docs` apparaît avec le statut "En cours".

**3. (Optionnel) Ajouter la Skill**

Dans Claude Desktop : Paramètres → Compétences → ajouter une nouvelle Skill,
en collant le contenu de `skills/retail-project-assistant/SKILL.md` (ou en
important le dossier, selon l'interface). Nécessite l'exécution de code
activée sur le compte (Pro/Max/Team/Enterprise).

Une fois ajoutée, aucune action supplémentaire : Claude l'active seul quand
une question correspond, exactement comme pour l'outil MCP.

**4. Poser une question**

Dans une conversation Claude Desktop : *"Comment fonctionne la couche Bronze de mon projet retail ?"* (RAG) ou *"Quel est le chiffre d'affaires total par magasin ?"* (SQL direct).

## Structure

```
├── ingest.py          # Chunking + embeddings + indexation (à lancer une fois)
├── mcp_server.py       # Serveur MCP : expose search_retail_docs (RAG) et query_gold_table (SQL)
├── requirements.txt
├── data/               # Documents source (markdown)
└── skills/
    └── retail-project-assistant/
        └── SKILL.md    # Méthode d'utilisation de l'outil (citer, ne pas inventer...)
```

## Stack

- [Model Context Protocol](https://modelcontextprotocol.io/) (SDK Python, `mcp`)
- [Chroma](https://www.trychroma.com/) — base vectorielle locale, embeddings ONNX intégrés
- [Claude Skills](https://support.claude.com/fr/articles/12512198) — instructions packagées pour une méthode cohérente
- [databricks-sql-connector](https://pypi.org/project/databricks-sql-connector/) — connexion SQL directe aux tables Gold
- Claude Desktop / Claude Code comme client

## Pistes d'évolution

- Jeu de questions/réponses pour évaluer la qualité du retrieval
- Améliorer le chunking (découper aussi sur les listes numérotées, pas
  seulement les titres)
