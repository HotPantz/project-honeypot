#!/bin/bash

# UTILISER SUDO POUR EXÉCUTER CE SCRIPT

# -----------------------------------------------------------------------------
# Répertoire de base
BASE_HOME="/home/admin"

# Création de plusieurs dossiers types dans un vrai home
FOLDERS=("Documents" "Downloads" "Music" "Pictures" "Videos")
for folder in "${FOLDERS[@]}"; do
  mkdir -p "$BASE_HOME/$folder"
done

# Nombre de fichiers à créer
NUM_FILES=50

# Date de base pour les timestamps (ex. à partir d'aujourd'hui)
BASE_DATE=$(date +%Y-%m-%d)

# Tableaux de données d'exemple
CRYPTO_NAMES=(
  "Bitcoin" "Ethereum" "Ripple" "Litecoin" "Cardano" "Polkadot" "Stellar" "Chainlink" "Binance Coin" "Tether"
)

WALLETS=(
  "BTC Wallet" "ETH Wallet" "XRP Wallet" "LTC Wallet" "ADA Wallet" "DOT Wallet" "XLM Wallet" "LINK Wallet" "BNB Wallet" "USDT Wallet"
)

# Fonction pour générer le contenu d'un fichier
generate_content() {
    local crypto="${CRYPTO_NAMES[$RANDOM % ${#CRYPTO_NAMES[@]}]}"
    local wallet="${WALLETS[$RANDOM % ${#WALLETS[@]}]}"
    local balance
    balance=$(shuf -i 1-1000 -n 1)
    local current_date
    current_date=$(date +%Y-%m-%d)
    
    # Exporter le nom de crypto pour utilisation dans le nom du fichier
    GENERATED_CRYPTO="$crypto"
    
    printf "Cryptocurrency: %s\nWallet: %s\nBalance: %s\nDate: %s\nNotes: This is a fake wallet for %s.\n" "$crypto" "$wallet" "$balance" "$current_date" "$crypto"
}

# Boucle pour créer les fichiers
for i in $(seq 1 $NUM_FILES); do
  # Sélectionner aléatoirement un des dossiers du "home"
  folder="${FOLDERS[$RANDOM % ${#FOLDERS[@]}]}"
  TARGET_DIR="$BASE_HOME/$folder"
  
  # Générer le contenu et récupérer la crypto générée
  file_content=$(generate_content)
  crypto_for_filename=$GENERATED_CRYPTO
  # Remplacer les espaces par des underscores dans le nom de crypto pour le nom du fichier
  crypto_sanitized=${crypto_for_filename// /_}
  
  # Générer un nom de fichier personnalisé
  FILENAME="$TARGET_DIR/wallet_${crypto_sanitized}_$i.txt"
  
  # Générer une date pour le fichier (ex. jours incrémentés)
  FILE_DATE=$(date -d "$BASE_DATE +$i day" +%Y-%m-%d)
  
  # Créer le fichier avec le contenu spécifique
  echo -e "$file_content" > "$FILENAME"
  
  # Définir la date de modification du fichier
  touch -d "$FILE_DATE" "$FILENAME"
  
  echo "Créé $FILENAME avec la date $FILE_DATE dans $TARGET_DIR"
done

echo "Tous les fichiers ont été créés avec succès."