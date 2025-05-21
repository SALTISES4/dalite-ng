# Resources
# https://testdriven.io/blog/dockerizing-django-with-postgres-gunicorn-and-nginx/
# https://mherman.org/presentations/dockercon-2018

FROM node:16 AS static
RUN mkdir /code
WORKDIR /code

COPY analytics ./analytics
COPY blink ./blink
COPY dalite ./dalite
COPY locale ./locale

COPY peerinst ./peerinst
COPY quality ./quality
COPY reputation ./reputation
COPY requirements ./requirements
COPY REST ./REST
COPY saltise ./saltise
COPY templates ./templates
COPY tos ./tos
COPY manage.py .
COPY local_settings.py .

COPY .eslintrc.json ./
COPY tsconfig.json ./
COPY package*.json ./
COPY gulpfile.js .

# RUN npx gulp build

FROM python:3.8-bullseye AS builder
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

WORKDIR /code
RUN ls
RUN apt-get update && \
    apt-get install -y \
    vim \
    default-mysql-client \
    net-tools

# still need node
RUN apt-get update && \
    apt-get install -y curl build-essential && \
    curl -L https://raw.githubusercontent.com/tj/n/master/bin/n -o /usr/local/bin/n && \
    chmod +x /usr/local/bin/n && \
    n lts
ENV PATH="/usr/local/n/versions/node/$(n --version)/bin:${PATH}"
RUN n install 16


RUN mkdir log
RUN mkdir static

COPY requirements ./requirements
RUN python3 -m pip install --upgrade pip==23
# RUN pip3 install --no-deps -r ./requirements/requirements-prod-aws.txt
RUN pip3 install --no-deps -r ./requirements/requirements-dev.txt
# Temporary fix for upcoming lti_provider functional tests
RUN pip3 install factory-boy


From builder AS producer

COPY --from=static /code/analytics ./analytics
COPY --from=static /code/blink ./blink
COPY --from=static /code/dalite ./dalite
COPY --from=static /code/locale ./locale
COPY --from=static /code/peerinst ./peerinst
COPY --from=static /code/quality ./quality
COPY --from=static /code/reputation ./reputation
COPY --from=static /code/REST ./REST
COPY --from=static /code/saltise ./saltise
COPY --from=static /code/templates ./templates
COPY --from=static /code/tos ./tos
COPY --from=static /code/manage.py .
COPY --from=static /code/local_settings.py ./dalite/local_settings.py

# node again
COPY --from=static /code/.eslintrc.json .
COPY --from=static /code/tsconfig.json .
COPY --from=static /code/package*.json .
COPY --from=static /code/gulpfile.js .

RUN echo "Working directory:" && pwd && echo "Contents:" && ls -la

RUN npm i
RUN npx gulp build

RUN python3 manage.py collectstatic --clear --noinput --skip-checks
# RUN python3 manage.py compress
RUN mkdir emails

# note this

# https://docs.docker.com/develop/develop-images/dockerfile_best-practices/#user
#RUN groupadd -r container_user && useradd --no-log-init -r -g container_user container_user
#RUN chown -R container_user:container_user /code
VOLUME /code/emails
USER root
