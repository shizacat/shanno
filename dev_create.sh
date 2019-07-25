#!/bin/bash

# Create development environment

VBASE=venv

# ======
sudo apt update

# ---
echo "Install NodeJS"
curl -sL https://dl.yarnpkg.com/debian/pubkey.gpg | sudo apt-key add -
echo "deb https://dl.yarnpkg.com/debian/ stable main" | sudo tee /etc/apt/sources.list.d/yarn.list
sudo apt update && sudo apt -y install yarn
curl --silent --location https://deb.nodesource.com/setup_6.x | sudo bash -
sudo apt install -y nodejs npm

# ---
echo "Install Gulp"
sudo npm install -g gulp

# ---
echo "Install Semantic UI"
# pip install django2-semantic-ui
npm install semantic-ui --save --no-bin-link
(
    cd semantic
    gulp build
)

# ---
echo "Install Python module"

sudo apt install python3-pip python3-venv

python3 -m venv ${VBASE}
. ${VBASE}/bin/activate

pip3 install -r requirements.txt

deactivate
