test:
	pytest --cov --cov-report term-missing
test-cdb:
	pytest --cov --cov-report term-missing --create-db -vvvs
rebuild:
	./node_modules/gulp/bin/gulp.js build
	./manage.py collectstatic --clear --noinput
	./manage.py compress
refresh: rebuild
	./manage.py runserver
compile-requirements:
	pip-compile requirements/requirements-base.in --index-url https://pypi.python.org/simple
	pip-compile requirements/requirements-test.in --index-url https://pypi.python.org/simple
	pip-compile requirements/requirements-dev.in --index-url https://pypi.python.org/simple
	pip-compile requirements/requirements-prod-aws.in --index-url https://pypi.python.org/simple
