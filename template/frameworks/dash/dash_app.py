import json
import logging

from cognito_auth.dash import DashAuth
from dash import Dash, Input, Output, dcc, html

logging.basicConfig(level=logging.DEBUG)
logging.getLogger("watchdog").setLevel(logging.WARNING)

REDIRECT_URL = "https://gds-idea.click/401.html"

app = Dash(__name__)
auth = DashAuth(app)
auth.protect_app(app)  # protects the entire app.


# health check endpoint for ECS/ALB
# create this so access to the container can be monitored
@app.server.route("/health")
def health_check():
    return {"status": "healthy"}, 200


# Layout with dynamic content that will be populated by callback
app.layout = html.Div(
    [
        html.H1("You are Authorised!"),
        html.Div(id="user-info"),
        # Hidden interval to trigger initial load
        dcc.Interval(id="interval", interval=1000, n_intervals=0, max_intervals=1),
    ]
)


# Callback to fetch and display user info within app context
@app.callback(Output("user-info", "children"), Input("interval", "n_intervals"))
def display_user_info(n):
    user = auth.get_auth_user()

    return html.Div(
        [
            html.P(f"Welcome {user.email}"),
            html.H2("OIDC Claims:"),
            html.Pre(json.dumps(user.oidc_claims, indent=2)),
            html.H2("Access Claims:"),
            html.Pre(json.dumps(user.access_claims, indent=2)),
        ]
    )


# Expose server for gunicorn
server = app.server
