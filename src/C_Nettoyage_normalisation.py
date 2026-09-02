# Import des bibliothèque
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import os
import re


#############################"" 1. Charegement de données

RAW_DATA_DIR = os.path.join("data", "raw")

df_auth = pd.read_csv(os.path.join(RAW_DATA_DIR, 'authentication_logs.csv'))
df_edr = pd.read_csv(os.path.join(RAW_DATA_DIR, 'edr_alerts.csv'))
df_assets = pd.read_csv(os.path.join(RAW_DATA_DIR, 'assets.csv'))
df_users = pd.read_csv(os.path.join(RAW_DATA_DIR, 'users.csv'))


########################## 2. GESTION DES DOUBLONS (Uniqueness)
audit_logs = []

# Traçabilité et suppression des doublons stricts (lignes 100% identiques)
for name, df, filename in [("auth", df_auth, 'authentication_logs.csv'), 
                           ("edr", df_edr, 'edr_alerts.csv'), 
                           ("assets", df_assets, 'assets.csv'), 
                           ("users", df_users, 'users.csv')]:
    if df is not None:
        mask_dupes = df.duplicated(keep='first')
        if mask_dupes.sum() > 0:
            df_dropped = df[mask_dupes].copy()
            df_dropped['source_file'] = filename
            df_dropped['deletion_reason'] = 'EXACT_DUPLICATE_ROW'
            audit_logs.append(df_dropped)
            df.drop_duplicates(inplace=True)
            print(f" {name} : {mask_dupes.sum()} doublons exacts isolés et supprimés.")

# Déduplication sur clés primaires des référentiels (conservation de la dernière version)
for name, df, pk, filename in [("assets", df_assets, 'device_id', 'assets.csv'), 
                               ("users", df_users, 'user_id', 'users.csv')]:
    if df is not None and pk in df.columns:
        mask_pk = df.duplicated(subset=[pk], keep='last')
        if mask_pk.sum() > 0:
            df_dropped = df[mask_pk].copy()
            df_dropped['source_file'] = filename
            df_dropped['deletion_reason'] = f'PRIMARY_KEY_DUPLICATE_KEEP_LAST ({pk})'
            audit_logs.append(df_dropped)
            df.drop_duplicates(subset=[pk], keep='last', inplace=True)
            print(f"🔑 {name} : {mask_pk.sum()} doublons de clé '{pk}' écartés (dernière version conservée).")

# Exportation du journal d'audit
if audit_logs:
    df_audit_global = pd.concat(audit_logs, ignore_index=True)
    audit_output_path = os.path.join("data", "processed", "audit_deleted_rows.csv")
    df_audit_global.to_csv(audit_output_path, index=False)
    print(f"[AUDIT SÉCURITÉ] {len(df_audit_global)} lignes écartées archivées dans : {audit_output_path}")


#################### 3. NORMALISATION DES TEMPS (Validity - Timestamps)

# Conversion en UTC pour unifier les fuseaux horaires hétérogènes

for name, df in [("authentication_logs.csv", df_auth), ("edr_alerts.csv", df_edr)]:
    if 'timestamp' in df.columns:
        df['timestamp'] = pd.to_datetime(df['timestamp'], utc=True, errors='coerce')
        invalid_dates = df['timestamp'].isnull().sum()
        print(f" {name} : {invalid_dates} timestamp invalides convertis en NaT.")


###################### 4. GESTION DES CHAMPS INVALIDES (Sans suppression)

# Isolation des adresses IP mal formées dans les logs d'authentification via un flag d'audit
if 'src_ip' in df_auth.columns:
    ipv4_regex = re.compile(r'^(?:[0-9]{1,3}\.){3}[0-9]{1,3}$')
    df_auth['is_valid_ip'] = df_auth['src_ip'].astype(str).apply(lambda x: bool(ipv4_regex.match(x)))
    
    # Isolation des lignes invalides dans un nouveau DataFrame
    df_invalid_ips = df_auth[~df_auth['is_valid_ip']].copy()
    invalid_count = len(df_invalid_ips)
    
    print(f"Sécurité : {invalid_count} adresses IP suspectes/invalides identifiées et isolées (conservées pour investigation).")
    
    if invalid_count > 0:
        # Documentation du motif d'anomalie pour l'audit
        df_invalid_ips['audit_reason'] = 'INVALID_IP_FORMAT'
        
        # Exportation sécurisée du DataFrame vers le dossier processed
        audit_path = os.path.join("data", "processed", "invalid_ips.csv")
        df_invalid_ips.to_csv(audit_path, index=False)
        print(f"Fichier d'audit généré avec succès : {audit_path}")


########################  5. TRAITEMENT DES VALEURS MANQUANTES (Completeness)

# Le champ analyst_decision est partiel (normal selon l'IT) -> Marquage explicite
if 'analyst_decision' in df_edr.columns:
    df_edr['analyst_decision'] = df_edr['analyst_decision'].fillna('UNREVIEWED')

# Valeurs par défaut pour les référentiels afin d'éviter les ruptures de jointure
df_assets['operating_system'] = df_assets['operating_system'].fillna('UNKNOWN_OS')
df_assets['department'] = df_assets['department'].fillna('UNASSIGNED')
df_users['department'] = df_users['department'].fillna('UNASSIGNED')

######################## 6. STANDARDISATION DES CATÉGORIES (Consistency)

# Harmonisation de la casse et suppression des espaces 
df_assets['operating_system'] = df_assets['operating_system'].str.upper().str.strip()
df_assets['asset_type'] = df_assets['asset_type'].str.title().str.strip()
df_users['department'] = df_users['department'].str.upper().str.strip()
df_auth['event_type'] = df_auth['event_type'].str.upper().str.strip()

print("Standardisation textuelle (casse et espaces) appliquée.")



########################  7. CONSTRUCTION DU FORMAT COMMUN (Compil des sources)

# Utilisation de LEFT JOIN depuis les tables de faits vers les référentiels
# Ne perdre aucune alerte ou log, même si la machine ou l'user est inconnu (Shadow IT / Obsolescence)
df_consolidated = df_auth.merge(
    df_users, on='user_id', how='left', suffixes=('', '_user')
).merge(
    df_assets, on='device_id', how='left', suffixes=('', '_asset')
)

print(f"\nDataset consolidé généré avec succès : {df_consolidated.shape[0]} lignes, {df_consolidated.shape[1]} colonnes.")
print("Aperçu des premières colonnes du format commun :")
print(df_consolidated[['event_id', 'timestamp', 'user_id', 'department', 'device_id', 'operating_system']].head(3))

consolidated_path = os.path.join("data", "processed", "combined_data.csv")
df_consolidated.to_csv(consolidated_path,index=False)