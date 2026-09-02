# Security Log Project
Audit et Qualification des Données

## Contexte du Projet
Ce projet s'inscrit dans le module de Gestion et Suivi de Projet. L'objectif est de réaliser un audit de qualité, un nettoyage et une normalisation des données historiques transmises par les équipes IT afin de déterminer leur exploitabilité pour la conception d'un système de classification et de priorisation des événements de sécurité.

## 1. Structure du Dépôt

```text
security-log-project/
├── data/
│   ├── raw/          # Fichiers sources d'origine (immuables)
│   └── processed/    # Données nettoyées, normalisées et journaux d'audit
├── docs/             # Documentation des règles de gestion et dictionnaires
├── notebooks/        # Notebooks d'exploration (EDA) et de nettoyage
├── src/              # Scripts de transformation Python
├── tests/            # Tests unitaires sur les règles de qualité
└── README.md         # Documentation principale du projet
````

## 2. Inventaire et Description des Sources

Les données fournies sont entièrement synthétiques, livrées sans contrôle qualité préalable et accompagnées de documentations partielles issues d'outils hétérogènes.

![inventaire](./notebooks/inventaire.png)

## 3. Évaluation de la Qualité des Données (Data Quality)

L'audit des sources a été réalisé selon les 6 dimensions fondamentales de la qualité des données :

* Completeness (Complétude) : Taux de champs vide massif sur analyst_decision (comportement nominal validé par l'IT) et trous ponctuels sur les attributs descriptifs des actifs et des logs.  
* Consistency (Cohérence) : Divergences de casse (LOGIN vs login), espaces et variations dans les désignations de systèmes d'exploitation.  
* Validity (Validité) : Présence des timestamps hétérogènes (mélange d'ISO 8601 et de formats locaux) et d'adresses IP mal formées.  
* Uniqueness (Unicité) : Détection de doublons exacts (lignes 100% identiques) et de doublons sur les clés primaires (device_id, user_id).  
* Accuracy (Exactitude) : Enregistrements des "orphaned users" détectés lors des croisements entre les logs opérationnels et les référentiels (users.csv / assets.csv), révélant de potentiels cas de Shadow IT.  
* Timeliness (Actualité) : Désynchronisation potentielle des référentiels RH/IT face aux connexions observées sur le terrain


## 4. Règles de Nettoyage et Normalisation

* Traçabilité des suppressions : Aucun enregistrement ne fait l'objet d'une suppression silencieuse. Les doublons stricts et les anomalies de clés primaires sont isolés et consignés dans un journal d'audit dédié (data/processed/audit_deleted_rows.csv).  
* Gestion des champs invalides : Les adresses IP mal formées ne sont pas supprimées mais isolées via un indicateur booléen d'audit (is_valid_ip) et exportées dans data/processed/invalid_ips.csv pour investigation de sécurité.
* Normalisation temporelle : Conversion systématique de tous les horodatages au format unifié UTC (datetime avec fuseau horaire). 
* Standardisation textuelle : Harmonisation de la casse et suppression des espaces superflus pour fiabiliser les futures jointures. 

## 5. Mesure d'Impact sur le Projet

* Backlog : Ajout de tâches transverses de nettoyage de données et de mise en place de scripts de contrôle d'intégrité référentielle avant toute phase de modélisation.
* Planning : Extension de la phase de cadrage et de préparation des données pour absorber la complexité des retraitements et de la documentation d'audit.
* Risques : Maîtrise du risque de faux positifs et de perte de signaux faibles grâce à l'implémentation de tables d'anomalies au lieu de suppressions pures et simples.