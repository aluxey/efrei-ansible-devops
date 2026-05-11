import os

from flask import Flask, jsonify
import psycopg


APP_NAME = os.environ.get("APP_NAME", "devops_quote_api")
APP_MESSAGE = os.environ.get(
    "APP_MESSAGE",
    "API de demonstration deployee avec Ansible",
)
APP_QUOTE_SEED = os.environ.get(
    "APP_QUOTE_SEED",
    "Infrastructure as code, livree proprement.",
)
DATABASE_URL = os.environ["DATABASE_URL"]

app = Flask(__name__)


def get_connection():
    return psycopg.connect(DATABASE_URL)


def ensure_seed_data():
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS quotes (
                    id SERIAL PRIMARY KEY,
                    body TEXT NOT NULL
                )
                """
            )
            cursor.execute("SELECT COUNT(*) FROM quotes")
            if cursor.fetchone()[0] == 0:
                cursor.execute(
                    "INSERT INTO quotes (body) VALUES (%s)",
                    (APP_QUOTE_SEED,),
                )
        connection.commit()


def get_quote_count():
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) FROM quotes")
            return cursor.fetchone()[0]


@app.route("/")
def index():
    return jsonify(
        {
            "service": APP_NAME,
            "message": APP_MESSAGE,
            "quote_count": get_quote_count(),
        }
    )


@app.route("/health")
def health():
    return jsonify({"status": "ok", "service": APP_NAME})


@app.route("/db-health")
def db_health():
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            result = cursor.fetchone()[0]

    return jsonify(
        {
            "status": "ok",
            "database": "postgresql",
            "result": result,
        }
    )


ensure_seed_data()


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000)
