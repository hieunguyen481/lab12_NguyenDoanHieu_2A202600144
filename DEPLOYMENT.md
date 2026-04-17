# Deployment Information

## Public URL
Current verified Railway deployment URL:

`https://day12-railway-agent-production.up.railway.app`

This URL was deployed and tested successfully during Part 3.

## Platform
Railway

## Deployment Status
- Railway deployment is live and publicly accessible
- `GET /health` on Railway works
- `POST /ask` on Railway works when using JSON body
- Final project `06-lab-complete` has been verified locally with Docker and passed the production readiness checker (`20/20`)

## Test Commands

### Health Check
```bash
curl https://day12-railway-agent-production.up.railway.app/health
```

Expected behavior: return JSON with `"status":"ok"`

### API Test On Railway
```bash
curl -X POST https://day12-railway-agent-production.up.railway.app/ask \
  -H "Content-Type: application/json" \
  -d '{"question":"Hello"}'
```

### Local Final Project Test
```bash
curl http://localhost:8000/health

curl -X POST http://localhost:8000/ask \
  -H "X-API-Key: test-key-123" \
  -H "Content-Type: application/json" \
  -d '{"user_id":"student1","question":"What is deployment?"}'

curl -H "X-API-Key: test-key-123" \
  http://localhost:8000/history/student1
```

## Verified Results

### Railway health check
```json
{"status":"ok","uptime_seconds":229.0,"platform":"Railway","timestamp":"2026-04-17T03:48:41.469970+00:00"}
```

### Railway ask endpoint
```json
{"question":"Hello","answer":"Agent đang hoạt động tốt! (mock response) Hỏi thêm câu hỏi đi nhé.","platform":"Railway"}
```

### Final project local health check
```json
{"status":"ok","version":"1.0.0","environment":"staging","uptime_seconds":7.6,"total_requests":2,"checks":{"llm":"mock"},"timestamp":"2026-04-17T05:07:21.865542+00:00"}
```

### Final project local ask endpoint
```json
{"user_id":"student1","question":"What is deployment?","answer":"Deployment moves your application from local development to a reachable runtime environment.","model":"gpt-4o-mini","timestamp":"2026-04-17T05:07:21.969825+00:00","history_length":2,"budget_remaining_usd":9.999985,"requests_remaining":9}
```

### Final project local history endpoint
```json
{"user_id":"student1","messages":[{"role":"user","content":"What is deployment?","timestamp":"2026-04-17T05:07:21.893137Z"},{"role":"assistant","content":"Deployment moves your application from local development to a reachable runtime environment.","timestamp":"2026-04-17T05:07:21.969543Z"}]}
```

## Environment Variables Used
- `PORT`
- `REDIS_URL`
- `AGENT_API_KEY`
- `LOG_LEVEL`
- `RATE_LIMIT_PER_MINUTE`
- `MONTHLY_BUDGET_USD`
- `HISTORY_TTL_SECONDS`
- `ALLOWED_ORIGINS`

## Screenshots
- Folder available: `screenshots/`
- Current status: screenshot files have not been added yet
- Recommended files to add before submission:
  - `screenshots/dashboard.png`
  - `screenshots/running.png`
  - `screenshots/test.png`

## Important Note
The current public Railway URL belongs to the verified Part 3 deployment sample.  
If your instructor requires the public URL to point specifically to the final Part 6 project, you should redeploy `06-lab-complete` to Railway or Render before final submission.
