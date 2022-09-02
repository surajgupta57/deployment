### Table of Contents

- [Requirements](#requirements)
- [Development Environment](#development-environment)
  * [AutoFormatter](#autoformatter)
  * [Linter](#linter)
- [Project Setup](#project-setup)
  * [Dependencies](#dependencies)
  * [Database](#database)
  * [Environment Variables](#environment-variables)
  * [Create Superuser](#create-superuser)
  * [Runserver command](#runserver-command)
- [Elasticsearch](#elasticsearch)
  * [Installation](#installation)
  * [Requirements](#requirements-1)
- [External Services](#external-services)
  * [Email Campaigns](#email-campaigns)
- [Contribution Guidelines](#contribution-guidelines)
  * [General Guidelines](#general-guidelines)
  * [Commit Guidelines](#commit-guidelines)
  * [Branch Guidelines](#branch-guidelines)


### Requirements

- **Python** : 3.7.x
- **PostgreSQL** : v11.8


### Development Environment

#### AutoFormatter
We use autopep8 as the python autoformatter, install it as follows:

```bash
pip install pep8   
```

To configure it in VSCode, read [this guide](https://donjayamanne.github.io/pythonVSCodeDocs/docs/formatting/).

#### Linter
We use flake8 as the linter, install it as follows:

```bash
pip install flake8
```

To configure it in VSCode, read [this guide](https://donjayamanne.github.io/pythonVSCodeDocs/docs/linting/#Flake8).


### Project Setup

First create a virtual environment locally using Python 3.7

```bash
python3 -m venv venv

```

Then activate the virtual environment as follows:

```bash
source venv/bin/activate
````

then First clone this Repository locally using the following command

```bash
git clone https://github.com/Ezyschooling/ezyadmissions-back.git
```

and then go into project folder

```bash
cd ezyadmissions-back
```

#### Dependencies

After that you need to install all the requirements, the requirements can be installed using

```bash
pip install -r requirements/local.txt
```

#### Database

Let's first install PostgreSQL on our system:

```bash
sudo apt install postgresql postgresql-contrib
```

First install the distro packages required:

```bash
sudo apt-get install libpq-dev
```

Then to compile psycopg2 from source you'll need gcc which can be installed as follows:

```bash
sudo apt install build-essential
```

Then install the python packages required for adding PostgreSQL support in django:

```bash
pip install psycopg2-binary
```

#### Environment Variables

Most of the project settings are configured using [environment variables](https://www.geeksforgeeks.org/environment-variables-in-linux-unix/), a python package is used to read these variables from `.env` file present in the project directory instead.

Run the following command:

```bash
cp .env.example .env
```

The important environment variables that you should be focusing for getting your project running is:

`DATABASE_URL`, it contains the information required to configure the database for the project.

It's syntax is :

```
postgres://db_user:db_password@db_host:db_port/db_name
```

Configure this value in the `.env` file.

Now you need to migrate to apply all the changes to new database, it can be done using following command

```
python manage.py migrate
```


#### Create Superuser

Now you need to create a Superuser to do all admin tasks, you can create it using

```
python manage.py createsuperuser
```


#### Runserver command

Now you can runserver locally using

```
python manage.py runserver
```



### Elasticsearch
Elasticsearch has been used in the project to implement search functionality, it has been used in the `articles`, `discussions`, `news` and `videos` app to create an API endpoint that allows searching through the data from the respective models.

To work with those app without installing Elasticsearch, you can use the trick mentioned below:
When working with `articles`, `discussions`, `news`, `videos` or `schools` app, whenever you're trying to add data to any of the tables, comment out the [following line](./ezyschoolingbackend/backend/settings/base.py#L83) in `base.py` settings file, this will disable the elasticsearch documents from being created.


#### Installation
If you'd like to work on the search API Views for the above mentioned apps, then you'll need to install Elasticsearch locally, which can be done using docker-compose.

#### Requirements
- **Docker** : Install it for the OS you're using, by following [this guide](https://docs.docker.com/engine/install/).
- **Docker Compose** : Install it for the OS you're using, by following [this guide](https://docs.docker.com/compose/install/)

When you're done installing docker and docker-compose, follow the below steps:

```bash
cd elasticsearch/
docker-compose up -d
```

### External Services

#### Email Campaigns
Contacts of the all signed up parents on website gets updated in the Email Campaign Service's contact list being used, currently Freshmarketer is being used, which requires the following environment variables to be configured:
- `FRESHMARKETER_API_KEY`
- `FRESHMARKETER_LIST_ID`

These can be obtained from the Freshmarketer dashboard.  
Documentation for Freshmarketer API is available at [https://developer.freshmarketer.com/](https://developer.freshmarketer.com/).  
Celery tasks are configured for these API calls, which are defined in the [newsletters/tasks.py](./ezyschoolingbackend/newsletters/tasks.py).

### Contribution Guidelines

#### General Guidelines
Always provide documentation with code and use python docstrings with every module, funtions, classes to understand code properly.

#### Commit Guidelines
Use proper commit message with every commits so that it is understandable what you are trying to accomplish.

#### Branch Guidelines
- Never push to stable, all work should be done on separate branches, and Pull Request needs to opened to the `stable` branch.
- When working on a feature, branch off from `stable`, the branch name should follow the format `feat/feature-name`.
- When working on a fix that needs to be deployed, branch off from `stable`, the branch name should follow the format `fix/fix-name`.
