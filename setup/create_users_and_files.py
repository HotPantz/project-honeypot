#!/usr/bin/env python3
import os
import random
from datetime import datetime, timedelta
import time
import pwd
import grp
import subprocess

#setup script that creates fake cryptocurrency-themed users and files for the honeypot

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

main_folders = ["Documents", "Downloads", "Music", "Pictures", "Videos"]

doc_subfolders = ["Crypto", "Wallets", "Reports", "Transactions", "Investments", "Logs"]

NUM_FILES = 50
base_date = datetime.today()

CRYPTO_NAMES = [
    "Bitcoin", "Ethereum", "Ripple", "Litecoin", "Cardano",
    "Polkadot", "Stellar", "Chainlink", "Binance Coin", "Tether"
]
WALLETS = [
    "BTC Wallet", "ETH Wallet", "XRP Wallet", "LTC Wallet", "ADA Wallet",
    "DOT Wallet", "XLM Wallet", "LINK Wallet", "BNB Wallet", "USDT Wallet"
]

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
    #returns both crypto name for filename and formatted content
    return crypto, f"Cryptocurrency: {crypto}\nWallet: {wallet}\nBalance: {balance}\nDate: {current_date}\nNotes: Fausse information pour {crypto}."

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

def create_files_for_user(user):
    try:
        user_info = pwd.getpwnam(user)
        uid = user_info.pw_uid
        gid = user_info.pw_gid
        base_home = user_info.pw_dir

        for folder in main_folders:
            folder_path = os.path.join(base_home, folder)
            os.makedirs(folder_path, exist_ok=True)
            os.chown(folder_path, uid, gid)

        for subfolder in doc_subfolders:
            subfolder_path = os.path.join(base_home, "Documents", subfolder)
            os.makedirs(subfolder_path, exist_ok=True)
            os.chown(subfolder_path, uid, gid)

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
            ts = time.mktime(datetime.strptime(file_date, "%Y-%m-%d").timetuple())
            os.utime(filepath, (ts, ts))
            os.chown(filepath, uid, gid)
            print(f"Créé {filepath} avec la date {file_date}")

        downloads_dir = os.path.join(base_home, "Downloads")
        for i in range(1, NUM_FILES+1):
            ext = random.choice(download_exts)
            name_list = download_names[ext]
            base_name = random.choice(name_list)
            filename = f"{base_name}_{i}.{ext}"
            filepath = os.path.join(downloads_dir, filename)
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

def create_users_and_set_permissions():
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

    #create users with specific options
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

    #add the froot user
    try:
        pwd.getpwnam("froot")
        print("User froot already exists")
    except KeyError:
        subprocess.run(["sudo", "useradd", "-m", "-s", "/usr/bin/fshell", "froot"])
        print("Created user: froot")

    #give froot full permissions on fake users' home directories
    for user in users:
        if user not in ["bitcoin-miner", "ethereum-miner"]:
            subprocess.run(["sudo", "setfacl", "-m", "u:froot:rwx", f"/home/{user}"])
            print(f"Granted all permissions to froot on /home/{user}")

    print("All users created and permissions modified successfully.")

create_users_and_set_permissions()

for user in users:
    create_files_for_user(user)