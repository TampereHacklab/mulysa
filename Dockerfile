FROM python:3
RUN apt update
RUN apt -y install gettext git python3-dev default-libmysqlclient-dev
ENV PYTHONUNBUFFERED 1
RUN pip install pipenv
RUN mkdir /code 
WORKDIR /code
ADD . /code/
RUN git clone https://github.com/wsvincent/drfx.git ; exit 0
WORKDIR /code/drfx
RUN pipenv install
WORKDIR /code
RUN pipenv install
ENTRYPOINT ["/code/entrypoint.sh"]
