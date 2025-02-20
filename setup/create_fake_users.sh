#!/bin/bash

# USE SUDO TO RUN THIS SCRIPT

# -----------------------------------------------------------------------------

# Liste des utilisateurs factices à créer
USERS=(
  "crypto-trader01"
  "crypto-trader02"
  "wallet-manager"
  "blockchain-analyst"
  "crypto-investor"
  "bitcoin-miner"
  "ethereum-miner"
  "crypto-researcher"
  "crypto-dev"
  "crypto-admin"
)

# Créer les utilisateurs avec les options spécifiques
for user in "${USERS[@]}"; do
  if [ "$user" = "bitcoin-miner" ] || [ "$user" = "ethereum-miner" ]; then
    sudo useradd -s /usr/sbin/nologin "$user"
  else
    sudo useradd -m -s /usr/bin/fshell "$user"
  fi
  echo "Created user: $user"
done

echo "All users created successfully."