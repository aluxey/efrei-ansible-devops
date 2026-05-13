import json
import os
from pathlib import Path

import testinfra.utils.ansible_runner

testinfra_hosts = testinfra.utils.ansible_runner.AnsibleRunner(
    os.environ['MOLECULE_INVENTORY_FILE']).get_hosts('all')

APP_SERVICE = "devops_quote_api"


def fetch_json(host, url):
    command = (
        "python3 -c 'import urllib.request; "
        f"print(urllib.request.urlopen(\"{url}\").read().decode())'"
    )
    return json.loads(host.check_output(command))


def test_nginx_running_and_enabled(host):
    nginx_service = host.service("nginx")
    assert nginx_service.is_running
    assert nginx_service.is_enabled


def test_postgresql_running_and_enabled(host):
    database_service = host.service("postgresql")
    assert database_service.is_running
    assert database_service.is_enabled


def test_application_running_and_enabled(host):
    application_service = host.service(APP_SERVICE)
    assert application_service.is_running
    assert application_service.is_enabled


def test_nginx_listening(host):
    assert host.socket("tcp://0.0.0.0:80").is_listening


def test_application_listening_on_localhost(host):
    assert host.socket("tcp://127.0.0.1:5000").is_listening


def test_health_endpoint_through_nginx(host):
    response = fetch_json(host, "http://127.0.0.1/health")
    assert response["status"] == "ok"
    assert response["service"] == APP_SERVICE
    assert response["database"] == "postgresql"
    assert response["result"] == 1


def test_postgresql_connection_with_vault_password(host):
    vault_file = Path(__file__).resolve().parents[3] / "group_vars" / "devops_dev" / "vault.yml"
    db_password = None
    for line in vault_file.read_text(encoding="utf-8").splitlines():
        if line.strip().startswith("db_password:"):
            db_password = line.split(":", 1)[1].strip().strip('"').strip("'")
            break
    assert db_password is not None

    command = (
        "PGPASSWORD='{password}' psql -h 127.0.0.1 -U devops_api "
        "-d devops_quotes -c '\\q'"
    ).format(password=db_password)
    result = host.run(command)
    assert result.rc == 0
