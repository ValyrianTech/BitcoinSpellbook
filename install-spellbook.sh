#!/bin/bash
cd ~
sudo apt-get update -y
sudo apt-get upgrade -y
sudo apt-get install git python2.7 python-dev python-pip -y

export PATH=$PATH:~/.local/bin

mkdir spellbook
cd spellbook
mkdir wallet
mkdir app_data

git clone https://github.com/ValyrianTech/BitcoinSpellbook-v0.3.git spellbook
cd spellbook

pip install -r requirements.txt