import json
import socket
import subprocess
import unittest
import urllib.request
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


if __name__ == "__main__":
    unittest.main()
