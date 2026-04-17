# Day 12 Lab - Mission Answers

## Part 1: Localhost vs Production

### Exercise 1.1: Anti-patterns found
1. `OPENAI_API_KEY` được hardcode trực tiếp trong code (`develop/app.py`), rất nguy hiểm nếu push lên GitHub vì secret sẽ bị lộ ngay.
2. `DATABASE_URL` cũng bị hardcode kèm username và password, khiến config nhạy cảm bị trộn vào source code thay vì tách ra bằng environment variables.
3. App dùng các biến cấu hình như `DEBUG = True` và `MAX_TOKENS = 500` ngay trong code, không có config management để đổi theo môi trường dev/staging/production.
4. Endpoint `/ask` dùng `print()` để log request và response thay vì structured logging, làm log khó theo dõi khi deploy thật.
5. Code còn log cả secret qua dòng `print(f"[DEBUG] Using key: {OPENAI_API_KEY}")`, đây là anti-pattern nghiêm trọng vì key có thể lộ trong logs.
6. Không có endpoint health check như `/health`, nên platform cloud khó phát hiện app đã chết để tự restart.
7. App bind vào `localhost` thay vì `0.0.0.0`, nên chỉ phù hợp local machine và không phù hợp khi chạy trong container/cloud.
8. Port bị hardcode là `8000`, không đọc từ biến môi trường `PORT`, nên dễ lỗi khi deploy lên Railway/Render.
9. `reload=True` được bật sẵn trong lệnh chạy app, phù hợp cho development nhưng không phù hợp cho production.
10. API thiết kế còn đơn giản, endpoint `/ask` nhận `question` qua query parameter thay vì JSON body, nên khó mở rộng schema request về sau.

### Exercise 1.3: Comparison table
| Feature | Develop | Production | Why Important? |
|---------|---------|------------|----------------|
| Config | Hardcode trực tiếp trong code (`OPENAI_API_KEY`, `DATABASE_URL`, `DEBUG`, `PORT`) | Đọc config từ `settings` và environment variables | Giúp tách code khỏi config, dễ đổi môi trường và tránh lộ secrets |
| Request format | Nhận `question` qua query parameter | Nhận `question` qua JSON body | JSON body rõ ràng hơn, dễ validate và dễ mở rộng API |
| Logging | Dùng `print()` và còn log cả secret | Dùng structured JSON logging, không log secrets | Dễ debug trên cloud, dễ đưa vào log systems như Datadog/Loki, an toàn hơn |
| Health check | Không có `/health` hoặc `/ready` | Có cả `/health` và `/ready` | Cloud platform cần các endpoint này để kiểm tra app còn sống và đã sẵn sàng nhận traffic |
| Lifecycle | Không có startup/shutdown lifecycle rõ ràng | Có `lifespan` để startup/shutdown | Giúp quản lý tài nguyên và trạng thái ứng dụng tốt hơn |
| Shutdown | Không xử lý graceful shutdown | Có handler cho `SIGTERM` | Khi container bị stop/redeploy, app có cơ hội đóng tài nguyên và kết thúc request đang chạy |
| Host binding | Chạy với `host="localhost"` | Chạy với `host=settings.host` mặc định là `0.0.0.0` | `0.0.0.0` là bắt buộc nếu muốn nhận traffic từ Docker/container/cloud |
| Port binding | Hardcode `port=8000` | Dùng `settings.port` đọc từ env var `PORT` | Railway/Render thường inject `PORT`, nên app production phải đọc từ env |
| Debug mode | `reload=True` luôn bật | `reload=settings.debug` | Production không nên luôn bật reload vì tốn tài nguyên và có thể gây lỗi hành vi |
| Metadata response | Trả về đơn giản chỉ có `answer` | Trả về `question`, `answer`, `model` | Response có cấu trúc rõ hơn, thuận tiện cho client và kiểm thử |

### Test results
- Develop version chạy thành công với lệnh: `curl.exe -X POST "http://localhost:8000/ask?question=Hello"`
- Production version chạy thành công với lệnh: `curl.exe -X POST "http://localhost:8000/ask" -H "Content-Type: application/json" -d "{\"question\":\"Hello\"}"`
- Từ đó có thể thấy develop và production không chỉ khác về config mà còn khác về cách thiết kế API và readiness cho môi trường cloud.
## Part 2: Docker

