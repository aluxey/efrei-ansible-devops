import os

from flask import Flask, jsonify
import psycopg


APP_NAME = os.environ.get("APP_NAME", "devops_quote_api")
DATABASE_URL = os.environ["DATABASE_URL"]

app = Flask(__name__)


def get_connection():
    return psycopg.connect(DATABASE_URL)


@app.route("/health")
def health():
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            result = cursor.fetchone()[0]

    return jsonify(
        {
            "status": "ok",
            "service": APP_NAME,
            "database": "postgresql",
            "result": result,
        }
    )


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000)
