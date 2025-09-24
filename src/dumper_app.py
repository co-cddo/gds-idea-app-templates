# src/dumper_app.py
import base64
import json
import os

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse

base_path = os.getenv("BASE_PATH") or ""

app = FastAPI(root_path=base_path)


def decode_jwt_payload(token: str) -> str | None:
    try:
        parts = token.split(".")
        if len(parts) < 2:
            raise ValueError("Invalid JWT")
        payload_b64 = parts[1]
        payload_b64 += "=" * (-len(payload_b64) % 4)  # padding
        payload_bytes = base64.urlsafe_b64decode(payload_b64)
        return payload_bytes.decode("utf-8")
    except Exception:
        return None


@app.get("/", response_class=HTMLResponse)
async def read_headers(request: Request):
    html = "<h1>Live Headers from AWS ALB</h1>"
    html += "<p>The following headers were received by this application from the load balancer:</p>"
    html += "<table border='1' style='width:100%; border-collapse: collapse;'>"
    html += "<tr style='background-color:#f2f2f2;'><th>Header</th><th>Value</th></tr>"

    for header, value in request.headers.items():
        html += f"<tr><td style='padding: 8px;'>{header}</td><td style='padding: 8px; word-break: break-all;'>{value}</td></tr>"
        if header in ["x-amzn-oidc-data", "x-amzn-oidc-accesstoken"]:
            html += f"<tr><td style='padding: 8px;'>{header}-decoded</td><td style='padding: 8px; word-break: break-all;'>{decode_jwt_payload(value)}</td></tr>"

    html += "</table>"

    html += """<a href="https://gds-idea.click">Logout</a>"""

    return HTMLResponse(content=html, status_code=200)
