#!/bin/bash
docker compose build
# docker compose up celery nginx redis selenium-hub chrome test_chrome --abort-on-container-exit
# echo "Done testing Chrome"
# docker compose up celery nginx redis selenium-hub firefox test_firefox --abort-on-container-exit
# echo "Done testing Firefox"
docker compose up celery nginx redis selenium-hub edge test_edge --abort-on-container-exit
echo "Done testing Edge"
