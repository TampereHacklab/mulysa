[![Updates](https://pyup.io/repos/github/TampereHacklab/mulysa/shield.svg)](https://pyup.io/repos/github/TampereHacklab/mulysa/)
[![Build Status](https://travis-ci.org/TampereHacklab/mulysa.svg?branch=master)](https://travis-ci.org/TampereHacklab/mulysa)
[![Coverage Status](https://coveralls.io/repos/github/TampereHacklab/mulysa/badge.svg?branch=master)](https://coveralls.io/github/TampereHacklab/mulysa?branch=master)

# Mulysa

asylym[::-1] is a member management system for Tampere Hacklab.

# Idea

Tampere Hacklab has been groving and member management has become pretty labor intensive.
This project tries to automate the boring parts by automating the communication with members,
managing the door access and managing the LDAP account creation.

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

# Start developing

* clone the repo
* install pipenv
* pipenv shell
* pipenv install --dev
* ./manage.py makemigrations
* ./manage.py migrate
* ./manage.py loaddata memberservices
* ./manage.py runserver

# Member state changes will trigger things

* State == active
  * members phone number will be added to the door management
  * members email will be activated to ldap (or added)
  * email to member stating what happened
* State == inactive
  * member phone number will be removed from the door management
  * members ldap account will be disabled
  * email to member stating what happened
* State == new
  * email to member with directions on what to do next


# Future improvements

* Automate fetching and processing of member payment data from bank

# examples

## register new user:

## deactivate user:

```
curl -X PATCH \
  http://127.0.0.1:8000/api/v1/users/2/set_activation/ \
  -H 'Authorization: Token FILL_WITH_YOUR_ADMIN_USER_TOKEN' \
  -H 'Content-Type: application/json' \
  -d '{
 "is_active": false
}'
```

## get list of new users

TODO

## push new payment for user

TODO


TODO: more examples
