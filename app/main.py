import json
import os
from dataclasses import dataclass
from http import HTTPStatus
from typing import Any, Dict, List, Optional, Tuple
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


@dataclass
class IMessageEvent:
    sender: str
    text: str
    repository: str


class GitHubClient:
    def __init__(self, token: Optional[str] = None):
        self.token = token

    def _request(self, url: str) -> Any:
        headers = {"Accept": "application/vnd.github+json", "User-Agent": "imessage-chatbot"}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"

        req = Request(url, headers=headers)
        try:
            with urlopen(req, timeout=10) as response:
                return json.loads(response.read().decode("utf-8"))
        except HTTPError as exc:
            if exc.code == HTTPStatus.NOT_FOUND:
                raise ValueError("Repository not found") from exc
            raise

    def fetch_repo_snapshot(self, repo: str) -> Dict[str, Any]:
        repo_data = self._request(f"https://api.github.com/repos/{repo}")
        issues_url = (
            f"https://api.github.com/repos/{repo}/issues?"
            + urlencode({"state": "open", "per_page": 5})
        )
        issues = self._request(issues_url)

        open_issues = [
            {"number": issue["number"], "title": issue["title"], "url": issue["html_url"]}
            for issue in issues
            if "pull_request" not in issue
        ]

        return {
            "name": repo_data["full_name"],
            "description": repo_data.get("description") or "No description provided.",
            "open_issues": open_issues,
        }


class AIResponder:
    def __init__(self, api_key: Optional[str] = None, model: str = "gpt-4o-mini"):
        self.api_key = api_key
        self.model = model

    def build_fallback(self, prompt: str, snapshot: Dict[str, Any]) -> str:
        issue_lines = "\n".join(
            [f"- #{item['number']}: {item['title']}" for item in snapshot["open_issues"][:3]]
        ) or "- No open issues found"

        return (
            f"You asked: '{prompt}'.\n"
            f"Repo: {snapshot['name']}\n"
            f"Summary: {snapshot['description']}\n"
            f"Top issues:\n{issue_lines}\n"
            "(Set OPENAI_API_KEY for richer AI responses.)"
        )

    def _openai_response(self, prompt: str, snapshot: Dict[str, Any]) -> str:
        payload = {
            "model": self.model,
            "input": (
                "You are an assistant replying to iMessage users about GitHub repositories. "
                "Keep answers concise and actionable.\n"
                f"User message: {prompt}\n"
                f"Repository context: {snapshot}"
            ),
        }
        req = Request(
            "https://api.openai.com/v1/responses",
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        with urlopen(req, timeout=15) as response:
            data = json.loads(response.read().decode("utf-8"))

        return data.get("output_text") or self.build_fallback(prompt, snapshot)

    def generate(self, prompt: str, snapshot: Dict[str, Any]) -> str:
        if not self.api_key:
            return self.build_fallback(prompt, snapshot)

        try:
            return self._openai_response(prompt, snapshot)
        except Exception:
            return self.build_fallback(prompt, snapshot)


def handle_imessage_event(event: IMessageEvent) -> Dict[str, Any]:
    github = GitHubClient(token=os.getenv("GITHUB_TOKEN"))
    snapshot = github.fetch_repo_snapshot(event.repository)

    responder = AIResponder(
        api_key=os.getenv("OPENAI_API_KEY"),
        model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
    )
    reply = responder.generate(event.text, snapshot)

    return {"reply": reply, "context": snapshot}


def app(environ, start_response):
    path = environ.get("PATH_INFO", "")
    method = environ.get("REQUEST_METHOD", "GET")

    if path == "/health" and method == "GET":
        body = json.dumps({"status": "ok"}).encode("utf-8")
        start_response("200 OK", [("Content-Type", "application/json")])
        return [body]

    if path == "/webhook/imessage" and method == "POST":
        try:
            length = int(environ.get("CONTENT_LENGTH", "0") or "0")
            raw = environ["wsgi.input"].read(length)
            payload = json.loads(raw.decode("utf-8"))
            event = IMessageEvent(**payload)
            result = handle_imessage_event(event)
            body = json.dumps(result).encode("utf-8")
            start_response("200 OK", [("Content-Type", "application/json")])
            return [body]
        except ValueError as exc:
            body = json.dumps({"error": str(exc)}).encode("utf-8")
            start_response("404 Not Found", [("Content-Type", "application/json")])
            return [body]
        except Exception as exc:
            body = json.dumps({"error": f"invalid request: {exc}"}).encode("utf-8")
            start_response("400 Bad Request", [("Content-Type", "application/json")])
            return [body]

    body = json.dumps({"error": "not found"}).encode("utf-8")
    start_response("404 Not Found", [("Content-Type", "application/json")])
    return [body]


def run() -> None:
    from wsgiref.simple_server import make_server

    port = int(os.getenv("PORT", "8000"))
    server = make_server("0.0.0.0", port, app)
    print(f"Server listening on http://0.0.0.0:{port}")
    server.serve_forever()


if __name__ == "__main__":
    run()
