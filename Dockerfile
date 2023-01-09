FROM python:3.10
ENV PYTHONUNBUFFERED 1
WORKDIR /code

RUN mkdir -p /code/static && \
    apt update && \
    apt -y --no-install-recommends install \
        default-libmysqlclient-dev \
        gettext \
        git \
        python3-dev \
    && \
    rm -rf /var/lib/apt/lists/* && \
    apt purge --auto-remove && \
    apt clean

RUN pip install pipenv
COPY Pipfile Pipfile.lock /code/
RUN pipenv sync

COPY . /code/
ENTRYPOINT ["/code/entrypoint.sh"]
