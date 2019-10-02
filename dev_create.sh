#!/bin/bash

# Create development environment

VBASE=venv

# ======
sudo apt update

# ---
# echo "Install NodeJS"
# curl -sL https://dl.yarnpkg.com/debian/pubkey.gpg | sudo apt-key add -
# echo "deb https://dl.yarnpkg.com/debian/ stable main" | sudo tee /etc/apt/sources.list.d/yarn.list
# sudo apt-get update && sudo apt-get -y install yarn
# curl --silent --location https://deb.nodesource.com/setup_6.x | sudo bash -
# sudo apt-get install -y nodejs npm

# ---
echo "Install Python module"

sudo apt-get install -y python3-pip python3-venv
sudo apt-get install -y libpq-dev python3-dev build-essential

python3 -m venv ${VBASE}
. ${VBASE}/bin/activate

pip3 install -r requirements.txt

# Setup Django
echo "from django.contrib.auth import get_user_model; User = get_user_model(); User.objects.create_superuser('admin', 'admin@myproject.com', 'admin')" | python3 manage.py shell
echo "Default user/password: admin/admin"

deactivate
