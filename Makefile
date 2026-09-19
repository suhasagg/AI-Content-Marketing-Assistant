run:
	uvicorn app.main:app --reload --port 8080
test:
	pytest -q
