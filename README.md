[![Updates](https://pyup.io/repos/github/TampereHacklab/mulysa/shield.svg)](https://pyup.io/repos/github/TampereHacklab/mulysa/)
[![Build Status](https://travis-ci.org/TampereHacklab/mulysa.svg?branch=master)](https://travis-ci.org/TampereHacklab/mulysa)
[![Coverage Status](https://coveralls.io/repos/github/TampereHacklab/mulysa/badge.svg?branch=master)](https://coveralls.io/github/TampereHacklab/mulysa?branch=master)

# Mulysa

asylym[::-1] is a member management system for Tampere Hacklab.

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

* clone the repo
* install pipenv
* pipenv shell
* pipenv install --dev
* ./manage.py makemigrations
* ./manage.py migrate
* ./manage.py loaddata memberservices
* ./manage.py runserver

## To update localizations

* django-admin makemessages -l fi
* (edit .po files)
* django-admin compilemessages

Push only .po files to git, not .mo's!

## Style checks & tests

Before committing, run

* black
* flake8
* tox

# Future improvements

* Automate fetching and processing of member payment data from bank


# Door access api

There are currently two different api endpoints for door access. One phone number based and one for nfc cards.

Phone number based access is based on the users phone number and they must have a active subscription to the default service (on a default installation this would be serviceid=2 "tilankäyttöoikeus"). User can also have multiple NFC cards that check the same service access.

Both endpoints expect the same data. a device id which needs to be first added to access devices (this is for future, there might be multiple doors with diffrent levels of access for example) and the payload (the phone number or nfc card id).

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


200 responses can be considered valid access, all other are invalid. 200 responses will also contain some basic user data for example for showing in a door access welcome message.

API will return these responses on certain error conditions:
 - 400 when query has invalid content
 - 404 when deviceid isn't found
 - 480 when phone number/NFC id is not found at all
 - 481 when phone number/NFC id is found within member but has no access rights

There are two example implementations for esp32 based access readers that can be found here:

https://github.com/TampereHacklab/mulysa_callerid
https://github.com/TampereHacklab/mulysa_nfc_reader