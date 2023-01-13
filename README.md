[![Depedency updates status](https://pyup.io/repos/github/TampereHacklab/mulysa/shield.svg)](https://pyup.io/repos/github/TampereHacklab/mulysa/)
[![Build status](https://github.com/TampereHacklab/mulysa/actions/workflows/tox.yml/badge.svg?branch=master)](https://github.com/TampereHacklab/mulysa/actions/workflows/tox.yml)
[![Coverage Status](https://coveralls.io/repos/github/TampereHacklab/mulysa/badge.svg?branch=master)](https://coveralls.io/github/TampereHacklab/mulysa?branch=master)

# Mulysa

asylum[::-1] is a member management system for Tampere Hacklab.

# Idea

Tampere Hacklab has been growing and member management has become pretty labour intensive.
This project tries to automate the boring parts by automating the communication with members,
managing the door access and managing the LDAP account creation (some of this is still on the TODO list).

Most of this works around our "User" model which can do multiple things

* Member can be registered as a new member
  * Member has to accept terms and conditions
  * Member will fill in their basic information like name, email, phone and address
  * Mulysa will generate a member id and bank reference number for this member
  * Mulysa will send an email to the new member stating how to pay their membership fee
* Treasurer can fetch information about new members
  * a simple list of all new members
  * a simple update call for treasurer to mark the members as being "watched"
* Treasurer can update "active" information of the member
  * when the member has paid their fees normally Treasurer will send a message to Mulysa to set the member active = true
  * when the member has not paid their fees Treasurer will set the member as active = false
* Member can request to leave Tampere Hacklab
  * Member fills in their email address
  * Mulysa sends email with a confirmation link and information to the Member
  * If member uses the activation link within X days the member will be MarkedForDeletion and deleted after XX days
* Door access can be automated with nfc or phone number

# Start developing

In order to run your local development environment of mulysa, there are some prerequisites you first need to install.

## Installing prerequisites on Debian 11.2

```sh
sudo apt install git python3-dev gettext pipenv default-libmysqlclient-dev
```

## Installing prerequisites on Mac OS

Make sure you have [Homebrew](https://brew.sh/) installed, then run:

```sh
brew install git
```

```sh
brew install pipenv
```

_Note: Homebrew will automatically install python for you since it is a prerequisite of pipenv._

```sh
brew install mysql
```

```sh
brew install gettext
```

## Installing prerequisites on other platforms

Find a way to install the software on this list (click the links to find installer downloads):

* [git](https://git-scm.com/book/en/v2/Getting-Started-Installing-Git)
* [python](https://www.python.org/downloads/) 3.9
* [gettext](https://www.gnu.org/software/gettext/) for translation editing and compiling
* [MySQL C API (libmysqlclient)](https://dev.mysql.com/downloads/c-api/)
* [pipenv](https://github.com/pypa/pipenv)

When you have the prerequisites installed, run these commands:

```bash
git clone https://github.com/TampereHacklab/mulysa.git
cd mulysa
pipenv sync --dev
pipenv shell
```

Create your own `drfx/settings_local.py` file with at least this to get cookies working without ssl

```
# revert back to cookie names that work in dev
SESSION_COOKIE_NAME = '__NotReallyHost-sessionid'
LANGUAGE_COOKIE_NAME = '__NotReallyHost-language'
CSRF_COOKIE_NAME = '__NotReallyHost-csrf'
```

```bash
./manage.py migrate --skip-checks
./manage.py loaddata memberservices
./manage.py runserver
```

## To update localizations

Always start everything by opening the pipenv shell for this project first! (`pipenv shell`) or by prepending individual commands with (`pipenv run`) for system users that does not have shell access normally.

```bash
./manage.py makemessages -l fi
```

Edit the .po files

```bash
./manage.py compilemessages
```

Push only the .po files to git, not .mo's!

# to update dependecies

run:

```bash
pipenv update
pipenv lock
pipenv sync
tox
```

## to update local bootstrap files

This will download some js and css files from external sites to be hosted locally.

run:

```bash
./manage.py update_local_bootstrap
```

the command spits out the new filenames that need to be updated to the settings.py file.

* update settings.py with the new values
* commit all the files

## Style checks & tests

Before committing, run

* black

### Running all test cases

```bash
./manage.py test
```

### Running just one test case

To speed up writing your tests you can run only one test case with something like this

```
./manage.py test api.tests.TestAccess.test_access_phone_list_unauthenticated
```

# Future improvements

* Automate fetching and processing of member payment data from bank

# Door access api

There are multiple api endpoints for checking door access: One phone number, nfc card and Matrix ID.

Phone number based access is based on the users phone number and they must have a active subscription to the default service (on a default installation this would be serviceid=2 "tilankäyttöoikeus"). User can also have multiple NFC cards that check the same service access.

All endpoints expect the same data. a device id which needs to be first added to access devices (this is for future, there might be multiple doors with diffrent levels of access for example) and the payload (the phone number, nfc card id or Matrix ID).

Examples:

```
curl -X POST \
  http://127.0.0.1:8000/api/v1/access/nfc/ \
  -H 'Content-Type: application/json' \
  -d '{
     "deviceid": "123",
     "payload": "ABC321"
   }'
```

```
curl -X POST \
  http://127.0.0.1:8000/api/v1/access/phone/ \
  -H 'Content-Type: application/json' \
  -d '{
     "deviceid": "123",
     "payload": "+358123123123"
   }'
```

```
curl -X POST \
  http://127.0.0.1:8000/api/v1/access/mxid/ \
  -H 'Content-Type: application/json' \
  -d '{
     "deviceid": "123",
     "payload": "@user:server.org"
   }'
```

HTTP `200` responses can be considered valid access, all other are invalid. `200` responses will also contain some basic user data for example for showing in a door access welcome message.

API will return these HTTP status code responses on certain error conditions:

* `400` when query has invalid content
* `404` when deviceid isn't found
* `480` when phone number/NFC id/mxid is not found at all
* `481` when phone number/NFC id/mxid is found within member but has no access rights, response will also contain basic user data for example executing proper procedures and admin logs
* `429` if rate throttling kicks in

There are two example implementations for esp32 based access readers that can be found here:

<https://github.com/TampereHacklab/mulysa_callerid>
<https://github.com/TampereHacklab/mulysa_nfc_reader>

# Door access api listings

Door access information can also be fetched for local checking and caching.

```
curl -X GET -H "Authorization: Token xxxxxxxxxxxxxx" http://127.0.0.1:8000/api/v1/access/phone/
```

will return a list of users with access to the door. Calling this endpoint you must be authenticated and have superadmin permissions.

# use oauth auth (advanced usage with keycloak integration)

These two settings are a bit intermingled, you need the redirect url in mulysa to create the app to get the id and secret
and you need the id and secret to create the keycloack end to get the redirect url :D

Just do one first with either dummy data or good guess then do the other.

## as a logged in admin user in mulysa

* go to: `https://yourmulysadomain/admin/oauth2_provider/application/`
* click on `add application`
  * clientid: autogenerated value works fine
  * user: leave empty
  * redirect uris: the url from keycloack
  * client type: confidential
  * authorization grant type: auth code
  * clientsecret: autogenerated value works fine (keep it secret!)
  * Name: keycloack
  * Skip authorisation: checked (this will skip one extra step after login)
  * algorithm: HMAC with SHA-2 256 (or RSA but then you need to create the key etc)
* take your clientid and client secret and endpoint and configure them in keycloak

## as a logged in admin user in keycloak

* go to [realm] -> identity providers -> add provider -> openid connect v1.0
* create new (only changes to defaults listed here)

  * alias: mulysa
  * display name: mulysa (or what ever you want to call it)
  * trust email: yes
  * sync mode: force (this makes the data always update from mulysa)
  * Authorization URL: https://yourmulysadomain/o/authorize/
  * Token URL: https://yourmulysadomain/o/token/
  * User Info URL: https://yourmulysadomain/o/userinfo/
  * Client Authentication: client secret sent as post
  * Client ID: the client id from mulysa
  * Client Secret: the client secret from mulysa
  * save

* go to [realm] -> identity providers -> [display name] -> Mappers
* create

  * name: firstnamemapper
  * Sync Mode Override: force
  * Mapper Type: Attribute Importer
  * Claim: firstName
  * User Attribute Name: firstName
  * save

* go to [realm] -> identity providers -> [display name] -> Mappers
* create
  * name: lastnamemapper
  * Sync Mode Override: force
  * Mapper Type: Attribute Importer
  * Claim: lastName
  * User Attribute Name: lastName
  * save

## fingers crossed

just try it out :)
