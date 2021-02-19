[![Depedency updates status](https://pyup.io/repos/github/TampereHacklab/mulysa/shield.svg)](https://pyup.io/repos/github/TampereHacklab/mulysa/)
[![Build status](https://github.com/TampereHacklab/mulysa/actions/workflows/tox.yml/badge.svg?branch=master)](https://github.com/TampereHacklab/mulysa/actions/workflows/tox.yml)
[![Coverage Status](https://coveralls.io/repos/github/TampereHacklab/mulysa/badge.svg?branch=master)](https://coveralls.io/github/TampereHacklab/mulysa?branch=master)

# Mulysa

asylum[::-1] is a member management system for Tampere Hacklab.

# Idea

Tampere Hacklab has been groving and member management has become pretty labor intensive.
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

Make sure you have proper python installation on your machine

* python 3.7
* pipenv from here: https://github.com/pypa/pipenv

Then run

```bash
git clone git@github.com:TampereHacklab/mulysa.git
cd mulysa
pipenv sync --dev
pipenv shell
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

run:

```bash
./manage.py update_local_bootstrap
```

* paste update settings.py with the new values
* commit all the files

## Style checks & tests

Before committing, run

* black

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

200 responses can be considered valid access, all other are invalid. 200 responses will also contain some basic user data for example for showing in a door access welcome message.

API will return these responses on certain error conditions:
 - 400 when query has invalid content
 - 404 when deviceid isn't found
 - 480 when phone number/NFC id/mxid is not found at all
 - 481 when phone number/NFC id/mxid is found within member but has no access rights, response will also contain basic user data for example executing proper procedures and admin logs

There are two example implementations for esp32 based access readers that can be found here:

https://github.com/TampereHacklab/mulysa_callerid
https://github.com/TampereHacklab/mulysa_nfc_reader

# Door access api listings

Door access information can also be fetched for local checking and caching.

```
curl -X GET -H "Authorization: Token xxxxxxxxxxxxxx" http://127.0.0.1:8000/api/v1/access/phone/
```

will return a list of users with access to the door. Calling this endpoint you must be authenticated and have superadmin permissions.
