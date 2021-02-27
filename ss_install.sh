#!/bin/bash

# install python3 dependencies
printf "Installing python3 dependencies...\n"
pip3 install python-dateutil
pip3 install python-dotenv


# install ansible dependencies
printf "Installing ansible dependencies...\n"
sudo apt update
sudo apt install software-properties-common
sudo apt-add-repository --yes --update ppa:ansible/ansible
sudo apt install ansible
