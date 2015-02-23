#!/bin/bash
# Installer for Roundware Server (http://www.roundware.org/)
# Tested with Ubuntu 14.04 LTS 64 bit

# Enable exit on error
set -e
set -v

# Default MySQL root user password (Change this on a production system!)
MYSQL_ROOT="password"

# Store the script start path
SOURCE_PATH="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Check if we are installing via vagrant (assuming standard Vagrant /vagrant share)
if [ -d "/vagrant" ]; then
  echo "Found Vagrant."
  FOUND_VAGRANT=true
fi

# Default user name.
USERNAME="roundware"

# Use vagrant username/directories used when available.
if [ "$FOUND_VAGRANT" = true ]; then
  # Change the user to the vagrant default.
  USERNAME="vagrant"

  # Create a symbolic link in the user's directory to the code
  ln -sfn /vagrant /home/$USERNAME/roundware-server
fi

# Set paths/directories
HOME_PATH="/home/$USERNAME"
DEV_CODE_PATH="$HOME_PATH/roundware-server"

WWW_PATH="/var/www/roundware"
CODE_PATH="$WWW_PATH/source"
STATIC_PATH="$WWW_PATH/static"
MEDIA_PATH="$WWW_PATH/rwmedia"
VENV_PATH="$WWW_PATH"
SITE_PACKAGES_PATH="$VENV_PATH/lib/python2.7/site-packages"

# If not vagrant, create user and copy files.
if [ ! "$FOUND_VAGRANT" = true ]; then

  # If user home doesn't exist, create the user.
  if [ ! -d "/home/$USERNAME" ]; then
    useradd $USERNAME -s /bin/bash -m -d $HOME_PATH
  fi

  # If source and dev code paths are different, create a symbolic link to code.
  if [ $SOURCE_PATH != $DEV_CODE_PATH ]; then
    rm -rf $DEV_CODE_PATH
    ln -sfn $CODE_PATH $DEV_CODE_PATH
  fi
fi

# Install required packages non-interactive
DEBIAN_FRONTEND=noninteractive apt-get install -y python-dev python-pip

# Install/upgrade virtualenv
pip install -U virtualenv fabric

$CODE_PATH/fab localhost install
# Create the virtual environment
virtualenv --system-site-packages $VENV_PATH

# Activate the environment
source $VENV_PATH/bin/activate
# Set python path to use production code
export PYTHONPATH=$CODE_PATH

# Setup MySQL database
echo "create database IF NOT EXISTS roundware;" | mysql -uroot -p$MYSQL_ROOT
echo "grant all privileges on roundware.* to 'round'@'localhost' identified by 'round';" | mysql -uroot -p$MYSQL_ROOT

# File/directory configurations
mkdir -p $MEDIA_PATH
mkdir -p $STATIC_PATH

# copy test audio file to media storage
cp $SOURCE_PATH/files/rw_test_audio1.wav $MEDIA_PATH

# Copy default production settings file
mkdir $WWW_PATH/settings
cp $SOURCE_PATH/files/var-www-roundware-settings.py $WWW_PATH/settings/roundware_production.py
chown $USERNAME:$USERNAME -R $WWW_PATH/settings

# Setup roundware log and logrotate
touch /var/log/roundware
chown $USERNAME:$USERNAME /var/log/roundware

# Run the production upgrade/deployment script
$SOURCE_PATH/deploy.sh

# Setup Apache Server
a2enmod rewrite
a2enmod wsgi
a2enmod headers
a2dissite 000-default
# Setup roundware in Apache
rm -f /etc/apache2/sites-available/roundware.conf
sed s/USERNAME/$USERNAME/g $CODE_PATH/files/etc-apache2-sites-available-roundware > /etc/apache2/sites-available/roundware.conf
a2ensite roundware

# Setup logrotate
sed s/USERNAME/$USERNAME/g $CODE_PATH/files/etc-logrotate-d-roundware > /etc/logrotate.d/roundware

# Install correct shout2send gstreamer plugin
mv /usr/lib/x86_64-linux-gnu/gstreamer-0.10/libgstshout2.so /usr/lib/x86_64-linux-gnu/gstreamer-0.10/libgstshout2.so.old
cp $CODE_PATH/files/64-bit/libgstshout2.so /usr/lib/x86_64-linux-gnu/gstreamer-0.10/libgstshout2.so

# Set $USERNAME to own all files
chown $USERNAME:$USERNAME -R $HOME_PATH

# Setup the default admin account
su - $USERNAME -c "$CODE_PATH/roundware/manage.py loaddata default_auth.json"

# Setup the sample project
su - $USERNAME -c "$CODE_PATH/roundware/manage.py loaddata sample_project.json"

service apache2 restart

# Setup icecast
cp $CODE_PATH/files/etc-default-icecast2 /etc/default/icecast2
cp $CODE_PATH/files/etc-icecast2-icecast.xml /etc/icecast2/icecast.xml
service icecast2 restart

echo "Install Complete"
