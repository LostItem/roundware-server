import os
import fabtools
from fabric.api import *
from fabtools.vagrant import vagrant
from fabtools import require
import cuisine

__author__ = 'Evan'

"""
A set of methods for managing and deploying RoundWare server instances
"""

PASSWORD = "ChangeMe!_tmp"

# Set paths/directories
WWW_PATH = "/var/www/roundware"
CODE_PATH = os.path.join(WWW_PATH, "source")
VENV_PATH = WWW_PATH

POSTGIS_PACKAGES = [
    'postgresql-contrib-9.3',
    'postgresql-server-dev-9.3',
    'postgresql-9.3-postgis-2.1',
    'postgresql-9.3-postgis-scripts',
    # spatial
    'python-gdal',
    'libproj-dev',
    ]


def virtualenv(command):
    activate = os.path.join(VENV_PATH, 'bin', 'activate')
    virtualenv_command = ' '.join(['source', activate, '&&', command])
    run(virtualenv_command)


def manage_py(cmd):
    with cd(os.path.join(CODE_PATH, 'roundware')):
        virtualenv("./manage.py " + cmd)


def patch(file, patch):
    run('patch -N {file} < {patch} || true'.format(file=file, patch=patch))


@task
def localhost(user='roundware'):
    """set environment variables for localhost"""

    env.hosts = ['localhost']
    env.host_string = 'localhost'

    env.user = user
    password = 'vagrant' if user == 'vagrant' else PASSWORD

    env.loginpassword = password
    env.password = password



@task
def install_roundware():
    """
    installs roundware on the server
    :return:
    """
    #!/bin/bash
    # # Installer for Roundware Server (http://www.roundware.org/)
    # # Tested with Ubuntu 14.04 LTS 64 bit
    #
    # # Enable exit on error
    # set -e
    # set -v
    #
    # # Default MySQL root user password (Change this on a production system!)
    # MYSQL_ROOT="password"
    #
    # # Store the script start path
    # SOURCE_PATH="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
    #
    # # Check if we are installing via vagrant (assuming standard Vagrant /vagrant share)
    # if [ -d "/vagrant" ]; then
    #   echo "Found Vagrant."
    #   FOUND_VAGRANT=true
    # fi
    #
    # # Default user name.
    # USERNAME="roundware"
    #
    # # Use vagrant username/directories used when available.
    # if [ "$FOUND_VAGRANT" = true ]; then
    #   # Change the user to the vagrant default.
    #   USERNAME="vagrant"
    #
    #   # Create a symbolic link in the user's directory to the code
    #   ln -sfn /vagrant /home/$USERNAME/roundware-server
    # fi
    #
    # # Set paths/directories
    # HOME_PATH="/home/$USERNAME"
    # DEV_CODE_PATH="$HOME_PATH/roundware-server"
    #
    # WWW_PATH="/var/www/roundware"
    # CODE_PATH="$WWW_PATH/source"
    # STATIC_PATH="$WWW_PATH/static"
    # MEDIA_PATH="$WWW_PATH/rwmedia"
    # VENV_PATH="$WWW_PATH"
    # SITE_PACKAGES_PATH="$VENV_PATH/lib/python2.7/site-packages"
    #
    # # If not vagrant, create user and copy files.
    # if [ ! "$FOUND_VAGRANT" = true ]; then
    #
    #   # If user home doesn't exist, create the user.
    #   if [ ! -d "/home/$USERNAME" ]; then
    #     useradd $USERNAME -s /bin/bash -m -d $HOME_PATH
    #   fi
    #
    #   # If source and dev code paths are different, create a symbolic link to code.
    #   if [ $SOURCE_PATH != $DEV_CODE_PATH ]; then
    #     rm -rf $DEV_CODE_PATH
    #     ln -sfn $CODE_PATH $DEV_CODE_PATH
    #   fi
    # fi
    #
    # # Replace the user's .profile
    # cp $SOURCE_PATH/files/home-user-profile /home/$USERNAME/.profile
    #
    # # Create a symbolic link to the main roundware directory
    # ln -sfn $WWW_PATH /home/$USERNAME/www
    #
    # apt-get update
    #
    # # Set MySQL root password
    # echo "mysql-server mysql-server/root_password password $MYSQL_ROOT" | debconf-set-selections
    # echo "mysql-server mysql-server/root_password_again password $MYSQL_ROOT" | debconf-set-selections
    #
    # # Install required packages non-interactive
    # DEBIAN_FRONTEND=noninteractive apt-get install -y \
    # apache2 libapache2-mod-wsgi mysql-server libav-tools mediainfo pacpl icecast2 \
    # python-dev python-pip python-mysqldb python-dbus python-gst0.10 \
    # gstreamer0.10-plugins-good gstreamer0.10-plugins-bad \
    # gstreamer0.10-plugins-ugly gstreamer0.10-tools
    #
    # # Install/upgrade virtualenv
    # pip install -U virtualenv
    #
    # # Create the virtual environment
    # virtualenv --system-site-packages $VENV_PATH
    #
    # # Activate the environment
    # source $VENV_PATH/bin/activate
    # # Set python path to use production code
    # export PYTHONPATH=$CODE_PATH
    #
    # # Setup MySQL database
    # echo "create database IF NOT EXISTS roundware;" | mysql -uroot -p$MYSQL_ROOT
    # echo "grant all privileges on roundware.* to 'round'@'localhost' identified by 'round';" | mysql -uroot -p$MYSQL_ROOT
    #
    # # File/directory configurations
    # mkdir -p $MEDIA_PATH
    # mkdir -p $STATIC_PATH
    #
    # # copy test audio file to media storage
    # cp $SOURCE_PATH/files/rw_test_audio1.wav $MEDIA_PATH
    #
    # # Copy default production settings file
    # mkdir $WWW_PATH/settings
    # cp $SOURCE_PATH/files/var-www-roundware-settings.py $WWW_PATH/settings/roundware_production.py
    # chown $USERNAME:$USERNAME -R $WWW_PATH/settings
    #
    # # Setup roundware log and logrotate
    # touch /var/log/roundware
    # chown $USERNAME:$USERNAME /var/log/roundware
    #
    # # Run the production upgrade/deployment script
    # $SOURCE_PATH/deploy.sh
    #
    # # Setup Apache Server
    # a2enmod rewrite
    # a2enmod wsgi
    # a2enmod headers
    # a2dissite 000-default
    # # Setup roundware in Apache
    # rm -f /etc/apache2/sites-available/roundware.conf
    # sed s/USERNAME/$USERNAME/g $CODE_PATH/files/etc-apache2-sites-available-roundware > /etc/apache2/sites-available/roundware.conf
    # a2ensite roundware
    #
    # # Setup logrotate
    # sed s/USERNAME/$USERNAME/g $CODE_PATH/files/etc-logrotate-d-roundware > /etc/logrotate.d/roundware
    #
    # # Install correct shout2send gstreamer plugin
    # mv /usr/lib/x86_64-linux-gnu/gstreamer-0.10/libgstshout2.so /usr/lib/x86_64-linux-gnu/gstreamer-0.10/libgstshout2.so.old
    # cp $CODE_PATH/files/64-bit/libgstshout2.so /usr/lib/x86_64-linux-gnu/gstreamer-0.10/libgstshout2.so
    #
    # # Set $USERNAME to own all files
    # chown $USERNAME:$USERNAME -R $HOME_PATH
    #
    # # Setup the default admin account
    # su - $USERNAME -c "$CODE_PATH/roundware/manage.py loaddata default_auth.json"
    #
    # # Setup the sample project
    # su - $USERNAME -c "$CODE_PATH/roundware/manage.py loaddata sample_project.json"
    #
    # service apache2 restart
    #
    # # Setup icecast
    # cp $CODE_PATH/files/etc-default-icecast2 /etc/default/icecast2
    # cp $CODE_PATH/files/etc-icecast2-icecast.xml /etc/icecast2/icecast.xml
    # service icecast2 restart
    #
    # echo "Install Complete"


