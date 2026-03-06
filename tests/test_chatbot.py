import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import io
import json

from app.main import AIResponder, IMessageEvent, app, handle_imessage_event


def test_fallback_response_contains_issue_summary():
    responder = AIResponder(api_key=None)
    snapshot = {
        "name": "octocat/Hello-World",
        "description": "Example",
        "open_issues": [
            {"number": 1, "title": "Bug", "url": "https://example.com/1"},
            {"number": 2, "title": "Feature", "url": "https://example.com/2"},
        ],
    }

    message = responder.generate("Any updates?", snapshot)

    assert "Any updates?" in message
    assert "#1: Bug" in message
    assert "Set OPENAI_API_KEY" in message


def test_health_endpoint_wsgi():
    status_holder = {}

    def start_response(status, _headers):
        status_holder["status"] = status

    result = b"".join(app({"PATH_INFO": "/health", "REQUEST_METHOD": "GET"}, start_response))
    assert status_holder["status"] == "200 OK"
    assert json.loads(result.decode("utf-8")) == {"status": "ok"}


def test_webhook_endpoint_with_stubbed_handler(monkeypatch):
    def fake_handler(event: IMessageEvent):
        assert event.sender == "+15551234567"
        return {"reply": "hello", "context": {"name": event.repository}}

    monkeypatch.setattr("app.main.handle_imessage_event", fake_handler)

    payload = {
        "sender": "+15551234567",
        "text": "What should I work on next?",
        "repository": "octocat/Hello-World",
    }
    body = json.dumps(payload).encode("utf-8")
    environ = {
        "PATH_INFO": "/webhook/imessage",
        "REQUEST_METHOD": "POST",
        "CONTENT_LENGTH": str(len(body)),
        "wsgi.input": io.BytesIO(body),
    }
    status_holder = {}

    def start_response(status, _headers):
        status_holder["status"] = status

    result = b"".join(app(environ, start_response))

    assert status_holder["status"] == "200 OK"
    assert json.loads(result.decode("utf-8"))["reply"] == "hello"
