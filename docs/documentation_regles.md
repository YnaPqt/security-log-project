# Documentation des Règles de Transformation et de Nettoyage

**Projet :** Security Log Project (TP 3 — Réception et Qualification des Données)

**Objectif :** Formaliser l'ensemble des règles de traitement, de nettoyage, de normalisation et de traçabilité appliquées aux sources de données brutes avant la phase de modélisation.

---

## 1. La Règle d'Or en Cybersécurité

> *« Une ligne supprimée sans justification équivaut à perdre une information précieuse : l'anomalie que l'on efface est parfois précisément le signal d'attaque qu'il fallait détecter. »*

Afin de respecter scrupuleusement ce principe fondamental, **aucune suppression silencieuse n'est autorisée**. Toutes les données écartées, dupliquées ou invalides sont systématiquement isolées, documentées et exportées dans des tables d'audit stockées dans le dossier `data/processed/`.

---

## 2. Règles par Source et par Dimension de Qualité

### A. Gestion des Doublons (*Uniqueness*)

* **Doublons stricts (Lignes 100% identiques) :** Suppression des lignes rigoureusement identiques dans l'ensemble des fichiers (`authentication_logs.csv`, `edr_alerts.csv`, `assets.csv`, `users.csv`). Les occurrences supprimées sont consignées dans `data/processed/audit_deleted_rows.csv` avec le motif `EXACT_DUPLICATE_ROW`.
* **Doublons de clés primaires (*device_id* / *user_id*) :** Pour les référentiels statiques, déduplication sur la clé primaire en conservant systématiquement la version la plus récente (`keep='last'`). Les anciennes versions écartées sont également archivées dans le fichier d'audit global.

### B. Normalisation Temporelle (*Validity*)

* **Horodatages (*Timestamps*) :** Conversion systématique de tous les champs temporels (`timestamp`) des logs d'authentification et des alertes EDR vers un format normalisé `datetime` avec fuseau horaire UTC (`utc=True`) pour permettre des analyses chronologiques et des tris cohérents.

### C. Standardisation Textuelle (*Consistency*)

* **Casse et Espaces :** Harmonisation des champs textuels (ex. systèmes d'exploitation dans `assets.csv`, départements dans `users.csv`, types d'événements) via le passage en majuscules (`.str.upper()`) et la suppression des espaces superflus (`.str.strip()`) pour garantir la fiabilité des futures jointures inter-fichiers.

### D. Gestion des Valeurs Manquantes (*Completeness*)

* **Décisions d'analystes (*analyst_decision*) :** Conformément aux réserves de l'équipe IT, l'absence de décision est un comportement nominal (renseigné uniquement si l'alerte a été traitée). Ces valeurs nulles sont explicitement remplacées par le libellé `UNREVIEWED`.
* **Attributs descriptifs :** Imputation des valeurs manquantes critiques par des valeurs par défaut sécurisées (ex. `UNKNOWN_OS`, `UNASSIGNED`) pour éviter les ruptures lors des traitements.

### E. Champs Invalides et Adresses IP (*Validity* & *Accuracy*)

* **Adresses IP sources (*src_ip*) :** Application d'une expression régulière IPv4 (`^(?:[0-9]{1,3}\.){3}[0-9]{1,3}$`).
* **Traitement :** Les adresses IP mal formées ou aberrantes ne sont pas supprimées. Un indicateur booléen d'audit (`is_valid_ip`) est positionné à `False`, et les lignes correspondantes sont isolées et exportées dans `data/processed/invalid_ips.csv` pour investigation par l'analyste sécurité.

### F. Intégrité Référentielle et Entités Orphelines (*Accuracy* / *Shadow IT*)

* **Utilisateurs et Machines Orphelins :** Croisement des logs opérationnels (`authentication_logs.csv`, `edr_alerts.csv`) avec les référentiels (`users.csv`, `assets.csv`).
* **Traitement :** Les logs d'authentification associés à des identifiants inconnus du référentiel RH (`user_id` absents de `users.csv`) sont isolés et sauvegardés dans `data/processed/orphan_auth_users.csv` afin de révéler de potentiels cas de *Shadow IT* ou d'accès non autorisés sans altérer le flux d'analyse.

---

## 3. Traçabilité et Structure de Sortie (`data/processed/`)

Le dossier des données traitées centralise les livrables suivants :

* `audit_deleted_rows.csv` : Journal centralisé des doublons et lignes supprimées.
* `invalid_ips.csv` : Relevé des logs d'authentification présentant des formats d'IP incorrects.
* `orphan_auth_users.csv` : Liste des connexions rattachées à des utilisateurs hors référentiel.
* `combined_data.csv` : Datasets nettoyés et consolidés prêts pour l'étape de modélisation.