### Exercise 2.1: Dockerfile questions
1. Base image: `python:3.11`
2. Working directory: `/app`
3. `COPY requirements.txt` trước để Docker tận dụng layer cache. Nếu dependencies không đổi thì lần build sau không cần cài lại toàn bộ packages, giúp build nhanh hơn.
4. `CMD` định nghĩa lệnh mặc định khi container start. Trong sample develop, `CMD ["python", "app.py"]` là lệnh khởi động ứng dụng bên trong container.

### Exercise 2.2: Build and run results
- Build thành công với lệnh: `docker build -f 02-docker\develop\Dockerfile -t my-agent:develop .`
- Chạy container thành công với lệnh: `docker run -p 8000:8000 my-agent:develop`
- Test API thành công với lệnh: `curl.exe -X POST "http://localhost:8000/ask?question=What%20is%20Docker?"`
- Response nhận được: `{"answer":"Container là cách đóng gói app để chạy ở mọi nơi. Build once, run anywhere!"}`

### Exercise 2.3: Image size comparison
- Develop: `1.66GB`
- Production (advanced): `236MB`
- Nhận xét: Multi-stage build giúp image production nhỏ hơn rất nhiều vì chỉ giữ lại runtime và dependencies cần thiết để chạy app, không mang theo toàn bộ build tools như stage builder.

### Exercise 2.3: Multi-stage build questions
1. Stage 1 (`builder`) dùng để cài dependencies và chuẩn bị các package cần thiết cho quá trình build.
2. Stage 2 (`runtime`) chỉ copy những gì cần để chạy ứng dụng, ví dụ source code và installed packages từ builder.
3. Image nhỏ hơn vì runtime stage không chứa compiler, apt cache, build dependencies và các file trung gian không cần thiết.

### Exercise 2.4: Docker Compose stack
- Docker Compose production stack gồm 4 services: `agent`, `redis`, `qdrant`, `nginx`
- `agent` là FastAPI application
- `redis` dùng làm cache/session backing service
- `qdrant` là vector database
- `nginx` đóng vai trò reverse proxy và load balancer
- Các service giao tiếp với nhau qua internal Docker network thay vì gọi `localhost`
- Truy cập từ bên ngoài đi qua `nginx`, sau đó được route tới `agent`

### Exercise 2.4: Test results
- Health check thành công với lệnh: `curl.exe http://localhost/health`
- Kết quả: `{"status":"ok","uptime_seconds":10.0,"version":"2.0.0","timestamp":"2026-04-17T03:27:51.196748"}`
- Test endpoint `/ask` thành công với lệnh: `curl.exe -X POST "http://localhost/ask" -H "Content-Type: application/json" --data-binary "@request.json"`
- Nội dung `request.json`: `{"question":"Explain microservices"}`
- Response nhận được: `{"answer":"Tôi là AI agent được deploy lên cloud. Câu hỏi của bạn đã được nhận."}`

### Exercise 2.4: Notes during setup
- Ban đầu sample production bị thiếu `requirements.txt`, nên cần bổ sung file này để Dockerfile build được.
- `docker-compose.yml` cũng cần sửa `build.context` về repo root để các lệnh `COPY 02-docker/production/...` và `COPY utils/mock_llm.py ...` tìm đúng file.
- `qdrant` container chạy được nhưng healthcheck ban đầu không phù hợp, nên cần nới điều kiện phụ thuộc để stack có thể start hoàn chỉnh trong môi trường lab.

## Part 3: Cloud Deployment

### Exercise 3.1: Railway deployment
- Nền tảng đã dùng: `Railway`
- Project đã tạo: `day12-railway-agent`
- Public URL: `https://day12-railway-agent-production.up.railway.app`
- Deploy thành công với lệnh: `railway up`
- Railway build thành công và healthcheck nội bộ trả `200 OK`

### Exercise 3.1: Public URL test results
- Health check thành công với lệnh:
  `curl.exe https://day12-railway-agent-production.up.railway.app/health`
- Response nhận được:
  `{"status":"ok","uptime_seconds":229.0,"platform":"Railway","timestamp":"2026-04-17T03:48:41.469970+00:00"}`
- Test endpoint `/ask` bằng query parameter:
  `curl.exe -X POST "https://day12-railway-agent-production.up.railway.app/ask?question=Hello"`
- Kết quả: `Internal Server Error`
- Test endpoint `/ask` bằng JSON body:
  `curl.exe -X POST "https://day12-railway-agent-production.up.railway.app/ask" -H "Content-Type: application/json" --data-binary "@request.json"`
