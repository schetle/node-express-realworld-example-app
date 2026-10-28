"""Article write routes require BOTH x-acme-user and a valid JWT (milestone 1)."""
import requests

from conftest import ACME, API, BASE_URL, RUN_ID, _created_slugs, create_article, tok


def get_article(slug, token=None):
    headers = tok(token) if token else {}
    return requests.get(f"{API}/articles/{slug}", headers=headers, timeout=10)


# --------------------------------------------------------------------------- happy paths
class TestCreateArticle:
    def test_create_article_with_acme_and_jwt(self, author, ev):
        title = f"FT create {RUN_ID}"
        body = {"article": {"title": title, "description": "d", "body": "b", "tagList": [RUN_ID, "ftcreate"]}}
        r = ev(requests.post(f"{API}/articles", json=body, headers={**ACME, **tok(author["token"])}, timeout=10),
               "POST", "/api/articles", body)
        assert r.status_code == 201
        art = r.json()["article"]
        _created_slugs.append((art["slug"], author["token"]))
        assert art["title"] == title
        assert art["author"]["username"] == author["username"]
        assert sorted(art["tagList"]) == sorted([RUN_ID, "ftcreate"])
        assert get_article(art["slug"]).status_code == 200

    def test_create_article_without_acme_header(self, author, ev):
        title = f"FT noacme {RUN_ID}"
        body = {"article": {"title": title, "description": "d", "body": "b"}}
        r = ev(requests.post(f"{API}/articles", json=body, headers=tok(author["token"]), timeout=10),
               "POST", "/api/articles", body)
        assert r.status_code == 401
        assert r.json() == {"error": "acme auth required"}
        # no side effect: article with that slug must not exist
        lst = requests.get(f"{API}/articles", params={"author": author["username"], "limit": 100},
                           headers=tok(author["token"]), timeout=10).json()
        assert lst["articlesCount"] >= 1  # author's own articles are visible to the author
        assert all(a["title"] != title for a in lst["articles"])

    def test_create_article_acme_without_jwt(self, author, ev):
        title = f"FT nojwt {RUN_ID}"
        body = {"article": {"title": title, "description": "d", "body": "b"}}
        r = ev(requests.post(f"{API}/articles", json=body, headers=ACME, timeout=10), "POST", "/api/articles", body)
        assert r.status_code == 401
        assert r.json()["message"] == "missing authorization credentials"
        lst = requests.get(f"{API}/articles", params={"author": author["username"], "limit": 100},
                           headers=tok(author["token"]), timeout=10).json()
        assert lst["articlesCount"] >= 1  # author's own articles are visible to the author
        assert all(a["title"] != title for a in lst["articles"])

    def test_create_article_acme_with_invalid_jwt(self, ev):
        body = {"article": {"title": f"FT badjwt {RUN_ID}", "description": "d", "body": "b"}}
        r = ev(requests.post(f"{API}/articles", json=body, headers={**ACME, **tok("not.a.jwt")}, timeout=10),
               "POST", "/api/articles", body)
        assert r.status_code == 401

    def test_create_article_missing_title(self, author, ev):
        body = {"article": {"description": "d", "body": "b"}}
        r = ev(requests.post(f"{API}/articles", json=body, headers={**ACME, **tok(author["token"])}, timeout=10),
               "POST", "/api/articles", body)
        assert r.status_code == 422
        assert r.json() == {"errors": {"title": ["can't be blank"]}}

    def test_create_article_duplicate_title(self, author, article, ev):
        body = {"article": {"title": article["title"], "description": "d", "body": "b"}}
        r = ev(requests.post(f"{API}/articles", json=body, headers={**ACME, **tok(author["token"])}, timeout=10),
               "POST", "/api/articles", body)
        assert r.status_code == 422
        assert r.json() == {"errors": {"title": ["must be unique"]}}


class TestUpdateArticle:
    def test_update_article_with_acme_and_jwt(self, author, fresh_article, ev):
        body = {"article": {"description": "updated desc", "body": "updated body"}}
        ep = f"/api/articles/{fresh_article['slug']}"
        r = ev(requests.put(f"{BASE_URL}{ep}", json=body,
                            headers={**ACME, **tok(author["token"])}, timeout=10), "PUT", ep, body)
        assert r.status_code == 200
        art = r.json()["article"]
        assert art["description"] == "updated desc" and art["body"] == "updated body"
        assert get_article(fresh_article["slug"]).json()["article"]["body"] == "updated body"

    def test_update_article_without_acme_header(self, author, fresh_article, ev):
        body = {"article": {"body": "should not apply"}}
        ep = f"/api/articles/{fresh_article['slug']}"
        r = ev(requests.put(f"{BASE_URL}{ep}", json=body,
                            headers=tok(author["token"]), timeout=10), "PUT", ep, body)
        assert r.status_code == 401
        assert r.json() == {"error": "acme auth required"}
        assert get_article(fresh_article["slug"]).json()["article"]["body"] == "ft body"

    def test_update_article_acme_without_jwt(self, fresh_article, ev):
        body = {"article": {"body": "should not apply"}}
        ep = f"/api/articles/{fresh_article['slug']}"
        r = ev(requests.put(f"{BASE_URL}{ep}", json=body, headers=ACME, timeout=10),
               "PUT", ep, body)
        assert r.status_code == 401
        assert get_article(fresh_article["slug"]).json()["article"]["body"] == "ft body"

    def test_update_article_not_owner(self, other_user, article, ev):
        body = {"article": {"body": "hijack"}}
        ep = f"/api/articles/{article['slug']}"
        r = ev(requests.put(f"{BASE_URL}{ep}", json=body,
                            headers={**ACME, **tok(other_user["token"])}, timeout=10), "PUT", ep, body)
        assert r.status_code == 403

    def test_update_article_not_found(self, author, ev):
        body = {"article": {"body": "x"}}
        ep = f"/api/articles/no-such-slug-{RUN_ID}"
        r = ev(requests.put(f"{BASE_URL}{ep}", json=body, headers={**ACME, **tok(author["token"])}, timeout=10),
               "PUT", ep, body)
        assert r.status_code == 404


