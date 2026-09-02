## Documentation des Règles de Transformation et de Traçabilité

1. Principes directeurs et Règle d'or
* Objectif : Transformer les données brutes et hétérogènes de sécurité (data/raw/) en un dataset consolidé et propre (data/processed/) tout en garantissant une traçabilité rigoureuse.  
* Règle d'or en cybersécurité : Aucune suppression silencieuse n'est tolérée. Chaque anomalie (doublon, IP invalide, entité orpheline) est isolée dans des tables de rejet dédiées afin de préserver d'éventuels signaux faibles d'attaque.  

2. Matrice des Règles de Transformation par Source

````text
Source / FichierDimension QualitéAnomalie / Problème IdentifiéRègle de Transformation et Traitement AppliquéFichier d'Audit / SortieTous les fichiersUniqueness  Doublons stricts (lignes 100% identiques)  Isolation et suppression des doublons stricts (conservation de la première occurrence).data/processed/audit_deleted_rows.csvassets.csv / users.csvUniqueness  Doublons sur les clés primaires (device_id, user_id)  Déduplication ciblée en conservant la dernière version mise à jour (keep='last').data/processed/audit_deleted_rows.csvauthentication_logs.csv / edr_alerts.csvValidity  Horodatages hétérogènes (ISO 8601, formats locaux, Epoch)  Conversion systématique au format UTC unifié avec fuseau horaire (pd.to_datetime(..., utc=True)).Dataset normaliséassets.csv / users.csvConsistency  Casse non uniformisée et espaces superflusApplication de la normalisation textuelle (.str.upper() et .str.strip()).Dataset normaliséauthentication_logs.csvValidity  Adresses IP mal formées ou aberrantesCréation d'un flag booléen d'audit (is_valid_ip) et isolation des lignes sans suppression.data/processed/invalid_ips.csvedr_alerts.csvCompleteness  Champ analyst_decision massivement vide (~85%)  Imputation par la valeur par défaut explicite UNREVIEWED (comportement fonctionnel nominal validé par l'IT).  Dataset normaliséauthentication_logs.csvAccuracy  Utilisateurs orphelins (user_id absent de users.csv)  Isolation des enregistrements sans suppression pour identifier d'éventuels cas de Shadow IT.  data/processed/orphan_auth_users.csv

````