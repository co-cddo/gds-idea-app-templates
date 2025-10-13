import logging

import streamlit as st
from cognito_auth.streamlit import StreamlitAuth

logging.basicConfig(level=logging.DEBUG)
logging.getLogger("watchdog").setLevel(logging.WARNING)

REDIRECT_URL = "https://gds-idea.click/401.html"

auth = StreamlitAuth()

user = auth.get_auth_user()


st.write("You are Authorised!")
st.write(f"Welcome {user.email}")

st.write("OIDC_claims:")
st.json(user.oidc_claims)

st.write("Access Claims:")
st.json(user.access_claims)

st.write("All Headers:")
st.json(dict(st.context.headers))
