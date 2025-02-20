#!/bin/bash

# Directory where files will be created
TARGET_DIR="/home/admin"

# Create the target directory if it doesn't exist
mkdir -p "$TARGET_DIR"

# Number of files to create
NUM_FILES=50

# Base date for file timestamps (e.g., starting from today)
BASE_DATE=$(date +%Y-%m-%d)

# Arrays of sample data
CRYPTO_NAMES=(
  "Bitcoin" "Ethereum" "Ripple" "Litecoin" "Cardano" "Polkadot" "Stellar" "Chainlink" "Binance Coin" "Tether"
)

WALLETS=(
  "BTC Wallet" "ETH Wallet" "XRP Wallet" "LTC Wallet" "ADA Wallet" "DOT Wallet" "XLM Wallet" "LINK Wallet" "BNB Wallet" "USDT Wallet"
)

# Function to generate random content for a file
generate_content() {
    local crypto=${CRYPTO_NAMES[$RANDOM % ${#CRYPTO_NAMES[@]}]}
    local wallet=${WALLETS[$RANDOM % ${#WALLETS[@]}]}
    local balance=$(shuf -i 1-1000 -n 1)
    local date=$(date +%Y-%m-%d)
    
    echo "Cryptocurrency: $crypto"
    echo "Wallet: $wallet"
    echo "Balance: $balance"
    echo "Date: $date"
    echo "Notes: This is a fake wallet for $crypto."
}

# Loop to create files
for i in $(seq 1 $NUM_FILES); do
  # Generate a filename with a specific pattern
  FILENAME="$TARGET_DIR/wallet_info_$i.txt"
  
  # Generate a date for the file (e.g., incrementing days)
  FILE_DATE=$(date -d "$BASE_DATE +$i day" +%Y-%m-%d)
  
  # Create the file with specific content
  generate_content > "$FILENAME"
  
  # Set the file's modification time to the generated date
  touch -d "$FILE_DATE" "$FILENAME"
  
  echo "Created $FILENAME with date $FILE_DATE in $TARGET_DIR"
done

echo "All files created successfully."