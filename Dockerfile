# Resources
# https://testdriven.io/blog/dockerizing-django-with-postgres-gunicorn-and-nginx/
# https://mherman.org/presentations/dockercon-2018

FROM node:16 AS static
RUN mkdir /code
WORKDIR /code
COPY .eslintrc.json ./
COPY tsconfig.json ./
COPY package*.json ./
RUN npm i
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
COPY gulpfile.js .
RUN npx gulp build

FROM python:3.8
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
WORKDIR /code
RUN mkdir log
RUN mkdir static
COPY requirements ./requirements
RUN python3 -m pip install --upgrade pip
RUN pip3 install --no-deps -r ./requirements/requirements-prod-aws.txt
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
RUN python3 manage.py collectstatic --clear --noinput
RUN python3 manage.py compress
RUN mkdir emails

# https://docs.docker.com/develop/develop-images/dockerfile_best-practices/#user
RUN groupadd -r container_user && useradd --no-log-init -r -g container_user container_user
RUN chown -R container_user:container_user /code
VOLUME /code/emails
USER container_user
