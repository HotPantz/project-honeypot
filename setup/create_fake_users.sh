#!/bin/bash

# List of fake users to create
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

# Create users without home directories and with /usr/sbin/nologin shell
for user in "${USERS[@]}"; do
  sudo useradd -m -s /usr/sbin/nologin "$user"
  echo "Created user: $user"
done

echo "All users created successfully."