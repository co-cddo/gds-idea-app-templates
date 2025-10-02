import streamlit as st

from cognito_user.helpers.streamlit import require_auth

REDIRECT_URL = "https://gds-idea.click/401.html"


user = require_auth(
    redirect_url=REDIRECT_URL,
    allowed_domains=["digital.cabinet-office.gov.uk"],
    allowed_emails=[
        "david.gillespie@digital.cabinet-office.gov.uk",
        "jose.orjales@digital.cabinet-office.gov.uk",
    ],
    require_all=True,
)

st.write("You are Authorized!")
st.write(f"Welcome {user.email}")

st.write("OIDC_claims:")
st.json(user.oidc_claims)

st.write("Access Claims:")
st.json(user.access_claims)

st.write("All Headers:")
st.json(dict(st.context.headers))
