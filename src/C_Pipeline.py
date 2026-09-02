from C_Nettoyage_Norm_donnee import *

def run_security_pipeline():
    """Exécute l'intégralité du pipeline de nettoyage et de normalisation."""
    # 1. Chargement
    auth, edr, assets, users = load_raw_data()
    
    # 2. Doublons & Audit
    auth, edr, assets, users = clean_and_audit_duplicates(auth, edr, assets, users)
    
    # 3. Normalisation des dates
    auth, edr = normalize_timestamps(auth, edr)
    
    # 4. Champs invalides et orphelins
    auth = handle_invalid_ips(auth)
    auth = handle_orphan_users(auth, users)
    
    # 5. Valeurs manquantes et standardisation
    auth, edr, assets, users = clean_missing_and_standardize(auth, edr, assets, users)
    
    # 6. Consolidation finale
    df_final = consolidate_datasets(auth, users, assets)
    
    return df_final

# Exécution du pipeline complet
df_cleaned_consolidated = run_security_pipeline()