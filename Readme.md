[![Updates](https://pyup.io/repos/github/TampereHacklab/mylysa/shield.svg)](https://pyup.io/repos/github/TampereHacklab/mylysa/)

# Mylysa

asylym[::-1] is a member management system for Tampere Hacklab.

# Idea

Tampere hacklab has been groving and member management has become pretty labor intensive. This project tries to automate the borin parts by automating communication with the member, managing door access and managing ldap account creation.

Most of this works around our "User" model which can do multiple things

* Member can register as a new member
  * Member has to accept terms and conditions
  * Member will fill in their basic information like name, email, phone and address
  * Mylysa will generate a member id and bank reference number for this member
  * Mylysa will send an email to the new member stating how to pay their membership fee
* Treasurer can fetch information about new members
  * a simple list of all new members
  * a simple update call for treasurer to mark the members as being "watched"
* Treasurer can update "active" information of the member
  * when the member has paid their fees normally Treasurer will send a message to Mylysa to set the member active = true
  * when the member has not paid their fees Treasurer will set the member as active = false
* Member can request to leave Tampere Hacklab
  * Member fills in their email address
  * Mylysa sends email with a confirmation link and information to the Member
  * If member uses the activation link within X days the member will be MarkedForDeletion and deleted after XX days

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



# Based on DRFx, see below:


# DRFx

A framework for launching new Django Rest Framework projects quickly. Comes with a custom user model, login/logout/signup, social authentication via django-allauth, and more.

## Features

- Django 2.2 and Python 3.7
- Custom user model
- Token-based auth
- Signup/login/logout
- [django-allauth](https://github.com/pennersr/django-allauth) for social auth
- [Pipenv](https://github.com/pypa/pipenv) for virtualenvs

## First-time setup

1.  Make sure Python 3.7x and Pipenv are already installed. [See here for help](https://djangoforbeginners.com/initial-setup/).
2.  Clone the repo and configure the virtual environment:

```
$ git clone https://github.com/wsvincent/drfx.git
$ cd drfx
$ pipenv install
$ pipenv shell
```

3.  Set up the initial migration for our custom user models in users and build the database.

```
(drfx) $ python manage.py makemigrations users
(drfx) $ python manage.py migrate
(drfx) $ python manage.py createsuperuser
(drfx) $ python manage.py runserver
```

4.  Endpoints

Login with your superuser account. Then navigate to all users. Logout. Sign up for a new account and repeat the login, users, logout flow.

- login - http://127.0.0.1:8000/api/v1/rest-auth/login/
- all users - http://127.0.0.1:8000/api/v1/users
- logout - http://127.0.0.1:8000/api/v1/rest-auth/logout/
- signup - http://127.0.0.1:8000/api/v1/rest-auth/registration/

---

Want to learn more about Django REST Framework? I've written an entire book that takes a project-based approach to building web APIs with Django. The first 2 chapters are available for free online at [https://djangoforapis.com/](https://djangoforapis.com/).

[![Django for APIs](https://wsvincent.com/assets/images/djangoforapis_cover_300.jpeg)](https://djangoforapis.com)
