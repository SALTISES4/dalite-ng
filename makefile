test:
	pytest --nomigrations --cov --cov-report term-missing
test-cdb:
	pytest --nomigrations --cov --cov-report term-missing --create-db