- Nội dung `request.json`: `{"question":"Hello"}`
- Response nhận được:
  `{"question":"Hello","answer":"Agent đang hoạt động tốt! (mock response) Hỏi thêm câu hỏi đi nhé.","platform":"Railway"}`

### Exercise 3.1: Notes
- App Railway này nhận dữ liệu cho `/ask` qua JSON body, không phù hợp với cách gọi bằng query parameter.
- Sau khi deploy, Railway tự build và start app bằng `uvicorn app:app --host 0.0.0.0 --port $PORT`.
- Railway CLI local vẫn hiển thị `Service: None`, nên việc `railway variables set ...` chưa chạy được ngay. Tuy vậy, deployment thực tế vẫn thành công và public URL đã hoạt động bình thường.

### Exercise 3.2: Railway vs Render
- `Railway` dùng workflow CLI khá nhanh: `railway login`, `railway init`, `railway up`, `railway domain`
- `Render` thiên về kết nối GitHub repo và đọc cấu hình từ `render.yaml`
- `railway.toml` chủ yếu mô tả cấu hình deploy cho Railway CLI/platform
- `render.yaml` là blueprint file để Render tự tạo service từ repository
- Railway phù hợp hơn cho bài lab khi cần deploy nhanh và lấy public URL sớm

### Exercise 3.3: Summary
- Đã deploy thành công lên ít nhất 1 platform cloud
- Đã có public URL hoạt động
- Đã test được endpoint công khai trên cloud
- Đã hiểu rằng cloud app cần đúng format request giống local app, nếu gọi sai kiểu body/query thì vẫn có thể lỗi dù deploy thành công

## Part 4: API Security

### Exercise 4.1: API key authentication (develop)
- App develop yêu cầu header `X-API-Key` để truy cập endpoint `/ask`
- Test không có key:
  `curl.exe -X POST "http://localhost:8000/ask?question=Hello"`
- Response:
  `{"detail":"Missing API key. Include header: X-API-Key: <your-key>"}`
- Test có key đúng:
  `curl.exe -X POST "http://localhost:8000/ask?question=Hello" -H "X-API-Key: demo-key-change-in-production"`
- Response:
  `{"question":"Hello","answer":"Agent đang hoạt động tốt! (mock response) Hỏi thêm câu hỏi đi nhé."}`
- Kết luận: API key authentication hoạt động đúng, request không có key sẽ bị chặn, request có key hợp lệ sẽ được xử lý.

### Exercise 4.2: JWT authentication (production)
- Endpoint lấy token là: `/auth/token`
- Credentials demo dùng thành công:
  - `student / demo123`
  - `teacher / teach456`
- Lấy token student thành công với lệnh:
  `curl.exe -X POST "http://localhost:8000/auth/token" -H "Content-Type: application/json" --data-binary "@login.json"`
- Response trả về có `access_token`, `token_type`, `expires_in_minutes`
- Dùng Bearer token gọi `/ask` thành công bằng PowerShell:
  `Invoke-RestMethod -Method Post -Uri "http://localhost:8000/ask" -Headers $headers -ContentType "application/json" -Body $body`
- Response nhận được có `question`, `answer`, và `usage`
- Kết luận: JWT login flow hoạt động đúng, token được cấp qua `/auth/token` và được dùng để bảo vệ `/ask`.

### Exercise 4.2: Debugging note
- Trong sample production ban đầu có bug tại middleware security headers:
  `response.headers.pop("server", None)`
- `MutableHeaders` không hỗ trợ `.pop()`, nên mọi request bị `500 Internal Server Error`
- Đã sửa thành cách xóa header hợp lệ:
  `if "server" in response.headers: del response.headers["server"]`
- Sau khi sửa, flow lấy token và gọi endpoint protected mới chạy bình thường.

### Exercise 4.3: Rate limiting
- Theo code:
  - `student` (role `user`) giới hạn `10 requests / 60 seconds`
  - `teacher` (role `admin`) giới hạn `100 requests / 60 seconds`
- Test với `student`:
  - Request `1` đến `10`: thành công
  - Request `11` và `12`: fail với `429 Too Many Requests`
- Test với `teacher`:
  - Request `1` đến `100`: thành công
  - Request `101`: fail với `429 Too Many Requests`
- Kết luận: rate limiter hoạt động đúng và có phân tầng theo role.

