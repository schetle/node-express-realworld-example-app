"""Shared fixtures for milestone 1 functional tests (target-only).

Every test records its last HTTP exchange via the ``ev`` fixture into an
evidence JSON file (FT_EVIDENCE env var, default /tmp/ft_evidence_m1.json) so
results can be reported verbatim.
"""
import json
import os
import time
import uuid

import pytest
import requests

BASE_URL = os.environ.get("FT_BASE_URL", "http://localhost:3000")
API = f"{BASE_URL}/api"
ACME = {"x-acme-user": "ftrun-acme-user"}
EVIDENCE_FILE = os.environ.get("FT_EVIDENCE", "/tmp/ft_evidence_m1.json")
RUN_ID = f"ftrun_{int(time.time())}_{uuid.uuid4().hex[:6]}"


def tok(token):
    return {"Authorization": f"Token {token}"}


@pytest.fixture(scope="session", autouse=True)
def _health():
    resp = requests.get(f"{BASE_URL}/", timeout=10)
    assert resp.status_code == 200, "app not healthy"
    if os.path.exists(EVIDENCE_FILE):
        os.remove(EVIDENCE_FILE)


class Evidence:
    def __init__(self, name):
        self.name = name

    def __call__(self, resp, method, endpoint, body=None, duration=None):
        try:
            data = json.load(open(EVIDENCE_FILE))
        except Exception:
            data = {}
        data[self.name] = {
            "method": method,
            "endpoint": endpoint,
            "request_body": body,
            "status": resp.status_code,
            "output": resp.text,
            "duration_ms": round(resp.elapsed.total_seconds() * 1000, 1),
        }
        json.dump(data, open(EVIDENCE_FILE, "w"), indent=1)
        return resp


@pytest.fixture
def ev(request):
    return Evidence(request.node.name)


def register(prefix):
    name = f"{prefix}_{RUN_ID}"
    payload = {"user": {"email": f"{name}@example.com", "username": name, "password": "pw-ftrun-123"}}
    resp = requests.post(f"{API}/users", json=payload, timeout=10)
    assert resp.status_code == 201, resp.text
    return resp.json()["user"]


@pytest.fixture(scope="session")
def author():
    return register("author")


@pytest.fixture(scope="session")
def other_user():
    return register("other")


_created_slugs = []


def create_article(user, title_suffix, tags=None):
    title = f"FT {title_suffix} {RUN_ID}"
    payload = {"article": {"title": title, "description": "ft desc", "body": "ft body",
                           "tagList": tags or [RUN_ID]}}
    resp = requests.post(f"{API}/articles", json=payload,
                         headers={**ACME, **tok(user["token"])}, timeout=10)
    assert resp.status_code == 201, resp.text
    slug = resp.json()["article"]["slug"]
    _created_slugs.append((slug, user["token"]))
    return resp.json()["article"]


@pytest.fixture(scope="session", autouse=True)
def _cleanup_articles():
    yield
    for slug, token in _created_slugs:
        requests.delete(f"{API}/articles/{slug}", headers={**ACME, **tok(token)}, timeout=10)


@pytest.fixture(scope="session")
def article(author):
    """A shared article owned by ``author``."""
    return create_article(author, "shared")


@pytest.fixture
def fresh_article(author, request):
    return create_article(author, request.node.name[:40])
