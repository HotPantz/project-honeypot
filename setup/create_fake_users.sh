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
  if id "$user" &>/dev/null; then
    echo "User $user already exists"
  else
    if [ "$user" = "bitcoin-miner" ] || [ "$user" = "ethereum-miner" ]; then
      sudo useradd -s /usr/sbin/nologin "$user"
    else
      sudo useradd -m -s /usr/bin/fshell "$user"
    fi
    echo "Created user: $user"
  fi
done

# Ajouter l'utilisateur froot
if ! id "froot" &>/dev/null; then
  sudo useradd -m -s /usr/bin/fshell froot
  echo "Created user: froot"
fi

# Donner tous les droits à froot sur les répertoires personnels des utilisateurs factices
for user in "${USERS[@]}"; do
  if [ "$user" != "bitcoin-miner" ] && [ "$user" != "ethereum-miner" ]; then
    sudo setfacl -m u:froot:rwx "/home/$user"
    echo "Granted all permissions to froot on /home/$user"
  fi
done

echo "All users created and permissions modified successfully."