### Exercise 4.4: Cost guard
- Endpoint `/me/usage` cho phép theo dõi usage theo user
- Ban đầu budget mặc định là `1.0 USD/day`, nên trong test bình thường rất khó chạm ngưỡng block
- Để kiểm chứng cost guard trong lab, budget đã được giảm tạm để dễ trigger
- Sau khi giảm budget và restart app:
  - Request `1` đến `18`: thành công
  - Request `19`: fail với `402 Payment Required`
- Usage sau khi bị block:
  - `user_id`: `teacher`
  - `requests`: `38`
  - `cost_usd`: `0.002052`
  - `budget_usd`: `0.002`
  - `budget_remaining_usd`: `0`
  - `budget_used_pct`: `102.6`
- Kết luận: cost guard hoạt động đúng, khi chi phí vượt budget thì API chặn request bằng mã lỗi `402`.

### Exercise 4.1-4.4: Overall summary
- API key auth hoạt động ở bản develop
- JWT auth hoạt động ở bản production
- Rate limiting hoạt động đúng với từng role khác nhau
- Cost guard có thể chặn request khi vượt budget
- Phần bảo mật của Part 4 đã được kiểm chứng cả ở mức xác thực lẫn bảo vệ chi phí/tần suất gọi API

## Part 5: Scaling & Reliability

### Exercise 5.1: Health checks
- Bản develop đã chạy thành công với:
  - `curl.exe http://localhost:8000/health`
  - `curl.exe http://localhost:8000/ready`
- Response `/health`:
  `{"status":"ok","uptime_seconds":7.2,"version":"1.0.0","environment":"development","timestamp":"2026-04-17T04:35:12.333288+00:00","checks":{"memory":{"status":"ok","used_percent":66.0}}}`
- Response `/ready`:
  `{"ready":true,"in_flight_requests":1}`
- Kết luận: app có cả liveness probe và readiness probe, đồng thời trả thêm thông tin runtime như memory usage và số request đang xử lý.

### Exercise 5.2: Graceful shutdown / service resilience
- Trong production stack có `3` agent instances, `1` nginx load balancer, và `1` Redis service
- Sau khi dừng riêng một instance:
  `docker stop production-agent-1`
- Hệ thống vẫn trả `/health` thành công qua nginx:
  `{"status":"ok","uptime_seconds":42.2,"version":"2.0.0","timestamp":"2026-04-17T04:43:17.425052"}`
- Kết luận: khi một instance bị dừng, hệ thống vẫn tiếp tục phục vụ nhờ các instance còn lại phía sau load balancer.

### Exercise 5.3: Stateless design
- Production app lưu session và conversation history trong Redis thay vì memory cục bộ của từng instance
- Điều này cho phép bất kỳ instance nào cũng có thể tiếp tục cuộc hội thoại của cùng một user/session
- Đây là điều kiện quan trọng để scale ngang mà không làm mất state

### Exercise 5.4: Load balancing
- Production stack được chạy với `3` agent replicas
- Các request đi qua nginx tại `http://localhost:8080`
- Health check production thành công:
  `curl.exe http://localhost:8080/health`
- Response:
  `{"status":"ok","uptime_seconds":62.7,"version":"2.0.0","timestamp":"2026-04-17T04:38:28.042249"}`
- Test endpoint `/ask` qua nginx thành công:
  `curl.exe -X POST "http://localhost:8080/ask" -H "Content-Type: application/json" --data-binary "@request.json"`
- Khi gọi liên tiếp 10 request, response thay đổi qua nhiều kiểu mock answer khác nhau, cho thấy traffic đã được phân tán qua các agent instances khác nhau.

### Exercise 5.5: Stateless test
- Script `test_stateless.py` ban đầu bị lỗi `404 Not Found`
- Nguyên nhân không phải do logic test, mà do `docker-compose.yml` đang build nhầm app từ đường dẫn khác, nên stack chạy sai ứng dụng
- Sau khi sửa lại cấu hình build để chạy đúng app `05-scaling-reliability/production/app.py`, script test chạy thành công
- Kết quả script:
  - `5` requests được phục vụ bởi `3` instance khác nhau:
    - `instance-4028a6`
    - `instance-c15fb9`
    - `instance-f42cbc`
  - Cùng một `session_id` được giữ xuyên suốt toàn bộ conversation
  - Conversation history có `10` messages và vẫn đầy đủ dù request đi qua nhiều instance khác nhau
