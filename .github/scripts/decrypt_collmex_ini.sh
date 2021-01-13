#!/bin/sh

# Decrypt the file
# --batch to prevent interactive command
# --yes to assume "yes" for questions
gpg --quiet --batch --yes --decrypt --passphrase="$GPG_PASSWORD_COLLMEX_INI" \
--output $HOME/collmex.ini collmex.ini.gpg
