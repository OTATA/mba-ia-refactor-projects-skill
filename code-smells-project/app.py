"""Entry point da aplicação.

Mantido na raiz para preservar `python app.py`. A montagem da aplicação está
em `src/app.py`; aqui só existe o arranque do servidor de desenvolvimento.
"""

from src.app import create_app

app = create_app()

if __name__ == "__main__":
    app.run(
        host=app.config["HOST"], port=app.config["PORT"], debug=app.config["DEBUG"]
    )