class TestDeleteArticle:
    def test_delete_article_with_acme_and_jwt(self, author, ev):
        art = create_article(author, "todelete")
        ep = f"/api/articles/{art['slug']}"
        r = ev(requests.delete(f"{BASE_URL}{ep}", headers={**ACME, **tok(author["token"])}, timeout=10), "DELETE", ep)
        assert r.status_code == 204
        assert get_article(art["slug"]).status_code == 404

    def test_delete_article_without_acme_header(self, author, fresh_article, ev):
        ep = f"/api/articles/{fresh_article['slug']}"
        r = ev(requests.delete(f"{BASE_URL}{ep}", headers=tok(author["token"]), timeout=10), "DELETE", ep)
        assert r.status_code == 401
        assert r.json() == {"error": "acme auth required"}
        assert get_article(fresh_article["slug"]).status_code == 200

    def test_delete_article_acme_without_jwt(self, fresh_article, ev):
        ep = f"/api/articles/{fresh_article['slug']}"
        r = ev(requests.delete(f"{BASE_URL}{ep}", headers=ACME, timeout=10), "DELETE", ep)
        assert r.status_code == 401
        assert get_article(fresh_article["slug"]).status_code == 200

    def test_delete_article_not_owner(self, other_user, article, ev):
        ep = f"/api/articles/{article['slug']}"
        r = ev(requests.delete(f"{BASE_URL}{ep}", headers={**ACME, **tok(other_user["token"])}, timeout=10),
               "DELETE", ep)
        assert r.status_code == 403
        assert get_article(article["slug"]).status_code == 200


class TestComments:
    def _add(self, user, slug, text="ft comment"):
        return requests.post(f"{API}/articles/{slug}/comments", json={"comment": {"body": text}},
                             headers={**ACME, **tok(user["token"])}, timeout=10)

    def _list(self, slug, token):
        # non-demo comments are only visible to their author (pre-existing rule), so list as the author
        return requests.get(f"{API}/articles/{slug}/comments", headers=tok(token), timeout=10).json()["comments"]

    def test_add_comment_with_acme_and_jwt(self, author, article, ev):
        body = {"comment": {"body": f"hello {RUN_ID}"}}
        ep = f"/api/articles/{article['slug']}/comments"
        r = ev(requests.post(f"{BASE_URL}{ep}", json=body, headers={**ACME, **tok(author["token"])}, timeout=10),
               "POST", ep, body)
        assert r.status_code == 200
        c = r.json()["comment"]
        assert c["body"] == f"hello {RUN_ID}" and c["author"]["username"] == author["username"]
        assert any(x["id"] == c["id"] for x in self._list(article["slug"], author["token"]))

    def test_add_comment_without_acme_header(self, author, article, ev):
        text = f"noacme {RUN_ID}"
        body = {"comment": {"body": text}}
        ep = f"/api/articles/{article['slug']}/comments"
        r = ev(requests.post(f"{BASE_URL}{ep}", json=body, headers=tok(author["token"]), timeout=10), "POST", ep, body)
        assert r.status_code == 401
        assert r.json() == {"error": "acme auth required"}
        assert all(x["body"] != text for x in self._list(article["slug"], author["token"]))

    def test_add_comment_acme_without_jwt(self, author, article, ev):
        text = f"nojwt {RUN_ID}"
        body = {"comment": {"body": text}}
        ep = f"/api/articles/{article['slug']}/comments"
        r = ev(requests.post(f"{BASE_URL}{ep}", json=body, headers=ACME, timeout=10), "POST", ep, body)
        assert r.status_code == 401
        assert all(x["body"] != text for x in self._list(article["slug"], author["token"]))

    def test_add_comment_empty_body(self, author, article, ev):
        body = {"comment": {"body": ""}}
        ep = f"/api/articles/{article['slug']}/comments"
        r = ev(requests.post(f"{BASE_URL}{ep}", json=body, headers={**ACME, **tok(author["token"])}, timeout=10),
               "POST", ep, body)
        assert r.status_code == 422
        assert r.json() == {"errors": {"body": ["can't be blank"]}}

    def test_delete_comment_with_acme_and_jwt(self, author, article, ev):
        cid = self._add(author, article["slug"]).json()["comment"]["id"]
        ep = f"/api/articles/{article['slug']}/comments/{cid}"
        r = ev(requests.delete(f"{BASE_URL}{ep}", headers={**ACME, **tok(author["token"])}, timeout=10), "DELETE", ep)
        assert r.status_code == 200
        assert r.json() == {}
        assert all(x["id"] != cid for x in self._list(article["slug"], author["token"]))

    def test_delete_comment_without_acme_header(self, author, article, ev):
        cid = self._add(author, article["slug"]).json()["comment"]["id"]
        ep = f"/api/articles/{article['slug']}/comments/{cid}"
        r = ev(requests.delete(f"{BASE_URL}{ep}", headers=tok(author["token"]), timeout=10), "DELETE", ep)
        assert r.status_code == 401
        assert r.json() == {"error": "acme auth required"}
        assert any(x["id"] == cid for x in self._list(article["slug"], author["token"]))

    def test_delete_comment_acme_without_jwt(self, author, article, ev):
        cid = self._add(author, article["slug"]).json()["comment"]["id"]
        ep = f"/api/articles/{article['slug']}/comments/{cid}"
        r = ev(requests.delete(f"{BASE_URL}{ep}", headers=ACME, timeout=10), "DELETE", ep)
        assert r.status_code == 401
        assert any(x["id"] == cid for x in self._list(article["slug"], author["token"]))

    def test_delete_comment_not_found(self, author, article, ev):
        ep = f"/api/articles/{article['slug']}/comments/999999999"
        r = ev(requests.delete(f"{BASE_URL}{ep}", headers={**ACME, **tok(author["token"])}, timeout=10), "DELETE", ep)
        assert r.status_code == 404


