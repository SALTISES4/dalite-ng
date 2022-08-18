# Dalite NG

[![SALTISES4](https://circleci.com/gh/SALTISES4/dalite-ng.svg?style=svg)](https://app.circleci.com/pipelines/github/SALTISES4/dalite-ng)

Dalite NG is a Peer Instruction Tool for online learning platforms such as Open edX. It is implemented in Django as an [LTI](https://en.m.wikipedia.org/wiki/Learning_Tools_Interoperability) tool and should be compatible with most online learning platforms. Dalite NG is a rewrite of the [Dalite tool][old-dalite] as a cleaner, Django-based LTI tool.

[old-dalite]: https://github.com/open-craft/edu8-dalite/

## Setting up the development server

1.  Install the requirements (you probably want to set up a virtualenv first).
    using `pip-tools`
    $ pip install pip-tools
    $ pip-sync requirements/requirements-base.txt

2.  Set up the database connection. The default configuration is to use the
    MySQL database `dalite_ng` and the user `dalite`. To set up the database,
    run these commands as the MySQL superuser:

         mysql> CREATE DATABASE dalite_ng;
         mysql> CREATE USER 'dalite'@'localhost' IDENTIFIED BY 'your password here';
         mysql> GRANT ALL PRIVILEGES ON dalite_ng.* TO 'dalite'@'localhost';
         mysql> GRANT ALL PRIVILEGES ON test_dalite_ng.* TO 'dalite'@'localhost';

    The password can be passed in the environment:

         $ export DALITE_DB_PASSWORD='your password here'

3.  Generate a secret key, e.g. using `tools/gen_secret_key.py`, an put it in
    `dalite/local_settings.py` along with a `PWD_KEY` and `TOKEN_KEY`.

4.  Create the database tables and the superuser.

        $ ./manage.py migrate
        $ ./manage.py createsuperuser

5.  Run the Django development server.

        $ python -X dev manage.py runserver

6.  Add Sample Consent Form

- Navigate to `127.0.0.1:8000/admin/tos` and add a sample Terms of Service (mark it as current)
- Login as a Teacher

## Front-End Build

#### Packaging of front-end bundles

`npx gulp build`

#### Browserslist (90.22% global coverage: http://browserl.ist/?q=last+3+versions%2C+iOS%3E%3D8%2C+ie+11%2C+not+dead)

['last 3 versions', 'iOS>=8', 'ie 11', 'Safari 9.1', 'not dead']

# Release notes

## Attributions

The thumbs up and down icons were taken from the [Entypo pictograms by Daniel
Bruce][entypo].

[entypo]: http://www.entypo.com/

## Coverage

`$ pytest --cov --cov-report html`

## Celery, beat, and Redis

Requires Redis 5.0.0

- Installation
  (env) $ wget http://download.redis.io/releases/redis-5.0.0.tar.gz
  (env) $ tar xzf redis-5.0.0.tar.gz
  (env) $ cd redis-5.0.0
  (env) $ make

- Start redis
  (env) $ redis-5.0.0/src/redis-server

- Start celery worker (for development)
  (env) $ celery -A dalite worker -l debug

- Start beat scheduler (for development)
  (env) $ celery -A dalite beat -l debug --scheduler django_celery_beat.schedulers:DatabaseScheduler

- Schedule tasks at: /admin/django_celery_beat/

## Translations

`django-admin makemessages -d djangojs -l fr -i=node_modules/* -i=venv* -i=static/CACHE/* -i=static/admin/* -i=*.min.js`:
Javascript

Delete static directory in project root and run:

`django-admin makemessages -d djangojs -l fr -i=node_modules/* -i=venv*`
`django-admin makemessages -l fr -i=node_modules/* -i=venv*`

`../manage.py compilemessages -l fr`

## Tools

`makefile`:
Command shortcuts

`make test`:
Runs pytest with migration and coverage options
`make test-cdb`:
Runs pytest with migration and coverage options, re-creating the db

## ElasticSearch

1. Build the index

`$ ./manage.py search_index --rebuild`

2. Add config to `local_settings.py`:

`ELASTICSEARCH_DSL = { "default": {"hosts": "<username>:<password>@localhost:9200"}, }`

```

## Snyk

Javascript vulnerability dependency scanning via Snyk is incorporated in the CircleCI config. To scan locally, authenticate with your Snyk account and then test:

`npx snyk auth`
`npx snyk test --all-projects` or `npx snyk monitor --all-projects`

Security analysis of application code is available via:

`npx snyk code test`
```
