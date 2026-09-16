# Récap projet Databricks — pipeline retail (Bronze/Silver/Gold)

## Contexte
Myriam (Ouidou) monte en compétence sur Databricks pour un projet client. Niveau
intermédiaire SQL/Python. Environnement : **Databricks Free Edition** (serverless
uniquement, Unity Catalog activé par défaut, pas de cluster classique à créer).

Catalogue/schéma utilisés : `workspace.retail_project`
Volume (landing zone) : `workspace.retail_project.raw_data`

## Statut : toutes les étapes principales sont terminées

1. **Workspace créé** — Databricks Free Edition, compute serverless par défaut
   ("Default Interactive Compute" / "Default Automated Compute", pas de bouton
   "Create" à chercher).

2. **Génération des données de test** (`01_generate_data.py`) — 8000 transactions
   retail synthétiques (magasins Paris/Lyon/Marseille/Toulouse/Lille, catégories
   Électronique/Épicerie/Vêtements/Maison/Sport), avec anomalies volontaires
   (quantités négatives, prix/clients manquants) pour travailler le nettoyage.
   Écrit directement dans le Volume `raw_data` (pas de dbutils.fs.cp, écriture
   Python standard car les Volumes UC sont exposés comme un chemin de fichier).

3. **Couche Bronze** (`02_bronze.py`) — table `bronze_transactions`, ingestion
   brute (tout en string) + métadonnées techniques (`_ingested_at`,
   `_source_file` via `_metadata.file_path` — `input_file_name()` n'est PAS
   supporté sous Unity Catalog).

4. **Couche Silver** (`03_silver.py`) — table `silver_transactions` : typage,
   rejet des quantités <= 0 et prix manquants, `customer_id` NULL toléré
   (rempli à -1), dédoublonnage sur `transaction_id`, colonne dérivée
   `total_amount`.

5. **Couche Gold** (`04_gold.py`) — 3 tables : `gold_sales_daily` (CA par jour),
   `gold_sales_by_store` (CA par magasin/région + panier moyen),
   `gold_sales_by_category` (CA par catégorie + panier moyen).

6. **Orchestration** — Job Databricks `retail_project_pipeline` (Jobs &
   Pipelines), 3 tâches enchaînées avec dépendances : bronze → silver → gold.
   Testé avec succès via "Run now". Le notebook de génération de données reste
   volontairement hors du job (simule un système source externe).

7. **Gouvernance Unity Catalog** (`05_governance.py`) :
   - Lineage : consultable dans Catalog Explorer → table → onglet Lineage.
     Attention, la vue par défaut n'affiche que la lignée à un niveau (ex :
     gold_sales_by_category ne montre que silver_transactions) — pour voir la
     chaîne complète jusqu'à bronze, cliquer sur "See lineage graph" ou aller
     directement sur la page Lineage de silver_transactions.
   - Permissions : syntaxe GRANT/REVOKE/SHOW GRANTS vue et testée (SHOW GRANTS
     exécuté avec succès, le reste en commentaire faute d'autres
     utilisateurs/groupes sur l'essai solo).
   - Row-Level Security : fonction `region_filter` créée et appliquée en ROW
     FILTER sur `gold_sales_by_store`, à visée pédagogique (comparaison directe
     avec la RLS Power BI/DAX que Myriam prépare aussi pour un entretien — voir
     fichier mémoire /areas/entretien-powerbi.md).

8. **Connexion Power BI** (en cours) :
   - Connection details récupérés depuis Compute → SQL warehouses → Serverless
     Starter Warehouse → Connection details (server hostname + HTTP path).
   - Token d'accès personnel généré (scope "BI Tools" / API scope `sql`).
   - Connexion réussie depuis Power BI Desktop via le connecteur Databricks,
     authentification par **Jeton d'accès personnel** (PAS OAuth — l'onglet
     OAuth demande une connexion interactive par navigateur, source de
     confusion rencontrée en cours de route).
   - Les 3 tables Gold sélectionnées dans le Navigator, chargement en cours.

## Prochaine étape (reprise ici)
Une fois les 3 tables Gold chargées dans Power BI : construire les premières
visualisations — courbe du CA par jour (gold_sales_daily), barres par magasin
(gold_sales_by_store), barres/secteurs par catégorie (gold_sales_by_category),
et une carte avec le CA total en DAX (`SUM(gold_sales_daily[revenue])`).

Piste optionnelle mentionnée mais pas encore traitée : configurer un rôle RLS
directement dans Power BI sur ces mêmes tables, pour comparer concrètement
avec l'implémentation Databricks (bon pont avec sa préparation d'entretien
Power BI/DAX).

## Fichiers livrés (notebooks Databricks, format source .py importable)
01_generate_data.py, 02_bronze.py, 03_silver.py, 04_gold.py, 05_governance.py
— tous envoyés à Myriam au fil de la conversation, à réimporter dans son
workspace Databricks si besoin de les reconsulter (elle les a déjà tous
importés et exécutés avec succès à ce stade).
