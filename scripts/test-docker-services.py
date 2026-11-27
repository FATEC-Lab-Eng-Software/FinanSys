import json
import socket
import subprocess
import time
import unittest
import urllib.parse
import urllib.request
import uuid
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
COMPOSE = ["docker", "compose"]
ONE_SHOT_SERVICES = {"supabase-auth-db-init"}


def run_compose(*arguments, timeout=900):
    return subprocess.run(
        [*COMPOSE, *arguments],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=timeout,
    )


def host_port(service, container_port):
    result = run_compose("port", service, str(container_port))
    return int(result.stdout.strip().rsplit(":", 1)[1])


def api_request(url, method="GET", payload=None, headers=None):
    request_headers = dict(headers or {})
    body = None if payload is None else json.dumps(payload).encode()
    if body is not None:
        request_headers["Content-Type"] = "application/json"
    request = urllib.request.Request(url, data=body, headers=request_headers, method=method)
    with urllib.request.urlopen(request, timeout=10) as response:
        return response.status, response.read()


def api_json(url, method="GET", payload=None, headers=None):
    status, body = api_request(url, method, payload, headers)
    return status, json.loads(body) if body else {}


class DockerServicesTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        run_compose("up", "--detach", "--wait")
        cls.compose_config = json.loads(run_compose("config", "--format", "json").stdout)
        cls.expected_services = set(cls.compose_config["services"]) - ONE_SHOT_SERVICES
        result = run_compose("ps", "--all", "--format", "json")
        cls.containers = [json.loads(line) for line in result.stdout.splitlines() if line]

    def test_all_compose_services_are_running(self):
        running_services = {
            container["Service"]
            for container in self.containers
            if container.get("State", "").lower() == "running"
        }
        self.assertSetEqual(self.expected_services, running_services)

    def test_kong_waits_until_auth_is_healthy(self):
        auth_dependency = self.compose_config["services"]["supabase-kong"]["depends_on"]["supabase-auth"]
        self.assertEqual(auth_dependency["condition"], "service_healthy")

    def test_server_waits_until_kong_is_healthy(self):
        kong_dependency = self.compose_config["services"]["server"]["depends_on"]["supabase-kong"]
        self.assertEqual(kong_dependency["condition"], "service_healthy")

    def test_kong_healthcheck_runs_frequently_during_startup(self):
        healthcheck = self.compose_config["services"]["supabase-kong"]["healthcheck"]
        self.assertEqual(healthcheck["test"][-1], "kong-health")
        self.assertEqual(healthcheck["interval"], "5s")

    def test_mailpit_web_interface_responds(self):
        port = host_port("mailpit", 8025)
        with urllib.request.urlopen(f"http://127.0.0.1:{port}/", timeout=10) as response:
            self.assertEqual(response.status, 200)

    def test_mailpit_accepts_smtp_connections(self):
        port = host_port("mailpit", 1025)
        with socket.create_connection(("127.0.0.1", port), timeout=10) as connection:
            greeting = connection.recv(1024)
        self.assertTrue(greeting.startswith(b"220"), greeting.decode(errors="replace"))

    def test_unconfirmed_account_resend_is_delivered_to_mailpit(self):
        email = f"mailpit-check-{uuid.uuid4().hex}@finansys.test"
        auth_base = f"http://127.0.0.1:{host_port('supabase-kong', 8000)}/auth/v1"
        mailpit_base = f"http://127.0.0.1:{host_port('mailpit', 8025)}/api/v1"
        server_base = f"http://127.0.0.1:{host_port('server', 8000)}"
        service_key = self.compose_config["services"]["supabase-kong"]["environment"]["SUPABASE_SERVICE_KEY"]
        service_headers = {"apikey": service_key, "Authorization": f"Bearer {service_key}"}
        user_id = None
        message_ids = []
        try:
            _, user = api_json(
                f"{auth_base}/admin/users",
                "POST",
                {"email": email, "password": "TempPassword123!", "email_confirm": False},
                service_headers,
            )
            user_id = user.get("id")
            self.assertIsNotNone(user_id)
            status, _ = api_json(
                f"{server_base}/auth/resend-confirmation",
                "POST",
                {"email": email},
                {"Origin": "http://localhost:3000"},
            )
            self.assertEqual(status, 202)
            deadline = time.monotonic() + 10
            matches = []
            while time.monotonic() < deadline:
                _, messages = api_json(f"{mailpit_base}/messages?start=0&limit=100")
                matches = [message for message in messages.get("messages", []) if email in json.dumps(message)]
                if matches:
                    break
                time.sleep(0.25)
            message_ids = [message.get("ID") for message in matches if message.get("ID")]
            self.assertTrue(matches, "O Auth aceitou o reenvio, mas o Mailpit não recebeu a mensagem.")
        finally:
            try:
                if message_ids:
                    api_request(f"{mailpit_base}/messages", "DELETE", {"IDs": message_ids})
            finally:
                if user_id:
                    api_request(f"{auth_base}/admin/users/{user_id}", "DELETE", headers=service_headers)


if __name__ == "__main__":
    unittest.main()
