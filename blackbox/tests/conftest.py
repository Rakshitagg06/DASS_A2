"""Shared fixtures and helpers for the QuickCart black-box API tests."""

from __future__ import annotations

import json
import shutil
import socket
import subprocess
import tarfile
import time
from pathlib import Path

import pytest
import requests


ROLL_NUMBER = "2026001"
API_PORT = 8080
SEEDED_CLEAN_USER_ID = 7
SEEDED_REVIEW_USER_ID = 29
SEEDED_SECOND_REVIEW_USER_ID = 30
SEEDED_DELIVERED_ORDER_USER_ID = 681
SEEDED_DELIVERED_ORDER_ID = 2997


class QuickCartClient:
    """Small HTTP helper for the seeded QuickCart API instance."""

    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip("/")

    def request(
        self,
        method: str,
        path: str,
        *,
        user_id: int | None = None,
        roll_number: str | None = ROLL_NUMBER,
        timeout: float = 3.0,
        **kwargs,
    ):
        headers = dict(kwargs.pop("headers", {}))
        if roll_number is not None:
            headers.setdefault("X-Roll-Number", str(roll_number))
        if user_id is not None:
            headers.setdefault("X-User-ID", str(user_id))
        return requests.request(
            method,
            f"{self.base_url}{path}",
            headers=headers,
            timeout=timeout,
            **kwargs,
        )

    def get(self, path: str, **kwargs):
        return self.request("GET", path, **kwargs)

    def post(self, path: str, **kwargs):
        return self.request("POST", path, **kwargs)

    def put(self, path: str, **kwargs):
        return self.request("PUT", path, **kwargs)

    def delete(self, path: str, **kwargs):
        return self.request("DELETE", path, **kwargs)

    def admin_json(self, path: str):
        response = self.get(path)
        response.raise_for_status()
        return response.json()

    def user_json(self, path: str, user_id: int):
        response = self.get(path, user_id=user_id)
        response.raise_for_status()
        return response.json()

    def admin_products_by_id(self):
        return {
            product["product_id"]: product
            for product in self.admin_json("/admin/products")
        }

    def clean_user_id(self) -> int:
        return SEEDED_CLEAN_USER_ID

    def user_with_addresses_id(self) -> int:
        return SEEDED_CLEAN_USER_ID

    def review_user_id(self) -> int:
        return SEEDED_REVIEW_USER_ID

    def second_review_user_id(self) -> int:
        return SEEDED_SECOND_REVIEW_USER_ID

    def delivered_order(self) -> tuple[int, int]:
        return SEEDED_DELIVERED_ORDER_USER_ID, SEEDED_DELIVERED_ORDER_ID


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _image_dir() -> Path:
    return _repo_root() / "quickcart_image_x86"


def _manifest() -> dict:
    image_dir = _image_dir()
    index = json.loads((image_dir / "index.json").read_text())
    manifest_digest = index["manifests"][0]["digest"].split(":", 1)[1]
    return json.loads((image_dir / "blobs" / "sha256" / manifest_digest).read_text())


def _extract_rootfs(destination: Path) -> None:
    image_dir = _image_dir()
    manifest = _manifest()
    blob_dir = image_dir / "blobs" / "sha256"
    for layer in manifest["layers"]:
        digest = layer["digest"].split(":", 1)[1]
        with tarfile.open(blob_dir / digest, mode="r:gz") as archive:
            archive.extractall(destination)


def _ensure_port_available(port: int) -> None:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(0.2)
        if sock.connect_ex(("127.0.0.1", port)) == 0:
            raise RuntimeError(
                f"Port {port} is already in use. Stop the running service and rerun pytest."
            )


def _wait_for_server(process: subprocess.Popen, log_path: Path) -> None:
    client = QuickCartClient(f"http://127.0.0.1:{API_PORT}/api/v1")
    last_error = ""
    deadline = time.time() + 10

    while time.time() < deadline:
        if process.poll() is not None:
            log_tail = log_path.read_text()[-4000:]
            raise RuntimeError(
                "QuickCart server exited during startup.\n"
                f"Process return code: {process.returncode}\n"
                f"Server log:\n{log_tail}"
            )
        try:
            response = client.get("/admin/users")
            if response.status_code == 200:
                return
            last_error = f"Unexpected startup status: {response.status_code}"
        except requests.RequestException as exc:
            last_error = str(exc)
        time.sleep(0.1)

    log_tail = log_path.read_text()[-4000:]
    raise RuntimeError(
        "QuickCart server did not become ready in time.\n"
        f"Last error: {last_error}\n"
        f"Server log:\n{log_tail}"
    )


@pytest.fixture(scope="session")
def quickcart_rootfs(tmp_path_factory):
    """Extract the provided OCI image once for the full test session."""
    rootfs_dir = tmp_path_factory.mktemp("quickcart-rootfs")
    _extract_rootfs(rootfs_dir)
    return rootfs_dir


@pytest.fixture
def api(tmp_path, quickcart_rootfs):
    """Run a fresh QuickCart server backed by a fresh copy of the seeded DB."""
    _ensure_port_available(API_PORT)

    runtime_dir = tmp_path / "runtime"
    runtime_dir.mkdir()
    shutil.copy2(quickcart_rootfs / "app" / "quickcart", runtime_dir / "quickcart")
    shutil.copy2(
        quickcart_rootfs / "app" / "quickcart.db",
        runtime_dir / "quickcart.db",
    )
    shutil.copy2(
        quickcart_rootfs / "lib" / "ld-musl-x86_64.so.1",
        runtime_dir / "ld-musl-x86_64.so.1",
    )

    log_path = runtime_dir / "quickcart.log"
    with log_path.open("w", encoding="utf-8") as log_file:
        process = subprocess.Popen(
            [str(runtime_dir / "ld-musl-x86_64.so.1"), "./quickcart"],
            cwd=runtime_dir,
            stdout=log_file,
            stderr=subprocess.STDOUT,
        )
        _wait_for_server(process, log_path)
        try:
            yield QuickCartClient(f"http://127.0.0.1:{API_PORT}/api/v1")
        finally:
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=5)
