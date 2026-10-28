"""GET article routes, tags, profile and user routes must NOT require x-acme-user (milestone 1)."""
import requests

from conftest import API, RUN_ID, tok


class TestArticleReads:
    def test_list_articles_no_acme(self, author, article, ev):
        # non-demo authors' articles are visible to themselves (pre-existing rule): list with author's JWT, no x-acme-user
        r = ev(requests.get(f"{API}/articles", params={"tag": RUN_ID, "limit": 100}, headers=tok(author["token"]), timeout=10),
               "GET", f"/api/articles?tag={RUN_ID}&limit=100")
        assert r.status_code == 200
        b = r.json()
        assert b["articlesCount"] >= 1 and any(a["slug"] == article["slug"] for a in b["articles"])

    def test_get_article_by_slug_no_acme(self, article, ev):
        ep = f"/api/articles/{article['slug']}"
        r = ev(requests.get(f"{API}/articles/{article['slug']}", timeout=10), "GET", ep)
        assert r.status_code == 200
        assert r.json()["article"]["title"] == article["title"]

    def test_get_article_not_found(self, ev):
        ep = f"/api/articles/no-such-slug-{RUN_ID}"
        r = ev(requests.get(f"{API}/articles/no-such-slug-{RUN_ID}", timeout=10), "GET", ep)
        assert r.status_code == 404
        assert r.json() == {"errors": {"article": ["not found"]}}

    def test_get_comments_no_acme(self, author, article, ev):
        cr = requests.post(f"{API}/articles/{article['slug']}/comments", json={"comment": {"body": f"rd {RUN_ID}"}},
                           headers={"x-acme-user": "ftrun-acme-user", **tok(author["token"])}, timeout=10)
        assert cr.status_code == 200
        ep = f"/api/articles/{article['slug']}/comments"
        r = ev(requests.get(f"{API}/articles/{article['slug']}/comments", headers=tok(author["token"]), timeout=10),
               "GET", ep)
        assert r.status_code == 200
        assert any(c["id"] == cr.json()["comment"]["id"] for c in r.json()["comments"])

    def test_feed_jwt_no_acme(self, other_user, author, article, ev):
        h = tok(other_user["token"])
        assert requests.post(f"{API}/profiles/{author['username']}/follow", headers=h, timeout=10).status_code == 200
        r = ev(requests.get(f"{API}/articles/feed", params={"limit": 50, "offset": 0}, headers=h, timeout=10),
               "GET", "/api/articles/feed?limit=50&offset=0")
        assert r.status_code == 200
        assert any(a["slug"] == article["slug"] for a in r.json()["articles"])

    def test_feed_without_jwt(self, ev):
        r = ev(requests.get(f"{API}/articles/feed", timeout=10), "GET", "/api/articles/feed")
        assert r.status_code == 401
        assert r.json() == {"status": "error", "message": "missing authorization credentials"}


class TestTags:
    def test_get_tags_no_acme(self, article, ev):
        r = ev(requests.get(f"{API}/tags", timeout=10), "GET", "/api/tags")
        assert r.status_code == 200
        assert isinstance(r.json()["tags"], list) and len(r.json()["tags"]) <= 10


class TestProfiles:
    def test_get_profile_no_acme(self, author, ev):
        ep = f"/api/profiles/{author['username']}"
        r = ev(requests.get(f"{API}/profiles/{author['username']}", timeout=10), "GET", ep)
        assert r.status_code == 200
        assert r.json()["profile"]["username"] == author["username"]
        assert r.json()["profile"]["following"] is False

    def test_get_profile_not_found(self, ev):
        ep = f"/api/profiles/nosuchuser_{RUN_ID}"
        r = ev(requests.get(f"{API}/profiles/nosuchuser_{RUN_ID}", timeout=10), "GET", ep)
        assert r.status_code == 404

    def test_follow_no_acme(self, author, other_user, ev):
        ep = f"/api/profiles/{author['username']}/follow"
        r = ev(requests.post(f"{API}/profiles/{author['username']}/follow", headers=tok(other_user["token"]),
                             timeout=10), "POST", ep)
        assert r.status_code == 200
        assert r.json()["profile"]["following"] is True

    def test_unfollow_no_acme(self, author, other_user, ev):
        h = tok(other_user["token"])
        requests.post(f"{API}/profiles/{author['username']}/follow", headers=h, timeout=10)
        ep = f"/api/profiles/{author['username']}/follow"
        r = ev(requests.delete(f"{API}/profiles/{author['username']}/follow", headers=h, timeout=10), "DELETE", ep)
        assert r.status_code == 200
        assert r.json()["profile"]["following"] is False

    def test_follow_without_jwt(self, author, ev):
        ep = f"/api/profiles/{author['username']}/follow"
        r = ev(requests.post(f"{API}/profiles/{author['username']}/follow", timeout=10), "POST", ep)
        assert r.status_code == 401


class TestCurrentUser:
    def test_get_current_user_no_acme(self, author, ev):
        r = ev(requests.get(f"{API}/user", headers=tok(author["token"]), timeout=10), "GET", "/api/user")
        assert r.status_code == 200
        assert r.json()["user"]["username"] == author["username"]

    def test_update_current_user_no_acme(self, other_user, ev):
        body = {"user": {"bio": f"bio {RUN_ID}"}}
        r = ev(requests.put(f"{API}/user", json=body, headers=tok(other_user["token"]), timeout=10),
               "PUT", "/api/user", body)
        assert r.status_code == 200
        assert r.json()["user"]["bio"] == f"bio {RUN_ID}"

    def test_get_current_user_without_jwt(self, ev):
        r = ev(requests.get(f"{API}/user", timeout=10), "GET", "/api/user")
        assert r.status_code == 401
        assert r.json() == {"status": "error", "message": "missing authorization credentials"}
