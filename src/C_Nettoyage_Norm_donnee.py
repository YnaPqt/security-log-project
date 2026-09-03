# Import des bibliothèques
import pandas as pd
import numpy as np
import os
import re

# ==========================================
# 1. CHARGEMENT DES DONNÉES BRUTES
# ==========================================
def load_raw_data(raw_data_dir="data/raw"):
    """Charge les fichiers CSV bruts de sécurité depuis le dossier spécifié."""
    df_auth = pd.read_csv(os.path.join(raw_data_dir, 'authentication_logs.csv'))
    df_edr = pd.read_csv(os.path.join(raw_data_dir, 'edr_alerts.csv'))
    df_assets = pd.read_csv(os.path.join(raw_data_dir, 'assets.csv'))
    df_users = pd.read_csv(os.path.join(raw_data_dir, 'users.csv'))
    print("Données brutes chargées avec succès.")
    return df_auth, df_edr, df_assets, df_users

# ==========================================
# 2. GESTION DES DOUBLONS ET TRAÇABILITÉ D'AUDIT
# ==========================================
def clean_and_audit_duplicates(df_auth, df_edr, df_assets, df_users, processed_dir="data/processed"):
    """Supprime les doublons stricts et de clés primaires tout en archivant les lignes écartées."""
    os.makedirs(processed_dir, exist_ok=True)
    audit_logs = []
    
    datasets = [
        ("auth", df_auth, 'authentication_logs.csv'),
        ("edr", df_edr, 'edr_alerts.csv'),
        ("assets", df_assets, 'assets.csv'),
        ("users", df_users, 'users.csv')
    ]
    
    # 1. Traçabilité et suppression des doublons stricts (100% identiques)
    for name, df, filename in datasets:
        if df is not None:
            mask_dupes = df.duplicated(keep='first')
            if mask_dupes.sum() > 0:
                df_dropped = df[mask_dupes].copy()
                df_dropped['source_file'] = filename
                df_dropped['deletion_reason'] = 'EXACT_DUPLICATE_ROW'
                audit_logs.append(df_dropped)
                df.drop_duplicates(inplace=True)
                print(f"{name} : {mask_dupes.sum()} doublons exacts isolés et supprimés.")

    # 2. Déduplication sur clés primaires des référentiels (conservation de la dernière version)
    pk_configs = [
        ("assets", df_assets, 'device_id', 'assets.csv'),
        ("users", df_users, 'user_id', 'users.csv')
    ]
    for name, df, pk, filename in pk_configs:
        if df is not None and pk in df.columns:
            mask_pk = df.duplicated(subset=[pk], keep='last')
            if mask_pk.sum() > 0:
                df_dropped = df[mask_pk].copy()
                df_dropped['source_file'] = filename
                df_dropped['deletion_reason'] = f'PRIMARY_KEY_DUPLICATE_KEEP_LAST ({pk})'
                audit_logs.append(df_dropped)
                df.drop_duplicates(subset=[pk], keep='last', inplace=True)
                print(f"{name} : {mask_pk.sum()} doublons de clé '{pk}' écartés.")

    # Exportation du journal d'audit global
    if audit_logs:
        df_audit_global = pd.concat(audit_logs, ignore_index=True)
        audit_output_path = os.path.join(processed_dir, "audit_deleted_rows.csv")
        df_audit_global.to_csv(audit_output_path, index=False)
        print(f"[AUDIT SÉCURITÉ] {len(df_audit_global)} lignes écartées archivées dans : {audit_output_path}")
        
    return df_auth, df_edr, df_assets, df_users

# ==========================================
# 3. NORMALISATION TEMPORELLE (Validity)
# ==========================================
def normalize_timestamps(df_auth, df_edr):
    """Convertit les timestamps au format UTC puis applique le format 'JJ/MM/AAAA' (%d/%m/%Y)."""
    for name, df in [("authentication_logs.csv", df_auth), ("edr_alerts.csv", df_edr)]:
        if df is not None and 'timestamp' in df.columns:
            # 1. Conversion en datetime UTC pour interpréter les différents formats bruts
            parsed_dates = pd.to_datetime(df['timestamp'], utc=True, errors='coerce')
            invalid_dates = parsed_dates.isnull().sum()
            
            # 2. Formatage au format cible %d/%m/%Y (JJ/MM/AAAA)
            df['timestamp'] = parsed_dates.dt.strftime('%d/%m/%Y')
            
            print(f" {name} : {invalid_dates} timestamps invalides convertis en NaT (format '%d/%m/%Y' appliqué).")
            
    return df_auth, df_edr

