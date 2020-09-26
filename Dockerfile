FROM python:3.8
RUN apt update
RUN apt -y install gettext git python3-dev default-libmysqlclient-dev
ENV PYTHONUNBUFFERED 1
RUN pip install pipenv
RUN mkdir /code
RUN mkdir /code/static
WORKDIR /code
ADD . /code/
WORKDIR /code
RUN pipenv install
ENTRYPOINT ["/code/entrypoint.sh"]
