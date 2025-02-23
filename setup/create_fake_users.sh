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

# Nom du groupe commun
GROUP="crypto-group"

# Créer le groupe commun
sudo groupadd "$GROUP"
echo "Created group: $GROUP"

# Créer les utilisateurs avec les options spécifiques et les ajouter au groupe
for user in "${USERS[@]}"; do
  if [ "$user" = "bitcoin-miner" ] || [ "$user" = "ethereum-miner" ]; then
    sudo useradd -s /usr/sbin/nologin -G "$GROUP" "$user"
  else
    sudo useradd -m -s /usr/bin/fshell -G "$GROUP" "$user"
  fi
  echo "Created user: $user"
done

# Ajouter l'utilisateur froot au groupe
sudo usermod -aG "$GROUP" froot
echo "Added froot to group: $GROUP"

# Modifier les permissions des répertoires personnels pour permettre l'accès au groupe
for user in "${USERS[@]}"; do
  if [ "$user" != "bitcoin-miner" ] && [ "$user" != "ethereum-miner" ]; then
    sudo chmod 770 "/home/$user"
    sudo chgrp "$GROUP" "/home/$user"
    echo "Modified permissions for /home/$user"
  fi
done

echo "All users created and permissions modified successfully."