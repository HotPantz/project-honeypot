#!/bin/bash

# Vérifier si le script est exécuté avec des privilèges root
if [ "$(id -u)" -ne 0 ]; then
    echo "Ce script doit être exécuté avec des privilèges root."
    exit 1
fi

# Nom du nouvel utilisateur avec des privilèges root
NEW_USER="superuser"

# Vérifier si l'utilisateur existe
if ! id -u "$NEW_USER" >/dev/null 2>&1; then
    echo "L'utilisateur $NEW_USER n'existe pas. Veuillez créer cet utilisateur avant d'exécuter ce script."
    exit 1
fi

# Changer le propriétaire et le groupe de tous les fichiers appartenant à root
echo "Changement du propriétaire et du groupe de tous les fichiers appartenant à root vers $NEW_USER..."

find / -user root -exec chown "$NEW_USER":"$NEW_USER" {} \;
find / -group root -exec chgrp "$NEW_USER" {} \;

echo "Changement terminé."

# Créer un nouvel utilisateur avec des privilèges root
useradd -m -s /bin/bash "$NEW_USER"
usermod -aG sudo "$NEW_USER"

# Ajouter le nouvel utilisateur au fichier sudoers
echo "$NEW_USER ALL=(ALL) NOPASSWD:ALL" >> /etc/sudoers

# Modifier le shell de root pour empêcher les connexions directes
usermod -s /usr/sbin/nologin root

echo "L'utilisateur $NEW_USER a été créé avec des privilèges root."
echo "Le compte root a été modifié pour empêcher les connexions directes."