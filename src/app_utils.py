import os
from flask import Flask
from waitress import serve


def get_env_var_as_bool(value: str):
    return value.lower() in ["true", "1", "t", "yes", "y"]


STAGE = os.environ.get("STAGE", default="prod")
PORT = int(os.environ.get("PORT", default="8080"))


def run(app):
    if STAGE == "dev":
        print("Running dev server")
        run_flask_beta_server(app, PORT)
    elif STAGE == "prod":
        print("Running prod server")
        run_flask_production_server(app, PORT)
    else:
        run_flask_production_server(app, PORT)


def run_flask_production_server(app: Flask, port):
    serve(app, host="0.0.0.0", port=port)


def run_flask_beta_server(app: Flask, port):
    app.run(threaded=True, host="0.0.0.0", debug=True, port=port)
