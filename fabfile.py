import os
from fabric.contrib.files import sed, append
import fabtools
from fabric.api import *
from fabtools.files import copy
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
THIS_DIR = os.path.dirname(__file__)

REQUIRED_PACKAGES = [
    "apache2",
    "libapache2-mod-wsgi",
    "mysql-server",
    "libav-tools",
    "mediainfo",
    "pacpl",
    "icecast2",

    #system
    'build-essential',
    'git',

    # python
    'python-pip',
    'python-virtualenv',
    'python-dev',
    'virtualenvwrapper',
    "python-dbus",
    "python-gst0.10",

    "gstreamer0.10-plugins-good",
    "gstreamer0.10-plugins-bad",
    "gstreamer0.10-plugins-ugly",
    "gstreamer0.10-tools"
]

# DEV_CODE_PATH="$HOME_PATH/roundware-server"
#
# WWW_PATH="/var/www/roundware"
# CODE_PATH="$WWW_PATH/source"
STATIC_PATH = os.path.join(WWW_PATH, "static")
MEDIA_PATH = os.path.join(WWW_PATH, "rwmedia")

# VENV_PATH="$WWW_PATH"
# SITE_PACKAGES_PATH="$VENV_PATH/lib/python2.7/site-packages"

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


def setup_webserver():
    """
    configures apache to serve RW
    :return:
    """
    # TODO why not use nginx?
    # # Setup Apache Server

    run("a2enmod rewrite")
    run("a2enmod wsgi")
    run("a2enmod headers")
    run("a2dissite 000-default")

    # configure Apache to serve RW directory

    # Setup roundware in Apache
    config_template = open(THIS_DIR + "/files/rw_apache.conf").readall()

    format_config_file(config_template, "/etc/apache2/sites-available/roundware.conf", {'user': env.user})

    run("a2ensite roundware")

@task
def setup_logrotate():
    """
    sets up logrotate
    """
    # make sure logfile is present and owned by user
    cuisine.file_ensure('/var/log/roundware', owner=env.user, group=env.user)
    logrotate_template = CODE_PATH + "/files/roundware_logrotate_template"
    format_config_file(logrotate_template, '/etc/logrotate.d/roundware', {'user': env.user})

@task
def localhost(user='roundware'):
    """
    set environment variables for localhost
    """
    env.hosts = ['localhost']
    env.host_string = 'localhost'

    env.user = user
    password = 'vagrant' if user == 'vagrant' else PASSWORD

    env.loginpassword = password
    env.password = password


def format_config_file(template, destination, format_dict):
    template_content = open(template).readall()

    rendered_template_content = template_content.format(**format_dict)
    template_content.close()

    rendered_template_path = template.replace("_template", "")
    run("rm -f {0}".format(rendered_template_path))
    cuisine.file_ensure(rendered_template_path)
    cuisine.file_append(rendered_template_path, rendered_template_content)
    cuisine.file_link(rendered_template_path, destination)


@task
def install_roundware():
    """
    installs roundware on the server
    :return:
    """

    if env.user == 'vagrant':
        dev_code_path = "/vagrant"
    else:
        dev_code_path = "/var/www/roundware/source"

    # if [ ! "$FOUND_VAGRANT" = true ]; then
    #
    #   # If user home doesn't exist, create the user.
    #   if [ ! -d "/home/$USERNAME" ]; then
    #     useradd $USERNAME -s /bin/bash -m -d $HOME_PATH
    #   fi

    fabtools.require.directory(WWW_PATH, use_sudo=True, owner=env.user, group=env.user)

    cuisine.file_link(WWW_PATH, "/home/{user}/www".format(user=env.user))

    # update and upgrade default system packages
    cuisine.package_update()
    cuisine.package_upgrade()

    # install system packages
    cuisine.package_ensure(" ".join(REQUIRED_PACKAGES))

    # make sure pip is most recent version
    sudo("pip install -U pip")

    cuisine.python_package_ensure('virtualenv')
    sudo('virtualenv --system-site-packages {path}'.format(path=VENV_PATH))

    # install postgis and create database
    setup_postgis()


    cuisine.dir_ensure(MEDIA_PATH, recursive=True, owner=env.user)
    cuisine.dir_ensure(STATIC_PATH, recursive=True, owner=env.user)

    cuisine.file_link(CODE_PATH + "/files/var-www-roundware-settings.py", WWW_PATH + "/settings/roundware_production.py")

    # Run the production upgrade/deployment script
    deploy()

    setup_webserver()

    install_gstreamer_plugin()

    # copy test audio file to media storage
    cuisine.file_link(CODE_PATH + "/files/rw_test_audio1.wav", MEDIA_PATH)

    # env.user should own all files at home
    cuisine.dir_attribs("~", owner=env.user, group=env.user)

    manage_py("loaddata default_auth.json")
    manage_py("loaddata sample_project.json")

    setup_icecast()
    run("service apache2 restart")
    run("service icecast2 restart")

    # Replace the user's .profile
    run("rm -f ~/.profile")
    cuisine.file_link(os.path.join(dev_code_path, "files/home-user-profile"), "~/.profile")

    print "Install Complete"

@task
def install_gstreamer_plugin():
    plugin = "/usr/lib/x86_64-linux-gnu/gstreamer-0.10/libgstshout2.so"
    cuisine.file_backup(plugin, suffix=".old")
    cuisine.file_link(CODE_PATH + "/files/64-bit/libgstshout2.so", plugin)

@task
def setup_icecast():
    """
    sets up icecast2
    :return:
    """
    cuisine.file_link(CODE_PATH + "files/etc-default-icecast2", '/etc/default/icecast2')
    cuisine.file_link(CODE_PATH + "etc-icecast2-icecast.xml", '/etc/icecast2/icecast.xml')
    run("service icecast2 restart")


@task
def setup_postgis():
    """
    makes sure postgres is installed along with PostGIS and its requirements

    :return:
    """

    cuisine.package_update()
    cuisine.package_upgrade()
    cuisine.package_ensure(" ".join(POSTGIS_PACKAGES))
    fabtools.require.postgres.user(env.user, "round")
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
        fabtools.files.symlink(CODE_PATH, _PATH)

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
