sudo apt update
sudo apt install python3-pip python3-dev nginx
sudo pip3 install virtualenv
mkdir ~/projectdir
cd ~/projectdir
virtualenv env
source env/bin/activate
ls
pip install django gunicorn
ls
django-admin startproject textutils ~/projectdir
ls
sudo nano textutils/settings.py 
~/projectdir/manage.py makemigrations
~/projectdir/manage.py migrate
~/projectdir/manage.py runserver 0.0.0.0:8000
sudo ufw allow 8000
~/projectdir/manage.py runserver 0.0.0.0:8000
gunicorn --bind 0.0.0.0:8000 textutils.wsgi
deactivate
sudo vim /etc/systemd/system/gunicorn.socket
sudo vim /etc/systemd/system/gunicorn.service
sudo systemctl start gunicorn.socket
sudo systemctl enable gunicorn.socket
sudo apt update
sudo vim /etc/nginx/sites-available/textutils
sudo ln -s /etc/nginx/sites-available/textutils /etc/nginx/sites-enabled/
sudo systemctl restart nginx
sudo systemctl restart gunicorn
sudo vim /etc/nginx/sites-available/textutils
sudo systemctl restart nginx
sudo systemctl restart gunicorn
ls
sudo nano textutils/settings.py 
sudo systemctl restart nginx
sudo systemctl restart gunicorn
sudo vim /etc/nginx/sites-available/textutils
sudo vim /etc/systemd/system/gunicorn.service
pwd
sudo vim /etc/systemd/system/gunicorn.service
sudo vim /etc/nginx/sites-available/textutils
sudo vim /etc/systemd/system/gunicorn.service
sudo systemctl start gunicorn.socket
sudo systemctl enable gunicorn.socket
sudo systemctl restart nginx
gunicorn --bind 0.0.0.0:8000 textutils.wsgi:application
pip install gunicorn
gunicorn --bind 0.0.0.0:8000 textutils.wsgi:application
sudo apt install gunicorn
gunicorn --bind 0.0.0.0:8000 textutils.wsgi:application
gunicorn --bind 0.0.0.0:8000 textutils.wsgi.application
gunicorn --bind 0.0.0.0:8000 textutils.wsgi:application
source env/bin/activate
pip install gunicorn
gunicorn --bind 0.0.0.0:8000 textutils.wsgi:application
deactivate
sudo systemctl restart nginx
sudo systemctl restart gunicorn
ls
cd 
ls
pwd
cd projectdir/
pwd
sudo vim /etc/systemd/system/gunicorn.service
sudo systemctl start gunicorn.socket
sudo systemctl enable  gunicorn.socket
source env/bin/activate
sudo vim /etc/nginx/sites-available/textutils
deactivatesudo systemctl start gunicorn.socket
sudo systemctl enable gunicorn.socket
sudo systemctl start gunicorn.socket
sudo systemctl enable gunicorn.socket
sudo systemctl restart nginx
celery -A proj worker
deactivate
sudo apt-get install redis-server
redis-cli ping 
sudo systemctl enable redis-server.service
source env/bin/activate
ls
ls -a
sudo nano gunicorn_start.bash
chmod u+x gunicorn_start.bash
sudo chmod u+x gunicorn_start.bash
./gunicorn_start.bash
sudo ./gunicorn_start.bash
ls
sudo chmod u+x gunicorn_start.bash
sudo nano gunicorn_start.bash
sudo ./gunicorn_start.bash
deactivate
activate
sudo apt-get install supervisor
cd /etc/supervisor/conf.d
ls
sudo nano gunicorn.conf
sudo nano celery_beat.conf
sudo nano celery_worker.conf
ls
sudo supervisorctl reread
sudo nano gunicorn.conf
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl start all
sudo supervisorctl status textutils
sudo supervisorctl status all
sudo nano gunicorn.conf
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl start all
sudo supervisorctl status all
sudo nano celery_beat.conf
sudo nano celery_beat.conf 
sudo nano celery_worker.conf 
sudo nano celery_beat.conf 
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl start all
sudo nano celery_worker.conf 
sudo nano celery_beat.conf 
sudo supervisorctl start all
ls
sudo nano celery_beat.conf 
sudo nano celery_worker.conf 
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl start all
sudo supervisorctl start
sudo supervisorctl start all
sudo nano celery_worker.conf 
sudo nano celery_beat.conf 
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl start all
sudo supervisorctl status all
sudo nano celery_worker.conf 
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl start all
sudo nano celery_beat.conf 
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl start all
sudo supervisorctl status all
sudo nano celery_beat.conf 
sudo nano celery_worker.conf 
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl start all
sudo nano celery_worker.conf 
sudo nano celery_beat.conf 
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl start all
sudo nano celery_beat.conf 
sudo nano celery_worker.conf 
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl start all
sudo supervisorctl status all
cd 
cd projectdir/
source env/bin/activate
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl start all
sudo supervisorctl status all
pip install celery
sudo supervisorctl update
sudo supervisorctl start all
sudo supervisorctl status all
sudo nano celery_beat.conf 
cd /etc/supervisor/conf.d
sudo nano celery_beat.conf 
sudo nano celery_worker.conf 
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl start all
sudo supervisorctl status all
sudo apt-get install nginx
cd
cd projectdir/
sudo update-rc.d nginx defaults
cd ~/etc/nginx/conf.d
cd /etc/nginx/conf.d
sudo nano textutils.conf
sudo service nginx restart
cd 
cd projectdir/
sudo service nginx restart
pwd
csu 
su
su -
exit
cd
cd projectdir/
cd textutils/
pwd
cd ..
ls
ls -a
sudo mkdir logs
ls
sudo mkdir logs/celery
ls
sudo mkdir logs/gunicorn
cd logs/celery/
ls
cd ..
sudo touch celery.log celery.err.log celery-beat.log celery-beat.err.log
ls
cd ..
sudno nano manage.py 
sudo nano manage.py 
pwd
sudo supervisorctl stop all
cd
cd /etc/nginx/conf.d
ls
sudo cp textutils.conf ~/home/ubuntu/deployment
sudo cp textutils.conf /home/ubuntu/deployment
cd 
cd /etc/supervisor/conf.d
ls
sudo cp . /home/ubuntu/deployment
sudo cp * /home/ubuntu/deployment
cd 
ls
cd projectdir/
ls
sudo cp gunicorn_start.bash /home/ubuntu/deployment
cd 
ls
sudo apt update
sudo apt install python3-venv python3-dev libpq-dev postgresql postgresql-contrib nginx curl
sudo -u postgres psql
ls
sudo mkdir ~/ezyschooling
cd ezyschooling/
python3 -m venv venv
sudo python3 -m venv venv
ls
source venv/bin/activate
git clone https://github.com/Ezyschooling/ezyadmissions-back.git
sudo git clone https://github.com/Ezyschooling/ezyadmissions-back.git
ls
cd ezyadmissions-back/
ls
cd ..
sudo cp -r ezyadmissions-back/* .
ls
sudo rm -r ezyadmissions-back
ls
cd /etc/supervisor/conf.d
ls
cd
ls
cd ezyschooling/
ls
cd requirements/
sudo nano req.txt
pip install -r req.txt 
cd ..
git clone https://github.com/Alexmhack/django_postgresql.git
ls
cd django_postgresql/
ls
deactivate
python3 -m venv env
source env/bin/activate
ls
cd blog
ls
sudo nano settings.py 
cd ..
python manage.py migrate
pip install django
pip install psycopg2-binary
python manage.py migrate
sudo nano blog/settings.py 
ls
sudo nano blog/settings.py 
python manage.py makemigrations
deactivate
source env/bin/activate
python manage.py makemigrations
pip freeze > requirements.txt

sudo nano requirements.txt 
ls
cd
ls
cd djn
cd django_postgresql/
source env/bin/activate
pip install django
pip install -r requirements.txt 
ls
python manage.py runserver 0.0.0.0:8001
sudo nano blog/settings.py 
ls
python manage.py makemigrations
sudo nano blog/settings.py 
python manage.py makemigrations
sudo nano blog/settings.py 
python manage.py makemigrations
sudo nano blog_list/migrations/0003_alter_blog_published_date.py 
cd  blog_list/migrations/
ls
sudo rm -r 0001_initial.py 0002_alter_blog_published_date.py 0003_alter_blog_published_date.py 
ls
cd ..
sudo nano models.py 
cd ..
python manage.py makemigrations
python manage.py migrate
cd 
cd django_postgresql/
source env/bin/activate
python manage.py runserver 0.0.0.0:8001
sudo ufw allow 8001
python manage.py runserver 0.0.0.0:8001
gunicorn --bind 0.0.0.0:8001 blog.wsgi
pip install django gunicorn
gunicorn --bind 0.0.0.0:8001 blog.wsgi
pip install django
pip install gunicorn
gunicorn --bind 0.0.0.0:8001 blog.wsgi
ls
gunicorn --bind 0.0.0.0:8001 Blo.wsgi
gunicorn --bind 0.0.0.0:8001 Blog.wsgi
gunicorn --bind 0.0.0.0:8001 blog.wsgi
pip freeze
deactivate 
source env/bin/activate
gunicorn --bind 0.0.0.0:8001 blog.wsgi
cd /etc/nginx/conf.d
ls
sudo nano blog.conf
cd ../../
cd supervisor/conf.d/
ls
sudo nano gunicorn.conf 
sudo nano celery_worker.conf 
sudo nano celery_beat.conf 
cd
ls
cd projectdir/
ls
cd ../django_postgresql/
sudo nano gunicorn_start.bah
sudo nano gunicorn_start.bash
chmod u+x gunicorn_start.bash
sudo chmod u+x gunicorn_start.bash
./gunicorn_start.bash
sudo ./gunicorn_start.bash
sudo supervisorctl reread
ls
sudo mkdir logs
sudo supervisorctl reread
sudo mkdir logs/gunicorn
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl start all
deactivate 
sudo supervisorctl start all
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl start all
cd /etc/supervisor/conf.d
sudo supervisorctl start all
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl start all
sudo nano /etc/systemd/system/gunicorn.service
sudo supervisorctl start all
sudo ./gunicorn_start.bash
sudo supervisorctl reread
sudo nano gunicorn.conf 
sudo nano celery_worker.conf 
sudo nano celery_beat.conf 
cd ../..//nginx/conf.d/
ls
cd ../../supervisor/.con
cd ../../supervisor/conf.d/
sudo supervisorctl reread
sudo nano celery_worker.conf 
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl start all
sudo nano celery_worker.conf 
sudo nano celery_beat.conf 
sudo nano gunicorn.conf 
ls
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl start all
sudo nano celery_worker.conf 
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl start all
sudo nano celery_worker.conf 
sudo systemctl start gunicorn.socket
sudo systemctl enable gunicorn.socket
sudo vim /etc/nginx/sites-available/textutils
sudo ln -s /etc/nginx/sites-available/blog /etc/nginx/sites-enabled/
sudo systemctl restart nginx
sudo vim /etc/nginx/sites-available/blog
sudo ln -s /etc/nginx/sites-available/textutils /etc/nginx/sites-enabled/
sudo systemctl restart nginx
sudo supervisorctl start all
sudo systemctl restart gunicorn
systemctl status gunicorn.service
cd ../../nginx/conf.d/
ld
ls
cd ../../supervisor/conf.d/
ls
sudo nano gunicorn.conf 
sudo nano celery_worker.conf 
sudo nano celery_beat.conf 
cd ../../nginx/conf.d/
sudo nano blog.conf 
sudo vim /etc/nginx/sites-available/blog 
cd 
cd django_postgresql/
sudo chmod u+x gunicorn_start.bash
sudo ./gunicorn_start.bash
sudo nano ./gunicorn_start.bash
sudo ./gunicorn_start.bash
./gunicorn_start.bash
sudo apt-get install supervisor
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl start all
sudo supervisorctl stop all
sudo supervisorctl start all
sudo supervisorctl restart all
sudo update-rc.d nginx defaults
sudo service nginx restart 
sudo service nginx restart sudo systemctl start gunicorn.socket
sudo systemctl enable gunicorn.socket
sudo apt update
sudo systemctl restart nginx
gunicorn blog.wsgi:application --bind 8001
gunicorn blog.wsgi:application --bind :8001
source env/bin/activate
gunicorn blog.wsgi:application --bind :8001
gunicorn blog.wsgi:application --bind 8001
python manage.py runserver 0.0.0.0:8001
ls
gunicorn blog.wsgi:application --bind 8001
gunicorn --bind 0.0.0.0:8001 blog.wsgi
gunicorn --bind 0.0.0.0:8001 blog.wsgi.application
gunicorn blog.wsgi:application --bind 0.0.0.0:8001
ps -ax
netstat -tulpn | grep 8001
sudo apt install net-tools
netstat -tulpn | grep 8001
kill `lsof -i :8001`
ps -ax |grep gunicorn
kill 13165
ps -ax |grep gunicorn
gunicorn blog.wsgi:application --bind 0.0.0.0:8001
ps -ax |grep gunicorn
gunicorn --bind 0.0.0.0:8001 blog.wsgi.application
netstat -tulpn | grep 8001
ps -aux
sudo fuser -k 8001/tcp
sudo fuser -k 8000/tcp
gunicorn --bind 0.0.0.0:8001 blog.wsgi.application
gunicorn --bind 0.0.0.0:8001 blog.wsgi
python manage.py collectstatic
sudo systemctl enable redis-server.service
sudo ./gunicorn_start.bash
sudo supervisorctl reread
deactivate 
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl start all
sudo supervisorctl status all
pip install celery
sudo supervisorctl update
sudo supervisorctl status all
source env/bin/activate
pip install celery
sudo supervisorctl update
sudo supervisorctl reread
sudo supervisorctl start all
sudo supervisorctl status all
sudo ./gunicorn_start.bash
sudo supervisorctl start all
deactivate 
sudo update-rc.d nginx defaults
sudo service nginx restart 
sudo service nginx restart sudo vim /etc/systemd/system/gunicorn.service
sudo vim /etc/systemd/system/gunicorn.service
sudo systemctl start gunicorn.socket
sudo systemctl enable gunicorn.socket
sudo vim /etc/nginx/sites-available/blog
sudo ln -s /etc/nginx/sites-available/textutils /etc/nginx/sites-enabled/
sudo systemctl restart nginx
sudo systemctl restart gunicorn
source env/bin/activate
python manage.py collectstatic
sudo systemctl restart nginx
sudo systemctl restart gunicorn
sudo systemctl start gunicorn.socket
sudo systemctl enable gunicorn.socket
deactivate 
sudo systemctl restart nginx
sudo systemctl restart gunicorn
sudo nano blog/settings.py 
python manage.py collectstatic
souce env/bin/activate
source env/bin/activate
python manage.py collectstatic
sudo systemctl restart nginx
sudo systemctl restart gunicorn
sudo vim /etc/nginx/sites-available/blog
sudo systemctl restart nginx
deactivate 
sudo systemctl restart nginx
sudo systemctl restart gunicorn
souce env/bin/activate
source env/bin/activate
python manage.py collectstatic
deactivate 
sudo systemctl start gunicorn.socket
sudo systemctl enable gunicorn.socket
sudo systemctl restart nginx
sudo systemctl restart gunicorn
exit
cd
ls
cd django_postgresql/
pwd
ls
cd staticfiles/
ls
cd ../staticfiles/
ls
pwd
exit
cd
cd django_postgresql/ 
pwd
ufw allow 8002
su -
exit
cd
cd /etc/nginx/sites-available/
ls
sudo nano blog 
cd
cd django_postgresql/
sudo nano blog/settings.py 
source env/bin/activate
python manage.py collectstatic
cd /etc/nginx/sites-available/
sudo nano blog 
cd
cd django_postgresql/
sudo nano blog/settings.py 
python manage.py collectstatic
sudo service nginx restart
cd /etc/nginx/sites-available/
sudo nano blog 
sudo service nginx restart
cd
cd django_postgresql/
python manage.py collectstatic
cd /etc/nginx/sites-available/
sudo nano blog 
cd
cd django_postgresql/
python manage.py collectstatic
cd /etc/nginx/sites-available/
sudo nano blog 
cd
cd django_postgresql/
python manage.py collectstatic
sudo service nginx restart
python manage.py runserver 0.0.0
python manage.py runserver 0.0.0.0:8000
python manage.py runserver 0.0.0.0:8001
python manage.py runserver 0.0.0.0:8002
sudo service nginx gunicorn
sudo service gunicorn restart
sudo nano blog/settings.py 
python manage.py collectstatic
sudo service gunicorn restart
sudo service nginx gunicorn
sudo service nginx restart
cd /etc/nginx/sites-available/
sudo nano blog 
sudo service nginx restart
cd
cd django_postgresql/
python manage.py collectstatic
sudo nano blog/settings.py 
cd /etc/nginx/sites-available/
sudo nano blog 
cd
cd django_postgresql/
python manage.py collectstatic
sudo nano blog/settings.py 
python manage.py collectstatic
sudo nano blog/settings.py 
python manage.py collectstatic
cd /etc/nginx/sites-available/
sudo nano blog 
cd
cd django_postgresql/
python manage.py collectstatic
sudo service nginx restart
clear
docker
deactivate 
exit
cd
cd django_postgresql/
source env/bin/activate
ls
cd static
ls
cd ../staticf
cd ../staticfiles/
ls
sudo nano README.txt 
cd
cd django_postgresql/
source env/bin/activate
ls
sudo nano blog/settings.py 
python manage.py collectstatic
sudo nano blog/settings.py 
python manage.py collectstatic
sudo nano blog/settings.py 
python manage.py collectstatic
cd /etc/nginx/sites-available/
sudo nano blog 
sudo service nginx restart
cd 
cd django_postgresql/
python manage.py collectstatic
sudo chmod -R 777 static
ls
cd
ls
git clone https://github.com/surajgupta57/prod-deploy.git
git switch master
cd prod-deploy/
git switch master
ls
python
sudo apt update
sudo apt install python3
python
python3
pip install virtualenv
python3 -m virtualenv venv
source venv/bin/activate
pip install requirements/local.txt 
pip install -r requirements/local.txt 
sudo su - postgres
python manage.py runserver
export DATABASE_URL=postgres://postgres:Admin@123@localhost:5432/proddeploy
docker compose -f local.yml config
sudo apt install docker.io
docker compose -f local.yml config
docker compose -f local.yml up --build -d --remove-orphans
docker compose -f local.yml up --build -d --remove-orphans --help
docker compose -f local.yml config --help
docker compose local.yml config --help
docker-compose local.yml config
sudo apt install docker-compose
docker-compose local.yml config
docker compose -f local.yml config
docker-compose -f local.yml config
cd docker compose -f local.yml up --build -d --remove-orphans
cd /home/delta/prod-deploy/docker/local/
ls
cd ..
git pull origin master
cd docker/
cd local/
ls
cd../..
cd ../..
docker-compose -f local.yml config
cd docker compose -f local.yml up --build -d --remove-orphans
cd docker-compose -f local.yml up --build -d --remove-orphans
cd docker compose -f local.yml up --build -d --remove-orphans
docker compose -f local.yml up --build -d --remove-orphans
docker-compose -f local.yml up --build -d --remove-orphans
sudo docker-compose -f local.yml up --build -d --remove-orphans
git pull origin master
sudo docker-compose -f local.yml up --build -d --remove-orphans
ps
ps -a
sudo docker-compose -f local.yml logs
sudo ufw 8000
sudo ufw enable 8000
ufw enable 8000
sudo ufw allow 8000
sudo ufw enable
ec2-18-191-195-223.us-east-2.compute.amazonaws.com
sudo nano /etc/sysctl.conf
sysctl vm.overcommit_memory=1
sudo sysctl vm.overcommit_memory=1
git switch de299da7f88ad819ba316bfaa40b3bcc93d5f0bb
dea
deactivate 
cd ..
git clone https://github.com/surajgupta57/authors-haven-api-live.git
cd authors-haven-api-live/
git switch till-docker 
ls
python3 -m virtualenv venv
python3 -m virtualenv env
ls
sudo rm -r venv
source env/bin/activate
pip install -r requirements/local.txt 
export DATABASE_URL=postgres://postgres:Admin@123@localhost:5432/proddeploy
python3 manage.py runserve
python3 manage.py runserver
export DATABASE_URL=postgres://postgres:Admin@123@localhost:5432/proddeploy
python3 manage.py runserver
psql -U postgres
postgres -i -u 
sudo systemctl start postgresql.service
sudo -i -u postgres
python3 manage.py runserver
export DATABASE_URL=postgres://postgres:Admin@123@localhost:5433/proddeploy
python3 manage.py runserver
export DATABASE_URL=postgres://postgres:Admin@123@localhost:5432/proddeployexport DATABASE_URL=postgres://postgres:Admin@123@localhost:5432/proddeploy
python3 manage.py runserver
export DATABASE_URL=postgres://postgres:Admin@123@localhost:5432/proddeploy
docker-compose -f local.yml config
sudo docker-compose -f local.yml up --build -d --remove-orphans
docker-compose -f local.yml logs
sudo docker-compose -f local.yml logs
sudo docker compose -f local.yml logs
sudo docker-compose -f local.yml logs
