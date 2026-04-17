# Lab 12 - Complete Production Agent

Final project for Day 12. This service includes environment-based config, API-key auth, Redis-backed conversation history, Redis-backed rate limiting, monthly budget guard, health/readiness checks, structured logging, Docker packaging, and cloud deploy configs.

## Project Structure

```text
06-lab-complete/
|-- app/
|   |-- __init__.py
|   |-- auth.py
|   |-- config.py
|   |-- cost_guard.py
|   |-- main.py
|   |-- rate_limiter.py
|   `-- storage.py
|-- utils/
|   `-- mock_llm.py
|-- Dockerfile
|-- docker-compose.yml
|-- requirements.txt
|-- .env.example
|-- railway.toml
|-- render.yaml
`-- check_production_ready.py
```

## Run Locally

```bash
cp .env.example .env.local
# edit AGENT_API_KEY if needed

docker compose up --build
```

## Test Endpoints

```bash
curl http://localhost:8000/health
curl http://localhost:8000/ready
curl -X POST http://localhost:8000/ask \
  -H "X-API-Key: test-key-123" \
  -H "Content-Type: application/json" \
  -d '{"user_id":"student1","question":"What is deployment?"}'
curl -H "X-API-Key: test-key-123" http://localhost:8000/history/student1
```

## Deploy Railway

```bash
railway login
railway init
railway variables set AGENT_API_KEY=your-secret-key
railway variables set REDIS_URL=redis://...
railway up
railway domain
```

## Deploy Render

1. Push this folder to GitHub.
2. Create a new Blueprint service on Render.
3. Use `render.yaml`.
4. Set `AGENT_API_KEY`, `REDIS_URL`, and optional `OPENAI_API_KEY`.

## Verify Production Readiness

```bash
python check_production_ready.py
```
