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

## Run locally (desktop/server)

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

---

## I’m on iPad — how do I use this?

You usually **won’t run this Python server directly on iPad**. Instead:

1. Host this service on a small cloud runtime (Railway, Render, Fly.io, or a VPS).
2. Set environment variables there (`OPENAI_API_KEY`, optional `GITHUB_TOKEN`).
3. Use the public HTTPS URL as your iMessage bridge webhook target.

### iPad-first setup flow

1. Push this repo to GitHub.
2. Open your cloud host app/site in Safari.
3. Create a new service from your GitHub repo.
4. Add env vars:
   - `OPENAI_API_KEY=...`
   - `GITHUB_TOKEN=...` (optional)
5. Deploy.
6. Copy your public URL, for example:
   - `https://your-bot.example.com/webhook/imessage`
7. Paste that URL into your iMessage bridge's incoming webhook config.

### Quick test from iPad (no terminal)

Use an API client app (e.g. HTTPBot, Postman mobile, or any REST client), then send:

- Method: `POST`
- URL: `https://your-bot.example.com/webhook/imessage`
- Header: `Content-Type: application/json`
- Body:

```json
{
  "sender": "+15551234567",
  "text": "Summarize open issues",
  "repository": "octocat/Hello-World"
}
```

You should get:

```json
{
  "reply": "...",
  "context": {
    "name": "octocat/Hello-World",
    "description": "...",
    "open_issues": []
  }
}
```

### Health check URL

Open this in Safari to verify deployment is up:

- `https://your-bot.example.com/health`

Expected response:

```json
{"status":"ok"}
```


## Render setup (recommended for iPad users)

Since you're deploying on Render, this repo now includes a `render.yaml` blueprint for one-click setup.

### Option A: Blueprint deploy (fastest)

1. Push this repository to GitHub.
2. In Render, click **New +** → **Blueprint**.
3. Select your repo. Render will read `render.yaml` automatically.
4. In the service settings, set secret environment variables:
   - `OPENAI_API_KEY` (required for AI responses)
   - `GITHUB_TOKEN` (optional but recommended for higher GitHub API limits)
5. Deploy.

### Option B: Manual Web Service deploy

If you prefer manual setup, create a Python Web Service with:

- **Build Command**: `pip install -r requirements.txt`
- **Start Command**: `python app/main.py`
- **Environment Variables**:
  - `PORT=10000`
  - `OPENAI_MODEL=gpt-4o-mini`
  - `OPENAI_API_KEY=...`
  - `GITHUB_TOKEN=...` (optional)

### Render health check and webhook URL

After deploy, verify:

- `https://<your-render-service>.onrender.com/health`

Then configure your iMessage bridge webhook URL as:

- `https://<your-render-service>.onrender.com/webhook/imessage`

## iMessage integration note

Use any iMessage bridge that can forward incoming messages to webhooks, then send the returned `reply` back to the user through that bridge.
