sudo useradd -M honeypot_user -d /home/honeypot_user -s /bin/fshell
sudo passwd honeypot_user
sudo mkdir -p /var/log/honeypot
sudo chown -R honeypot_user:honeypot_user /var/log/honeypot/
sudo chmod -R 0755 /var/log/honeypot