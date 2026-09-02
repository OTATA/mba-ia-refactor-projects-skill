"""Entry point da aplicação.

Mantido na raiz para preservar `python app.py`. A montagem da aplicação está
em `src/app.py`; aqui só existe o arranque do servidor de desenvolvimento.

O original chamava `app.run(debug=True, host='0.0.0.0')` com valores fixos:
o debugger do Werkzeug, que permite executar código no processo, ficava
exposto em todas as interfaces de rede. Agora host, porta e debug vêm da
configuração, e em produção o servidor é o gunicorn:

    gunicorn "app:app" --bind 0.0.0.0:5000
"""

from src.app import create_app

app = create_app()

if __name__ == "__main__":
    app.run(
        host=app.config["HOST"],
        port=app.config["PORT"],
        debug=app.config["DEBUG"],
    )
