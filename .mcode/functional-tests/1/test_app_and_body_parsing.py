"""App root, express.json()/express.urlencoded() body parsing and error handling (milestone 1)."""
import json

import requests

from conftest import ACME, API, BASE_URL, RUN_ID, _created_slugs, tok


class TestRoot:
    def test_root_status(self, ev):
        r = ev(requests.get(f"{BASE_URL}/", timeout=10), "GET", "/")
        assert r.status_code == 200
        assert r.json() == {"status": "API is running on /api"}


class TestJsonBodies:
    def test_register_json(self, ev):
        name = f"json_{RUN_ID}"
        body = {"user": {"email": f"{name}@example.com", "username": name, "password": "pw-ftrun-123"}}
        r = ev(requests.post(f"{API}/users", json=body, timeout=10), "POST", "/api/users", body)
        assert r.status_code == 201
        u = r.json()["user"]
        assert u["username"] == name and u["email"] == f"{name}@example.com" and u["token"]

    def test_login_json(self, author, ev):
        body = {"user": {"email": author["email"], "password": "pw-ftrun-123"}}
        r = ev(requests.post(f"{API}/users/login", json=body, timeout=10), "POST", "/api/users/login", body)
        assert r.status_code == 200
        assert r.json()["user"]["username"] == author["username"] and r.json()["user"]["token"]

    def test_login_json_wrong_password(self, author, ev):
        body = {"user": {"email": author["email"], "password": "wrong"}}
        r = ev(requests.post(f"{API}/users/login", json=body, timeout=10), "POST", "/api/users/login", body)
        assert r.status_code == 403

    def test_register_json_missing_email(self, ev):
        body = {"user": {"username": f"noemail_{RUN_ID}", "password": "pw"}}
        r = ev(requests.post(f"{API}/users", json=body, timeout=10), "POST", "/api/users", body)
        assert r.status_code == 422
        assert r.json() == {"errors": {"email": ["can't be blank"]}}


class TestUrlencodedBodies:
    def test_register_urlencoded(self, ev):
        name = f"form_{RUN_ID}"
        form = {"user[email]": f"{name}@example.com", "user[username]": name, "user[password]": "pw-ftrun-123"}
        r = ev(requests.post(f"{API}/users", data=form, timeout=10), "POST", "/api/users", form)
        assert r.status_code == 201
        assert r.json()["user"]["username"] == name

    def test_login_urlencoded(self, author, ev):
        form = {"user[email]": author["email"], "user[password]": "pw-ftrun-123"}
        r = ev(requests.post(f"{API}/users/login", data=form, timeout=10), "POST", "/api/users/login", form)
        assert r.status_code == 200
        assert r.json()["user"]["username"] == author["username"]

    def test_create_article_urlencoded(self, author, ev):
        title = f"FT form article {RUN_ID}"
        form = {"article[title]": title, "article[description]": "form d", "article[body]": "form b",
                "article[tagList][]": [RUN_ID, "ftform"]}
        r = ev(requests.post(f"{API}/articles", data=form, headers={**ACME, **tok(author["token"])}, timeout=10),
               "POST", "/api/articles", form)
        assert r.status_code == 201
        art = r.json()["article"]
        _created_slugs.append((art["slug"], author["token"]))
        assert art["title"] == title and art["body"] == "form b"
        assert sorted(art["tagList"]) == sorted([RUN_ID, "ftform"])


class TestBodyParserErrors:
    def test_malformed_json_body(self, ev):
        raw = '{"user": {bad json'
        r = ev(requests.post(f"{API}/users", data=raw, headers={"Content-Type": "application/json"}, timeout=10),
               "POST", "/api/users", raw)
        # Original global error handler turns body-parser errors (no errorCode) into 500 + message string
        assert r.status_code == 500
        assert isinstance(r.json(), str) and "JSON" in r.json()

    def test_json_body_over_100kb_limit(self, ev):
        big = {"user": {"email": "x@example.com", "username": "big", "password": "p" * (110 * 1024)}}
        r = ev(requests.post(f"{API}/users", data=json.dumps(big), headers={"Content-Type": "application/json"},
                             timeout=10), "POST", "/api/users", "<~110KB JSON body>")
        assert r.status_code == 500
        assert "too large" in r.text.lower()

    def test_json_body_just_under_limit_parses(self, ev):
        # ~90KB body parses fine (limit is 100kb); missing username => 422 from service, proving parse succeeded
        big = {"user": {"email": f"near_{RUN_ID}@example.com", "password": "p", "pad": "x" * (90 * 1024)}}
        r = ev(requests.post(f"{API}/users", json=big, timeout=10), "POST", "/api/users", "<~90KB JSON body>")
        assert r.status_code == 422
        assert r.json() == {"errors": {"username": ["can't be blank"]}}
