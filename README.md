# iMessage GitHub AI Chatbot

A lightweight Python chatbot service that can sit behind an iMessage webhook bridge, use GitHub API context, and produce AI-assisted replies.

## Features

- Receives iMessage-like webhook events at `POST /webhook/imessage`.
- Fetches repository details and open issues from GitHub API.
- Builds an AI reply using OpenAI Responses API when `OPENAI_API_KEY` is set.
- Falls back to a deterministic summary response if no AI key is configured.
- Uses only Python standard library for runtime dependencies.

## Environment variables

- `GITHUB_TOKEN` (optional, raises GitHub rate limits)
- `OPENAI_API_KEY` (optional, enables AI output)
- `OPENAI_MODEL` (optional, default: `gpt-4o-mini`)
- `PORT` (optional, default: `8000`)

## Run

```bash
python app/main.py
```

## Example request

```bash
curl -X POST http://localhost:8000/webhook/imessage \
  -H "Content-Type: application/json" \
  -d '{
    "sender": "+15551234567",
    "text": "What should I work on next?",
    "repository": "octocat/Hello-World"
  }'
```

## iMessage integration note

Use any iMessage bridge that can forward incoming messages to webhooks, then send the returned `reply` back to the user through that bridge.
