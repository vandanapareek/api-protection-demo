from prometheus_client import Counter, Histogram

REQUESTS = Counter("demo_requests_total", "Total requests")
ALLOWED = Counter("demo_allowed_total", "Allowed requests")
BLOCKED = Counter("demo_blocked_total", "Blocked requests (429)")
SUSPICIONS = Counter("demo_suspicious_total", "Suspicious events flagged")
LATENCY = Histogram("demo_request_latency_seconds", "Request latency")
