files = *.py problems/**/*.py

lint:
	pipenv run flake8 $(files)

format:
	pipenv run black $(files)
