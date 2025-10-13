import logging

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from cognito_auth.fastapi import FastAPIAuth

logging.basicConfig(level=logging.DEBUG)
logging.getLogger("watchdog").setLevel(logging.WARNING)

app = FastAPI()
auth = FastAPIAuth(app)

# Health check endpoint for ECS/ALB (unprotected)
@app.get("/health")
def health_check():
    return {"status": "healthy"}

# Main route - protected by app-wide auth middleware
@app.get("/")
def index(request: Request):
    user = auth.get_current_user(request)

    return {
        "message": "You are Authorised!",
        "email": user.email,
        "oidc_claims": user.oidc_claims,
        "access_claims": user.access_claims,
    }

# Additional example route - also automatically protected
@app.get("/api/user")
def get_user(request: Request):
    user = auth.get_current_user(request)

    return {
        "email": user.email,
        "groups": user.groups if hasattr(user, 'groups') else []
    }
