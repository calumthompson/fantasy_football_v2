run:
	poetry run streamlit run app/streamlit_app.py


lint:
	poetry run ruff check src
	poetry run black --check src


reformat:
	poetry run ruff check src --fix
	poetry run black src