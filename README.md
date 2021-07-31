Dalite NG
=========

[![TravisCI](https://travis-ci.com/SALTISES4/dalite-ng.svg?branch=master)](https://travis-ci.com/SALTISES4/dalite-ng)

Dalite NG is a Peer Instruction Tool for online learning platforms such as Open edX. It is implemented in Django as an [LTI](https://en.m.wikipedia.org/wiki/Learning_Tools_Interoperability) tool and should be compatible with most online learning platforms.  Dalite NG is a rewrite of the [Dalite tool][old-dalite] as a cleaner, Django-based LTI tool.

[old-dalite]: https://github.com/open-craft/edu8-dalite/

Setting up the development server
---------------------------------

1. Install the requirements (you probably want to set up a virtualenv first).
using `pip-tools`
        $ pip install pip-tools
        $ pip-sync requirements/requirements-base.txt

2. Set up the database connection.  The default configuration is to use the
   MySQL database `dalite_ng` and the user `dalite`.  To set up the database,
   run these commands as the MySQL superuser:

        mysql> CREATE DATABASE dalite_ng;
        mysql> CREATE USER 'dalite'@'localhost' IDENTIFIED BY 'your password here';
        mysql> GRANT ALL PRIVILEGES ON dalite_ng.* TO 'dalite'@'localhost';
        mysql> GRANT ALL PRIVILEGES ON test_dalite_ng.* TO 'dalite'@'localhost';

   The password can be passed in the environment:

        $ export DALITE_DB_PASSWORD='your password here'

3. Generate a secret key, e.g. using `tools/gen_secret_key.py`, an put it in
   `dalite/local_settings.py`.

4. Create the database tables and the superuser.

        $ ./manage.py migrate
        $ ./manage.py createsuperuser

5. Run the Django development server.

        $ ./manage.py runsslserver


6. Add Sample Consent Form

  - Navigate to `127.0.0.1:8000/admin/tos` and add a sample Terms of Service (mark it as current)
  - Login as a Teacher




Front-End Build
---------------

#### Packaging of front-end bundles
./node_modules/gulp/bin/gulp.js build

#### Browserslist (90.22% global coverage: http://browserl.ist/?q=last+3+versions%2C+iOS%3E%3D8%2C+ie+11%2C+not+dead)
['last 3 versions', 'iOS>=8', 'ie 11', 'Safari 9.1', 'not dead']



Setting up a development server in an Open edX Devstack
-------------------------------------------------------
**Note:** This section contains security credentials: dalitepassword, alpha, beta, gamma.  Do **not** use these values on a system open to the Internet! Choose new ones.

* Clone dalite-ng into the "src" directory that comes with the edX Developer Stack. This is the one which gets mounted as /edx/src/ within vagrant; you may need to run `sudo chmod 0777 /edx/src` if you notice permissions issues.

* Start up the VM instance, and add the `dalite` Unix user.
```shell
$ vagrant up && vagrant ssh
vagrant@precise64:~$ sudo useradd -d /home/dalite -m -U -s /bin/bash dalite
```

* Set up MySQL for Dalite.  The default configuration is to use the MySQL database `dalite_ng` and the user `dalite`.
```shell
vagrant$ echo "CREATE DATABASE dalite_ng;
GRANT ALL PRIVILEGES ON dalite_ng.* TO 'dalite'@localhost IDENTIFIED BY 'dalitepassword';
GRANT ALL PRIVILEGES ON dalite_ng.* TO 'dalite'@'%' IDENTIFIED BY 'dalitepassword';" | mysql -u root
```
Check the output of MySQL in case there are any errors.

* Switch to the dalite Unix user and set up the build environment.

```shell
vagrant@precise64:~$ sudo su dalite
dalite$ cd
dalite$ echo "export DALITE_DB_PASSWORD='dalitepassword'" >> ~/.bashrc
dalite$ source ~/.bashrc
dalite$ ln -s /edx/src/dalite-ng dalite-ng
dalite$ virtualenv venv
dalite$ source venv/bin/activate
dalite$ cd dalite-ng
```

* Install the requirements
```shell
dalite$ pip install -r requirements/requirements.txt
```

* Generate a secret key using `tools/gen_secret_key.py`, and put it in `dalite/local_settings.py`.
```shell
dalite$ python tools/gen_secret_key.py >> dalite/local_settings.py
```

* Add the other settings.
```shell
dalite$ echo 'LTI_CLIENT_KEY = "alpha"' >> dalite/local_settings.py
dalite$ echo 'LTI_CLIENT_SECRET = "beta"' >> dalite/local_settings.py
dalite$ echo 'PASSWORD_GENERATOR_NONCE = "gamma"' >> dalite/local_settings.py
```

* Create the database tables and the superuser.
```shell
dalite$ ./manage.py migrate
dalite$ ./manage.py createsuperuser
```

* Start up the Django development server.
```shell
dalite$ ./manage.py runserver 0.0.0.0:8321
```

Usage Example: Configuring Dalite in edX Studio
-----------------------------------------------
This is an example of configuring Dalite as an LTI component in edX Studio. See the [official LTI component instructions](http://edx.readthedocs.org/projects/edx-partner-course-staff/en/latest/exercises_tools/lti_component.html) for further information.

* Go to Dalite at [http://192.168.33.10:8321/admin/](http://192.168.33.10:8321/admin/) and login with the superuser login you created. Note that we use the IP address 192.168.33.10 which is automatically setup for devstacks, so we don't have to fiddle around with port forwarding settings.

* Click "Questions" and create a couple of questions.

* Click "Assignments" and create a new assignment with identifier "assign1". Add the questions previously created to "Chosen questions" for the assignment.

* In another terminal, start up Studio.

```shell
vagrant ssh
vagrant@precise64:~$ sudo su edxapp
edxapp@precise64:~/edx-platform$ paver devstack studio
```

* Go to Studio at [http://localhost:8001/](http://localhost:8001/), login as staff@example.com, click "Advanced Settings", and set or add these settings:
  * Advanced Module List: `[ "lti" ]`.
  * LTI Passports: `[ "dalite:alpha:beta" ]`.  The second and third values here correspond to the `LTI_CLIENT_KEY` and `LTI_CLIENT_SECRET` chosen when setting up the Dalite server above.

Click "Save".

![module-list](https://cloud.githubusercontent.com/assets/945577/12212208/8f04b264-b61c-11e5-934b-8540e1d94da7.png)

![lti-passports](https://cloud.githubusercontent.com/assets/945577/12212222/b800b1ae-b61c-11e5-881b-9fa02c04c86a.png)

* Go to content, create a new unit, click `Advanced` → `LTI` to add a new LTI component, then set these settings on the new component:

  * Custom parameters (first): `assignment_id=assign1`
  * Custom parameters (second): `question_id=1`
  * Display Name: `Dalite 1`
  * LTI ID: `dalite`
  * LTI URL: `http://192.168.33.10/lti/`. The trailing `/` is required.

![lti-xblock-1](https://cloud.githubusercontent.com/assets/945577/12212288/8ef605ce-b61d-11e5-8dea-51620079e305.png)

![lti-xblock-2](https://cloud.githubusercontent.com/assets/945577/12212291/95f33af4-b61d-11e5-943b-afcb65c85ce1.png)

Click "Save". At this point, the Dalite question should be visible in Studio.

**Note:** it is important that the Studio and Dalite URL domains are different; here they are deliberately chosen to be "192.168.33.10" and "localhost".  This difference is necessary to prevent cookies clashing.

Usage Example: Configuring Dalite in Moodle
-------------------------------------------

_**Note**: For the purposes of these example setup instructions, it is assumed that you already have a working local Moodle and a locally running Dalite LTI server._

* Go to Dalite at [http://192.168.33.10:8321/admin/](http://192.168.33.10:8321/admin/) and login with the superuser login you created (see above steps). Note that we use the IP address 192.168.33.10 which is automatically setup for devstacks, so we don't have to fiddle around with port forwarding settings.

* Click "Questions" and create a couple of questions.

* Click "Assignments" and create a new assignment with identifier "assign1". Add the questions previously created to "Chosen questions" for the assignment.

* Navigate to a Moodle course as a course Instructor.

* Click the "Turn editing on" button in the top right corner: ![](http://i.imgur.com/yiOlqse.png)

* Click "Add an activity or resource" on a topic, and then select "External Tool" ![](http://i.imgur.com/TnVuoLu.png)

* Click the "+" (![](http://i.imgur.com/dI6aKpQ.png)) next to the "External tool type" field and configure a new External Tool type (this will be the configuration for the Dalite LTI server):
  - Fill out a "Tool name" of your choosing.
  - Set the tool base URL to `http://192.168.33.10:8321/lti/`.
  - Set the "Consumer key" to `alpha`.
  - Set the "Shared secret" to `beta`.
  - Leave the "Custom parameters" field blank.
  - Set "Default launch container" to "Embed, without blocks".
  - Click "Save changes".

    ![](http://i.imgur.com/QRVEcRy.png)
* Return to the "Adding a new External tool" configuration, and create a new activity:
  - Fill out an "Activity name" of your choosing.
  - Set the "External tool type" to be the name of the tool type you just created.
  - Click "Show more...": ![](http://i.imgur.com/XRBSqag.png)
  - Set the "Custom parameters" to the following, noting that each parameter is on a separate line (change this field when creating each new activity with problems from the same Dalite LTI server):

    ```
assignment_id=assign1
question_id=1
```
    ![](http://i.imgur.com/sCnMy5B.png)
  - Click "Save and Display" (![](http://i.imgur.com/XgGTSbE.png)) to see if your new problem works!
    ![](http://i.imgur.com/epLoE1X.png)

Running the tests
-----------------

The tests can be run with

```
dalite$ export PASSWORD_GENERATOR_NONCE=some_random_string
dalite$ make test
```

(If you have set `PASSWORD_GENERATOR_NONCE` in your settings you don't need the
export statement above.)

After the tests have finished, you can view the coverage report using:

```
dalite$ make coverage-report
```

Deployment notes
----------------

## Storage backends

### AWS

Dalite file upload has been tested with AWS S3  using `django-storages-redux`.

TOOD: Describe how it works

### Open Stack Swift

Dalite file upload has been tested with OpenStack Swift using `django-storage-swift`,
to configure it you'll need to configure dalite, as well as set-up Swift on OpenStack
provider.

#### Swift setup

* Create two publicly readable containers, one can be used for media uploads, second
  for staticfiles (this one is optional).
* Note user credentials required, you might obtain these credentials using the OpenStack Horizon
  web-console (look for in the `Compute -> Access and Security` tab for `Download OpenStack RC file`
  button. This file, once sourced, will set-up OpenStack enviorment variables, that are
  read in the settings example below.   

#### Dalite setup

To set it up you need to:

* Install requirements from ``requirements/prod-openstack.txt``
* Set up the `settings.py` file (extensive list of setting keys
  can be found in the [Django storage swift documentation]
  (https://github.com/blacktorn/django-storage-swift#configuring).

Example file is here (it works  out of the box when you source the
OpenStack rc file)

```
# Storage to use for user uploads
DEFAULT_FILE_STORAGE='swift.storage.SwiftStorage'
# An existing, publicly readable container for media uploads
SWIFT_CONTAINER_NAME='media'

# Storage to use for static file
STATICFILES_STORAGE ='swift.storage.StaticSwiftStorage'
# An existing, publicly readable container for static files
SWIFT_STATIC_CONTAINER_NAME='static'

# Credentials
# This is the url to authentication endpoint of your OpenStack installation
SWIFT_AUTH_URL=os.environ["OS_AUTH_URL"]
# Username for Swift authorization
SWIFT_USERNAME=os.environ["OS_USERNAME"]
# Password for Swift authorization
SWIFT_KEY=os.environ["OS_PASSWORD"]
# This is the auth version to use, on OVH I used version 2
SWIFT_AUTH_VERSION=2
# Tenant ID
SWIFT_TENANT_ID=os.environ["OS_TENANT_ID"]
# Region name, this one is optional
SWIFT_EXTRA_OPTIONS = {
    'region_name': os.environ['OS_REGION_NAME']
}
```

#### Testing Dalite with swift locally

If you need to test Dalite with swift locally, [you might use this vagrant instance]
(https://github.com/swiftstack/vagrant-swift-all-in-one), it will create a working swift VM that is usable
with Dalite.


# Release notes

## v0.0.2 (released at 2016-05-02)

A backward-incompatible change have been introduced in this version, this change allows
users to run dalite on mysql 5.5, which has maximal key length of 767 bytes.

If you have a running dalite instance, you'll need to run following command manually
(this command assumes dalite uses schema  `dalite_ng`):  

     ALTER TABLE `dalite_ng`.`django_lti_tool_provider_ltiuserdata`
     CHANGE COLUMN `custom_key` `custom_key` VARCHAR(190) NOT NULL ;

Before running that command check that no row in
`django_lti_tool_provider_ltiuserdata` table contains more than
190 characters. You can the use following query:

     SELECT MAX(char_length(custom_key)) FROM django_lti_tool_provider_ltiuserdata;


Attributions
------------

The thumbs up and down icons were taken from the [Entypo pictograms by Daniel
Bruce][entypo].

[entypo]: http://www.entypo.com/


Coverage
--------

`$ pytest --cov --cov-report html`


Celery, beat, and Redis
-----------------------

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


Translations
------------
`django-admin makemessages -d djangojs -l fr -i=node_modules/* -i=venv* -i=static/CACHE/* -i=static/admin/* -i=*.min.js`:
  Javascript


Tools
-----
`makefile`:
  Command shortcuts

  `make test`:
    Runs pytest with migration and coverage options
  `make test-cdb`:
    Runs pytest with migration and coverage options, re-creating the db



ElasticSearch
-------------

1. Build the index

  `$ ./manage.py search_index --rebuild`

2. Add config to `local_settings.py`:

  `ELASTICSEARCH_DSL = {
      "default": {"hosts": "<username>:<password>@localhost:9200"},
  }`
