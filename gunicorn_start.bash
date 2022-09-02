#!/bin/bash

NAME="textutils"                                  							              # Name of the application
DJANGODIR=/home/delta/projectdir             				        # Django project directory
DJANGOENVDIR=/home/delta/projectdir/env            			    # Django project env
SOCKFILE=/home/delta/projectdir/env/run/gunicorn.sock  		  # we will communicte using this unix socket
USER=delta                                        					              # the user to run as
GROUP=delta                                     							            # the group to run as
NUM_WORKERS=3                                    							            # how many worker processes should Gunicorn spawn (2 * CPUs + 1)
DJANGO_SETTINGS_MODULE=textutils.settings             						            # which settings file should Django use
DJANGO_WSGI_MODULE=textutils.wsgi                     						            # WSGI module name

echo "Starting $NAME as `whoami`"

# Activate the virtual environment
cd $DJANGODIR
source env/bin/activate
export DJANGO_SETTINGS_MODULE=$DJANGO_SETTINGS_MODULE
export PYTHONPATH=$DJANGODIR:$PYTHONPATH

# Create the run directory if it doesn't exist
RUNDIR=$(dirname $SOCKFILE)
test -d $RUNDIR || mkdir -p $RUNDIR

# Start your Django Unicorn
# Programs meant to be run under supervisor should not daemonize themselves (do not use --daemon)
exec ${DJANGOENVDIR}/bin/gunicorn ${DJANGO_WSGI_MODULE}:application \
  --name $NAME \
  --workers $NUM_WORKERS \
  --user=$USER --group=$GROUP \
  --bind=unix:$SOCKFILE \
  --log-level=debug \
  --log-file=-



