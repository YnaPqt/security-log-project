# Security Log Project
Audit et Qualification des Données

## 1. Contexte du Projet
Ce projet s'inscrit dans le module de Gestion et Suivi de Projet. L'objectif est de réaliser un audit de qualité, un nettoyage et une normalisation des données historiques transmises par les équipes IT afin de déterminer leur exploitabilité pour la conception d'un système de classification et de priorisation des événements de sécurité.

## 2. Structure du Dépôt (Arborescence Git)

`security-log-project/
`├── data/
`│   ├── raw/          # Fichiers sources d'origine (immuables)
`│   └── processed/    # Données nettoyées, normalisées et journaux d'audit
`├── docs/             # Documentation des règles de gestion et dictionnaires
`├── notebooks/        # Notebooks d'exploration (EDA) et de nettoyage
`├── src/              # Scripts de transformation Python
`├── tests/            # Tests unitaires sur les règles de qualité
`└── README.md         # Documentation principale du projet