import socket
import subprocess
import time
from urllib.parse import urlparse

from django.conf import settings
from django.core.management.base import CommandError
from django.core.management.commands.runserver import Command as RunserverCommand


def _is_local_host(hostname: str | None) -> bool:
    return hostname in {"localhost", "127.0.0.1", "::1"}


def _parse_base_url(base_url: str) -> tuple[str, int]:
    raw = base_url or "http://localhost:11434"
    if "://" not in raw:
        raw = f"http://{raw}"
    parsed = urlparse(raw)
    host = parsed.hostname or "localhost"
    port = parsed.port or (443 if parsed.scheme == "https" else 80)
    return host, port


def _can_connect(host: str, port: int) -> bool:
    try:
        with socket.create_connection((host, port), timeout=1):
            return True
    except OSError:
        return False


def _wait_for_port(host: str, port: int, timeout_seconds: float) -> bool:
    deadline = time.time() + timeout_seconds
    while time.time() < deadline:
        if _can_connect(host, port):
            return True
        time.sleep(0.4)
    return False


class Command(RunserverCommand):
    help = "Start Ollama (if needed) and run the Django development server."

    def handle(self, *args, **options):
        options["use_reloader"] = False

        base_url = getattr(settings, "OLLAMA_BASE_URL", "http://localhost:11434")
        host, port = _parse_base_url(base_url)

        started = None
        if _is_local_host(host):
            if not _can_connect(host, port):
                try:
                    started = subprocess.Popen(
                        ["ollama", "serve"],
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL,
                    )
                except FileNotFoundError as exc:
                    raise CommandError(
                        "Ollama CLI not found. Install Ollama and ensure it is on PATH."
                    ) from exc
                if not _wait_for_port(host, port, timeout_seconds=20):
                    raise CommandError("Ollama failed to start. Check the Ollama install.")
        else:
            self.stdout.write(self.style.WARNING("OLLAMA_BASE_URL is not local; skipping auto-start."))

        try:
            return super().handle(*args, **options)
        finally:
            if started is not None:
                started.terminate()
                try:
                    started.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    started.kill()
