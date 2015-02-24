#!/bin/bash
# Installer for Roundware Server (http://www.roundware.org/)
# Tested with Ubuntu 14.04 LTS 64 bit

# Enable exit on error
set -e
set -v

DEV_CODE_PATH="$HOME_PATH/roundware-server"

WWW_PATH="/var/www/roundware"
CODE_PATH="$WWW_PATH/source"
STATIC_PATH="$WWW_PATH/static"
MEDIA_PATH="$WWW_PATH/rwmedia"
VENV_PATH="$WWW_PATH"

# If not vagrant, create user and copy files.
if [ -d "/vagrant" ]; then
    # Default user name.
    USERNAME="roundware"
    # Set paths/directories
    HOME_PATH="/home/$USERNAME"
  # If user home doesn't exist, create the user.
  if [ ! -d "/home/$USERNAME" ]; then
    useradd $USERNAME -s /bin/bash -m -d $HOME_PATH
  fi
fi

# Install required packages non-interactive
DEBIAN_FRONTEND=noninteractive apt-get install -y python-dev python-pip

# Install/upgrade virtualenv
pip install -U virtualenv fabric
$CODE_PATH/fab localhost install_roundware
