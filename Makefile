files = *.py

lint:
	pipenv run flake8 $(files)

format:
	pipenv run black $(files)
