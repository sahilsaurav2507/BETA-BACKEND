from prometheus_client import Counter, Histogram, generate_latest
from fastapi import Request, Response
import time

REQUEST_COUNT = Counter(
    "api_requests_total",
    "Total number of API requests",
    ["method", "endpoint", "status"]
)
REQUEST_LATENCY = Histogram(
    "api_request_duration_seconds",
    "API request duration in seconds",
    ["method", "endpoint"]
)
# Custom business event counters
USER_SIGNUP_COUNT = Counter("user_signup_total", "Total number of user signups")
SHARE_EVENT_COUNT = Counter("share_event_total", "Total number of share events")
BULK_EMAIL_SENT_COUNT = Counter("bulk_email_sent_total", "Total number of bulk email sends")
ADMIN_PROMOTION_COUNT = Counter("admin_promotion_total", "Total number of admin promotions")

def prometheus_middleware(app):
    @app.middleware("http")
    async def prometheus_metrics(request: Request, call_next):
        start_time = time.time()
        try:
            response: Response = await call_next(request)
            process_time = time.time() - start_time
            REQUEST_COUNT.labels(request.method, request.url.path, response.status_code).inc()
            REQUEST_LATENCY.labels(request.method, request.url.path).observe(process_time)
            return response
        except Exception as e:
            process_time = time.time() - start_time
            REQUEST_COUNT.labels(request.method, request.url.path, 500).inc()
            REQUEST_LATENCY.labels(request.method, request.url.path).observe(process_time)
            raise
    return app

def prometheus_endpoint():
    return Response(generate_latest(), media_type="text/plain")

# Increment functions for business events
def inc_user_signup():
    USER_SIGNUP_COUNT.inc()
def inc_share_event():
    SHARE_EVENT_COUNT.inc()
def inc_bulk_email_sent():
    BULK_EMAIL_SENT_COUNT.inc()
def inc_admin_promotion():
    ADMIN_PROMOTION_COUNT.inc() 