class TestFavorite:
    def test_favorite_with_acme_and_jwt(self, other_user, fresh_article, ev):
        ep = f"/api/articles/{fresh_article['slug']}/favorite"
        r = ev(requests.post(f"{BASE_URL}{ep}", headers={**ACME, **tok(other_user["token"])}, timeout=10), "POST", ep)
        assert r.status_code == 200
        art = r.json()["article"]
        assert art["favorited"] is True and art["favoritesCount"] == 1

    def test_favorite_without_acme_header(self, other_user, fresh_article, ev):
        ep = f"/api/articles/{fresh_article['slug']}/favorite"
        r = ev(requests.post(f"{BASE_URL}{ep}", headers=tok(other_user["token"]), timeout=10), "POST", ep)
        assert r.status_code == 401
        assert r.json() == {"error": "acme auth required"}
        assert get_article(fresh_article["slug"]).json()["article"]["favoritesCount"] == 0

    def test_favorite_acme_without_jwt(self, fresh_article, ev):
        ep = f"/api/articles/{fresh_article['slug']}/favorite"
        r = ev(requests.post(f"{BASE_URL}{ep}", headers=ACME, timeout=10), "POST", ep)
        assert r.status_code == 401
        assert get_article(fresh_article["slug"]).json()["article"]["favoritesCount"] == 0

    def test_unfavorite_with_acme_and_jwt(self, other_user, fresh_article, ev):
        h = {**ACME, **tok(other_user["token"])}
        assert requests.post(f"{API}/articles/{fresh_article['slug']}/favorite", headers=h, timeout=10).status_code == 200
        ep = f"/api/articles/{fresh_article['slug']}/favorite"
        r = ev(requests.delete(f"{BASE_URL}{ep}", headers=h, timeout=10), "DELETE", ep)
        assert r.status_code == 200
        art = r.json()["article"]
        assert art["favorited"] is False and art["favoritesCount"] == 0

    def test_unfavorite_without_acme_header(self, other_user, fresh_article, ev):
        h = {**ACME, **tok(other_user["token"])}
        assert requests.post(f"{API}/articles/{fresh_article['slug']}/favorite", headers=h, timeout=10).status_code == 200
        ep = f"/api/articles/{fresh_article['slug']}/favorite"
        r = ev(requests.delete(f"{BASE_URL}{ep}", headers=tok(other_user["token"]), timeout=10), "DELETE", ep)
        assert r.status_code == 401
        assert r.json() == {"error": "acme auth required"}
        a = get_article(fresh_article["slug"], other_user["token"]).json()["article"]
        assert a["favorited"] is True and a["favoritesCount"] == 1

    def test_unfavorite_acme_without_jwt(self, other_user, fresh_article, ev):
        h = {**ACME, **tok(other_user["token"])}
        assert requests.post(f"{API}/articles/{fresh_article['slug']}/favorite", headers=h, timeout=10).status_code == 200
        ep = f"/api/articles/{fresh_article['slug']}/favorite"
        r = ev(requests.delete(f"{BASE_URL}{ep}", headers=ACME, timeout=10), "DELETE", ep)
        assert r.status_code == 401
        assert get_article(fresh_article["slug"]).json()["article"]["favoritesCount"] == 1
