# App "Medallion" — suivi de projets, chat IA & quiz de révision

## Statut : premier prototype publié (2026-09-15)
Artifact : https://claude.ai/artifact/Jy3diaukZ41nSMsGm1mQZ5

## Organisation retenue
- **Projets** — fiche par projet (titre, tags, statut, résumé de compréhension éditable, journal de notes horodatées). Pré-rempli avec le projet Databricks retail réel de Myriam.
- **Tâches** — liste de tâches avec minuteur individuel (Démarrer / Pause / Fait / Réouvrir), rattachables à un projet ou en général.
- **Chat IA** — conversation contextualisée par projet (ou mode général), s'appuyant sur les résumés/notes comme contexte.
- **Quiz IA** — génère une question ouverte à partir de l'ensemble des projets, évalue la réponse de Myriam (vrai/partiel/faux) avec explication, garde un historique et des stats.

## Technique
Page HTML autoportante publiée via l'outil Artifact (pas de backend séparé) : capacité `db` pour la persistance (projets/tâches/chats/quiz stockés côté artifact, synchronisés entre sessions) et capacité `sample` pour les appels IA (chat + génération/correction des questions de quiz).

## Décisions encore ouvertes
- Ajuster l'organisation ou le contenu si besoin après premier usage réel.
- Voir si elle veut partager l'artifact ou le garder strictement personnel.