@task
def setup_postgis():
    """
    makes sure postgres is installed along with PostGIS and its requirements

    :return:
    """

    cuisine.package_update()
    cuisine.package_upgrade()
    cuisine.package_ensure(POSTGIS_PACKAGES)
    fabtools.require.postgres.user(env.user, env.password)
    fabtools.require.postgres.database("roundware", env.user)
    fabtools.postgres._run_as_pg("psql -U postgres roundware -c 'create extension if not exists postgis;'")
    fabtools.postgres._run_as_pg("psql -U postgres roundware -c 'grant all on database roundware to {user};'".format(user=env.user))

@task
def deploy():
    """
    deploys the code to the instance
    :return:
    """

    if not fabtools.files.is_dir(CODE_PATH):
        fabtools.files.symlink(CODE_PATH, CODE_PATH)

    # Install upgrade pip
    virtualenv('pip install -U pip')

    # Install and upgrade RoundWare requirements
    virtualenv('pip install -r {requirements} --upgrade'.format(requirements=CODE_PATH + '/requirements.txt'))

    # Apply patch to fix M2M field deserializing for Tag relationships, force command to return true.
    # Details: https://code.djangoproject.com/ticket/17946
    # TODO: Remove when fixed in Django core, probably when upgrading to Django 1.8.
    patch(
        os.path.join(WWW_PATH, "/lib/python2.7/site-packages/django/core/serializers/python.py"),
        os.path.join(CODE_PATH, "/files/fix-m2m-deserial.patch")
    )

    sudo('export PYTHONPATH=$PYTHONPATH:$CODE_PATH')

    # Set $USERNAME to own all files
    sudo('chown {user}:{group} -R {path}'.format(user=env.user, group=env.user, path=WWW_PATH))

    manage_py("migrate --noinput")
    manage_py("collectstatic --noinput")

    sudo("service apache2 restart")

    print "Deploy Complete"
