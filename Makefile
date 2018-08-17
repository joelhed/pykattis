files = **/*.py

lint:
	pipenv run flake8 $(files)

format:
	pipenv run black $(files)

upload:
	pipenv run python setup.py upload
