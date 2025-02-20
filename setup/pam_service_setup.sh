#!/bin/bash
# Creates /etc/pam.d/honeypot with config

PAM_FILE="/etc/pam.d/admin"

sudo tee "$PAM_FILE" > /dev/null <<EOF
auth      required      pam_unix.so try_first_pass
account   required      pam_unix.so
password  required      pam_unix.so
session   required      pam_unix.so
EOF

if [ $? -eq 0 ]; then
    echo "PAM config created successfully at $PAM_FILE"
else
    echo "Failed to create $PAM_FILE"
    exit 1
fi