- Script kết luận:
  - `All requests served despite different instances!`
  - `Session history preserved across all instances via Redis!`
- Kết luận: thiết kế stateless với Redis đã hoạt động đúng trong môi trường scale nhiều instance.

### Exercise 5.1-5.5: Overall summary
- Health và readiness checks hoạt động đúng
- Hệ thống production dùng nhiều instance phía sau nginx
- Traffic được load balance giữa các agent instances
- Session/history được lưu trong Redis nên không phụ thuộc vào một instance cụ thể
- Khi một instance bị dừng, hệ thống vẫn tiếp tục phục vụ request
- Part 5 chứng minh được cả reliability lẫn scalability của agent architecture
## Part 6: Final Project

### Objective
- Xây dựng một production-ready AI agent hoàn chỉnh, kết hợp config theo environment, API key auth, rate limiting, cost guard, health/readiness checks, graceful shutdown, Redis-backed state, Docker packaging và cloud deploy config.

### Final implementation summary
- Final project được hoàn thiện trong thư mục `06-lab-complete`
- Đã bổ sung đầy đủ các module theo đúng cấu trúc deliverable:
  - `app/main.py`
  - `app/config.py`
  - `app/auth.py`
  - `app/rate_limiter.py`
  - `app/cost_guard.py`
  - `app/storage.py`
  - `utils/mock_llm.py`
- App sử dụng Redis để lưu conversation history theo `user_id`, nên state không còn nằm trong memory cục bộ của từng process.

### Functional requirements
- REST API hoạt động qua endpoint `POST /ask`
- Request body dùng format:
  `{"user_id":"student1","question":"What is deployment?"}`
- App trả về đầy đủ:
  - `user_id`
  - `question`
  - `answer`
  - `model`
  - `timestamp`
  - `history_length`
  - `budget_remaining_usd`
  - `requests_remaining`
- Có endpoint `GET /history/{user_id}` để kiểm tra conversation history đã được lưu trong Redis

### Non-functional requirements
- Config đọc từ environment variables
- Authentication dùng `X-API-Key`
- Rate limiting dùng Redis sliding window
- Cost guard dùng Redis với monthly budget
- Có `GET /health`
- Có `GET /ready`
- Có structured JSON logging
- Có graceful shutdown handler cho `SIGTERM`
- Có Dockerfile multi-stage
- Có `docker-compose.yml`
- Có `railway.toml` và `render.yaml`

### Local runtime verification
- `python check_production_ready.py` chạy thành công với kết quả:
  `20/20 checks passed (100%)`
- Docker runtime local của Part 6 đã được verify thành công
- `GET /health` trả `200 OK`:
  `{"status":"ok","version":"1.0.0","environment":"staging","uptime_seconds":7.6,"total_requests":2,"checks":{"llm":"mock"},"timestamp":"2026-04-17T05:07:21.865542+00:00"}`
- `POST /ask` với API key hợp lệ chạy thành công:
  `{"user_id":"student1","question":"What is deployment?","answer":"Deployment moves your application from local development to a reachable runtime environment.","model":"gpt-4o-mini","timestamp":"2026-04-17T05:07:21.969825+00:00","history_length":2,"budget_remaining_usd":9.999985,"requests_remaining":9}`
- `GET /history/student1` chạy thành công và trả đúng conversation history:
  `{"user_id":"student1","messages":[{"role":"user","content":"What is deployment?","timestamp":"2026-04-17T05:07:21.893137Z"},{"role":"assistant","content":"Deployment moves your application from local development to a reachable runtime environment.","timestamp":"2026-04-17T05:07:21.969543Z"}]}`

### Validation
- Code syntax đã được kiểm tra thành công
- Production readiness checker pass 100%
- App final không còn dùng in-memory state cho conversation history
- App final đã đáp ứng đúng tinh thần yêu cầu của Part 6: production-ready, stateless, containerized, có auth, rate limit, budget guard và Redis-backed history

### Notes
- Trong quá trình hoàn thiện Part 6 có một lỗi runtime ở Docker image liên quan đến `uvicorn` import path trong container; Dockerfile đã được sửa lại để dependencies được copy đúng vào runtime image.
- Public Railway URL hiện có trong repo là deployment đã verify ở Part 3. Nếu giảng viên yêu cầu public URL phải trỏ đúng final project Part 6, nên redeploy thư mục `06-lab-complete` lên Railway hoặc Render trước khi nộp chính thức.
