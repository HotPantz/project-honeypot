#!/usr/bin/env python3
import os
import random
from datetime import datetime, timedelta
import time
import pwd
import grp
import subprocess

# Liste des utilisateurs pour lesquels créer des fichiers
users = [
    "crypto-trader01",
    "crypto-trader02",
    "wallet-manager",
    "blockchain-analyst",
    "crypto-investor",
    "crypto-researcher",
    "crypto-dev",
    "crypto-admin"
]

# Dossiers principaux
main_folders = ["Documents", "Downloads", "Music", "Pictures", "Videos"]

# Sous-dossiers dans Documents
doc_subfolders = ["Crypto", "Wallets", "Reports", "Transactions", "Investments", "Logs"]

# Nombre de fichiers à créer par section
NUM_FILES = 50
base_date = datetime.today()

# Listes pour Crypto
CRYPTO_NAMES = [
    "Bitcoin", "Ethereum", "Ripple", "Litecoin", "Cardano",
    "Polkadot", "Stellar", "Chainlink", "Binance Coin", "Tether"
]
WALLETS = [
    "BTC Wallet", "ETH Wallet", "XRP Wallet", "LTC Wallet", "ADA Wallet",
    "DOT Wallet", "XLM Wallet", "LINK Wallet", "BNB Wallet", "USDT Wallet"
]

# Préfixes naturels selon le sous-dossier de Documents
doc_prefixes = {
    "Crypto": "crypto",
    "Wallets": "wallet",
    "Reports": "report",
    "Transactions": "transaction",
    "Investments": "investment",
    "Logs": "log"
}

def generate_crypto_content():
    crypto = random.choice(CRYPTO_NAMES)
    wallet = random.choice(WALLETS)
    balance = random.randint(1, 1000)
    current_date = datetime.today().strftime("%Y-%m-%d")
    # On exporte le nom de crypto pour le nom de fichier
    return crypto, f"Cryptocurrency: {crypto}\nWallet: {wallet}\nBalance: {balance}\nDate: {current_date}\nNotes: Fausse information pour {crypto}."

# Pour Downloads, association extension -> liste de noms naturels
download_names = {
    "png": ["vacation_photo", "screenshot", "wallpaper", "profile_pic", "banner"],
    "jpg": ["holiday_photo", "snapshot", "portrait", "scenery", "insta_pic"],
    "pdf": ["invoice", "annual_report", "ebook", "manual", "whitepaper"],
    "mp3": ["favorite_song", "podcast_episode", "audio_note", "ringtone", "music_track"],
    "docx": ["meeting_minutes", "project_proposal", "resume", "cover_letter", "letter"],
    "xlsx": ["financial_sheet", "budget", "sales_data", "inventory", "statistics"],
    "pptx": ["presentation", "pitch_deck", "conference_slides", "training_material", "overview"],
    "txt": ["notes", "readme", "todo_list", "log", "draft"],
    "zip": ["archive", "backup", "compressed_files", "old_data", "package"],
    "tar.gz": ["source_code", "distribution", "release_package", "software_bundle", "documentation"]
}
download_exts = list(download_names.keys())

# Fonction pour créer des fichiers pour un utilisateur donné
def create_files_for_user(user):
    try:
        user_info = pwd.getpwnam(user)
        uid = user_info.pw_uid
        gid = user_info.pw_gid
        base_home = user_info.pw_dir

        # Créer les dossiers principaux
        for folder in main_folders:
            folder_path = os.path.join(base_home, folder)
            os.makedirs(folder_path, exist_ok=True)
            os.chown(folder_path, uid, gid)

        # Créer les sous-dossiers dans Documents
        for subfolder in doc_subfolders:
            subfolder_path = os.path.join(base_home, "Documents", subfolder)
            os.makedirs(subfolder_path, exist_ok=True)
            os.chown(subfolder_path, uid, gid)

        # Créer les fichiers dans Documents avec noms liés au sous-dossier
        for i in range(1, NUM_FILES+1):
            subfolder = random.choice(doc_subfolders)
            target_dir = os.path.join(base_home, "Documents", subfolder)
            crypto, content = generate_crypto_content()
            crypto_clean = crypto.replace(" ", "_")
            prefix = doc_prefixes.get(subfolder, "doc")
            filename = f"{prefix}_{crypto_clean}_{i}.txt"
            filepath = os.path.join(target_dir, filename)
            with open(filepath, "w") as f:
                f.write(content)
            file_date = (base_date + timedelta(days=i)).strftime("%Y-%m-%d")
            # Convertir la date en timestamp
            ts = time.mktime(datetime.strptime(file_date, "%Y-%m-%d").timetuple())
            os.utime(filepath, (ts, ts))
            os.chown(filepath, uid, gid)
            print(f"Créé {filepath} avec la date {file_date}")

        # Créer les fichiers dans Downloads
        downloads_dir = os.path.join(base_home, "Downloads")
        for i in range(1, NUM_FILES+1):
            ext = random.choice(download_exts)
            name_list = download_names[ext]
            base_name = random.choice(name_list)
            filename = f"{base_name}_{i}.{ext}"
            filepath = os.path.join(downloads_dir, filename)
            # Pour certains types, on peut créer un contenu fictif ; sinon, fichier vide.
            content = f"Fichier {base_name} fictif, extension {ext}." if ext in ["txt", "docx", "pdf"] else ""
            with open(filepath, "w") as f:
                f.write(content)
            file_date = (base_date + timedelta(days=i)).strftime("%Y-%m-%d")
            ts = time.mktime(datetime.strptime(file_date, "%Y-%m-%d").timetuple())
            os.utime(filepath, (ts, ts))
            os.chown(filepath, uid, gid)
            print(f"Créé {filepath} avec la date {file_date}")

        print(f"Tous les fichiers ont été créés avec succès pour l'utilisateur {user}.")
    except KeyError:
        print(f"Utilisateur {user} non trouvé.")

# Fonction pour créer des utilisateurs et définir les permissions
def create_users_and_set_permissions():
    # Liste des utilisateurs factices à créer
    users = [
        "crypto-trader01",
        "crypto-trader02",
        "wallet-manager",
        "blockchain-analyst",
        "crypto-investor",
        "bitcoin-miner",
        "ethereum-miner",
        "crypto-researcher",
        "crypto-dev",
        "crypto-admin"
    ]

    # Créer les utilisateurs avec les options spécifiques
    for user in users:
        try:
            pwd.getpwnam(user)
            print(f"User {user} already exists")
        except KeyError:
            if user in ["bitcoin-miner", "ethereum-miner"]:
                subprocess.run(["sudo", "useradd", "-s", "/usr/sbin/nologin", user])
            else:
                subprocess.run(["sudo", "useradd", "-m", "-s", "/usr/bin/fshell", user])
            print(f"Created user: {user}")

    # Ajouter l'utilisateur froot
    try:
        pwd.getpwnam("froot")
        print("User froot already exists")
    except KeyError:
        subprocess.run(["sudo", "useradd", "-m", "-s", "/usr/bin/fshell", "froot"])
        print("Created user: froot")

    # Donner tous les droits à froot sur les répertoires personnels des utilisateurs factices
    for user in users:
        if user not in ["bitcoin-miner", "ethereum-miner"]:
            subprocess.run(["sudo", "setfacl", "-m", "u:froot:rwx", f"/home/{user}"])
            print(f"Granted all permissions to froot on /home/{user}")

    print("All users created and permissions modified successfully.")

# Créer des utilisateurs et définir les permissions
create_users_and_set_permissions()

# Créer des fichiers pour chaque utilisateur spécifié
for user in users:
    create_files_for_user(user)