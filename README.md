# API Protection Demo

A simple **FastAPI** service that demonstrates how to protect APIs against **abuse, scraping, and brute force attacks** using **rate limiting**, **Redis**, and **Prometheus monitoring**.

🔗 **Live Demo**: [https://api-protection-demo.onrender.com](https://api-protection-demo.onrender.com)

---

## Features
- ✅ REST API built with **FastAPI**  
- ✅ **Rate limiting** (via Redis) to block suspicious/bot-like traffic  
- ✅ **Prometheus metrics** integration for observability  
- ✅ Example endpoints (`/`, `/search`, `/protected`, `/metrics`)  
- ✅ Deployable on **Render** (or any Docker-ready platform)  

---

## API Endpoints

### 1. Health Check
```http
GET /
```
🔗 [https://api-protection-demo.onrender.com/](https://api-protection-demo.onrender.com/)  
➡️ Returns:
```json
{"status": "ok", "info": "API protection demo"}
```

---

### 2. Search API (example query)
```http
GET /search?q=apple
```
🔗 [https://api-protection-demo.onrender.com/search?q=apple](https://api-protection-demo.onrender.com/search?q=apple)  
➡️ Returns:
```json
{"query": "apple", "results": ["apple result 1", "apple result 2"]}
```

---

### 3. Protected Endpoint (rate-limited)
```http
GET /protected
```
🔗 [https://api-protection-demo.onrender.com/protected](https://api-protection-demo.onrender.com/protected)  
➡️ Returns normal JSON at first.  
➡️ After exceeding rate limits, returns:
```json
{"detail": "Too Many Requests"}
```

---

### 4. Prometheus Metrics
```http
GET /metrics
```
🔗 [https://api-protection-demo.onrender.com/metrics](https://api-protection-demo.onrender.com/metrics)  
➡️ Returns live counters:
```
demo_requests_total
demo_allowed_total
demo_blocked_total
```

---

## ⚙️ Tech Stack
- **FastAPI** (Python web framework)  
- **Redis** (for rate limiting state)  
- **aioredis** (async Redis client)  
- **Prometheus client** (metrics export)  
- **Uvicorn** (ASGI server)  
- **Render** (deployment)  

---

## Example Metrics Flow
1. Call `/search?q=apple` → `demo_requests_total` increases.  
2. Call `/protected` repeatedly → after the limit, `demo_blocked_total` increases.  
3. View `/metrics` → confirms blocked vs allowed requests.  

---

## 💡 Purpose
This project is a **demo for interview prep & practice**.  
It simulates how **real-world backend teams** (like Agoda, Grab, Shopee) protect APIs from:  
- Scraping bots  
- DDoS-like traffic  
- Abuse of rate-limited endpoints  

---

## 🛠️ Run Locally

Clone repo:
```bash
git clone https://github.com/your-username/api-protection-demo.git
cd api-protection-demo
```

Create virtual env:
```bash
python -m venv venv
source venv/bin/activate   # macOS/Linux
venv\Scripts\activate      # Windows
```

Install dependencies:
```bash
pip install -r requirements.txt
```

Start service:
```bash
uvicorn app.main:app --reload --port 8080
```

Service runs at: [http://127.0.0.1:8080](http://127.0.0.1:8080)  

---

## ✅ Next Steps
- Add **JWT authentication** for real user-level protection.  
- Integrate **IP reputation APIs** for advanced bot detection.  
- Deploy on AWS/GCP with **CloudFront or API Gateway** in front.  

---