# ==========================================
# 4. GESTION DES CHAMPS INVALIDES & ORPHELINS
# ==========================================
def handle_invalid_ips(df_auth, processed_dir="data/processed"):
    """Isole les adresses IP mal formées sans suppression brute."""
    if df_auth is not None and 'src_ip' in df_auth.columns:
        ipv4_regex = re.compile(r'^(?:[0-9]{1,3}\.){3}[0-9]{1,3}$')
        df_auth['is_valid_ip'] = df_auth['src_ip'].astype(str).apply(lambda x: bool(ipv4_regex.match(x)))
        
        df_invalid_ips = df_auth[~df_auth['is_valid_ip']].copy()
        invalid_count = len(df_invalid_ips)
        print(f"Sécurité : {invalid_count} adresses IP suspectes/invalides identifiées.")
        
        if invalid_count > 0:
            df_invalid_ips['audit_reason'] = 'INVALID_IP_FORMAT'
            audit_path = os.path.join(processed_dir, "invalid_ips.csv")
            df_invalid_ips.to_csv(audit_path, index=False)
            print(f"Fichier d'audit IP généré : {audit_path}")
    return df_auth

def handle_orphan_users(df_auth, df_users, processed_dir="data/processed"):
    """Isole et sauvegarde les utilisateurs orphelins (Shadow IT / Absent du référentiel)."""
    if df_auth is not None and df_users is not None and 'user_id' in df_auth.columns and 'user_id' in df_users.columns:
        valid_users = set(df_users['user_id'].dropna())
        df_auth['is_known_user'] = df_auth['user_id'].isin(valid_users)
        
        df_orphan_users = df_auth[~df_auth['is_known_user']].copy()
        orphan_count = len(df_orphan_users)
        print(f"[ACCURACY] {orphan_count} logs d'authentification avec un 'user_id' inconnu.")
        
        if orphan_count > 0:
            df_orphan_users['audit_reason'] = 'ORPHAN_USER_ID (Absent de users.csv)'
            audit_path_user = os.path.join(processed_dir, "orphan_auth_users.csv")
            df_orphan_users.to_csv(audit_path_user, index=False)
            print(f"Rapport d'audit orphelins exporté : {audit_path_user}")
    return df_auth

# ==========================================
# 5. VALEURS MANQUANTES ET STANDARDISATION
# ==========================================
def clean_missing_and_standardize(df_auth, df_edr, df_assets, df_users):
    """Traite les valeurs manquantes et normalise la casse textuelle."""
    if df_edr is not None and 'analyst_decision' in df_edr.columns:
        df_edr['analyst_decision'] = df_edr['analyst_decision'].fillna('UNREVIEWED')
        
    if df_assets is not None:
        df_assets['operating_system'] = df_assets['operating_system'].fillna('UNKNOWN_OS').str.upper().str.strip()
        df_assets['asset_type'] = df_assets['asset_type'].fillna('UNKNOWN_TYPE').str.title().str.strip()
        df_assets['department'] = df_assets['department'].fillna('UNASSIGNED').str.upper().str.strip()
        
    if df_users is not None:
        df_users['department'] = df_users['department'].fillna('UNASSIGNED').str.upper().str.strip()
        
    if df_auth is not None and 'event_type' in df_auth.columns:
        df_auth['event_type'] = df_auth['event_type'].str.upper().str.strip()
        
    print("Traitement des valeurs manquantes et standardisation textuelle terminés.")
    return df_auth, df_edr, df_assets, df_users

# ==========================================
# 6. CONSOLIDATION ET EXPORTATION FINALE
# ==========================================
def consolidate_datasets(
    df_auth, df_users, df_assets, processed_dir="data/processed"):
  """Combine les sources via LEFT JOIN et remplace les valeurs manquantes par 'INCONNU'."""
  os.makedirs(processed_dir, exist_ok=True)

  # 1. Rapprochement des sources
  df_consolidated = df_auth.merge(
      df_users, on="user_id", how="left", suffixes=("", "_user")
  ).merge(df_assets, on="device_id", how="left", suffixes=("", "_asset"))

  # 2. Remplacement des valeurs manquantes (NaN) par 'INCONNU'
  df_consolidated = df_consolidated.fillna("INCONNU")

  print(
      f"\nDataset consolidé généré : {df_consolidated.shape[0]} lignes,"
      f" {df_consolidated.shape[1]} colonnes."
  )
  print(
      f"Valeurs manquantes restantes : {df_consolidated.isnull().sum().sum()}"
  )

  # 3. Exportation vers data/processed/
  consolidated_path = os.path.join(processed_dir, "combined_data.csv")
  df_consolidated.to_csv(consolidated_path, index=False)
  print(f"Dataset consolidé exporté : {consolidated_path}")

  return df_consolidated