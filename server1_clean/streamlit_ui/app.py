import streamlit as st
import urllib.parse
import requests
import urllib3
import os
from jose import jwt
from dotenv import load_dotenv
from pathlib import Path

# Suppress SSL warnings for self-signed cert
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# ==============================
# LOAD .env FROM SAME FOLDER AS app.py
# ==============================
load_dotenv(dotenv_path=Path(__file__).resolve().parent / ".env")

# ==============================
# KEYCLOAK CONFIG (from .env)
# ==============================
KEYCLOAK_SERVER = os.getenv("KEYCLOAK_SERVER", "https://10.155.38.139:8443")
REALM           = os.getenv("KEYCLOAK_REALM",  "ckuens-platform")
CLIENT_ID       = os.getenv("KEYCLOAK_CLIENT_ID", "data-platform-ui")
CLIENT_SECRET   = os.getenv("KEYCLOAK_CLIENT_SECRET", "5BfPmCrKteVEo6ZhqscJymaX3cjJPrGf")
# Fixed ZeroTier IP — always use http://10.155.38.206:8501 in browser
REDIRECT_URI    = os.getenv("KEYCLOAK_REDIRECT_URI", "http://10.155.38.206:8501")
MICROSOFT_IDP_ALIAS = os.getenv("MICROSOFT_IDP_ALIAS", "microsoft")

AUTH_URL   = f"{KEYCLOAK_SERVER}/realms/{REALM}/protocol/openid-connect/auth"
TOKEN_URL  = f"{KEYCLOAK_SERVER}/realms/{REALM}/protocol/openid-connect/token"
LOGOUT_URL = f"{KEYCLOAK_SERVER}/realms/{REALM}/protocol/openid-connect/logout"

# ==============================
# PAGE CONFIG — must be FIRST st call
# ==============================
st.set_page_config(layout="wide", page_title="Data Platform Console")

# ==============================
# GLOBAL CSS
# ==============================
st.markdown("""
<style>
html, body, [class*="css"] { font-size: 12px; }
textarea { font-size: 12px !important; }
input    { font-size: 12px !important; }
.successbox {
  padding: 0.75rem 1rem;
  border-radius: 0.5rem;
  background: rgba(0,255,0,0.12);
  border: 1px solid rgba(0,255,0,0.35);
}
.successbox a { text-decoration: underline; }
</style>
""", unsafe_allow_html=True)

def success_box(markdown_text: str):
    st.markdown(
        f"<div class='successbox'>{markdown_text}</div>",
        unsafe_allow_html=True
    )

# ==============================
# KEYCLOAK HELPERS
# ==============================
def build_login_url(idp_hint=None) -> str:
    """Build Keycloak auth URL. prompt=login forces credential screen every time."""
    params = {
        "client_id":     CLIENT_ID,
        "response_type": "code",
        "scope":         "openid profile email",
        "redirect_uri":  REDIRECT_URI,
        "prompt":        "login",
    }
    if idp_hint:
        params["kc_idp_hint"] = idp_hint
    return AUTH_URL + "?" + urllib.parse.urlencode(params)

def exchange_code_for_token(code: str) -> dict:
    data = {
        "grant_type":    "authorization_code",
        "client_id":     CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "code":          code,
        "redirect_uri":  REDIRECT_URI,
    }
    try:
        resp = requests.post(TOKEN_URL, data=data, timeout=15, verify=False)
        return resp.json()
    except Exception as e:
        return {"error": str(e)}

def decode_token(token: str) -> dict:
    return jwt.get_unverified_claims(token)

# ==============================
# ROLE -> TEAM MAPPING
# ==============================
ROLE_TEAMS = {
    "Admin":         "Platform",
    "Data Engineer": "DataEng",
    "Data Analyst":  "Analytics",
    "ML Engineer":   "ML",
}

# ==============================
# AUTH FLOW — handle ?code= callback from Keycloak
# ==============================
query_params = st.query_params

if "code" in query_params:
    if "token" not in st.session_state:
        token_response = exchange_code_for_token(query_params["code"])
        if "access_token" in token_response:
            st.session_state["token"] = token_response
            st.query_params.clear()
            st.rerun()
        else:
            st.error("Token exchange failed.")
            st.json(token_response)
            with st.expander("Debug info"):
                st.caption(f"Keycloak Server : `{KEYCLOAK_SERVER}`")
                st.caption(f"Realm           : `{REALM}`")
                st.caption(f"Client ID       : `{CLIENT_ID}`")
                st.caption(f"Redirect URI    : `{REDIRECT_URI}`")
                st.caption(f"Token URL       : `{TOKEN_URL}`")
            st.stop()

# ==============================
# NOT LOGGED IN — show login page
# ==============================
if "token" not in st.session_state:
    st.title("Data Platform Console")
    st.info("Please login with your Keycloak account to continue.")
    st.markdown(f"### [Login with Keycloak]({build_login_url()})")
    st.markdown("---")
    st.markdown(f"### [Login with Microsoft]({build_login_url(idp_hint=MICROSOFT_IDP_ALIAS)})")
    with st.expander("Debug info", expanded=False):
        st.caption(f"Keycloak Server : `{KEYCLOAK_SERVER}`")
        st.caption(f"Realm           : `{REALM}`")
        st.caption(f"Client ID       : `{CLIENT_ID}`")
        st.caption(f"Redirect URI    : `{REDIRECT_URI}`")
    st.stop()

# ==============================
# LOGGED IN — decode token & populate session
# ==============================
decoded  = decode_token(st.session_state["token"]["access_token"])
username = decoded.get("preferred_username", "unknown")
roles    = decoded.get("resource_access", {}).get(CLIENT_ID, {}).get("roles", [])

PRIMARY_ROLE = None
if "platform_admin" in roles:
    PRIMARY_ROLE = "Admin"
elif "data_engineer" in roles:
    PRIMARY_ROLE = "Data Engineer"
elif "data_analyst" in roles:
    PRIMARY_ROLE = "Data Analyst"
elif "ml_engineer" in roles:
    PRIMARY_ROLE = "ML Engineer"

st.session_state.logged_in = True
st.session_state.user      = username
st.session_state.role      = PRIMARY_ROLE
st.session_state.team      = ROLE_TEAMS.get(PRIMARY_ROLE, "Unknown")

# ==============================
# SIDEBAR — user info + logout
# ==============================
st.sidebar.markdown("---")
st.sidebar.write("Logged in as:", username)
st.sidebar.write("Role:", PRIMARY_ROLE or "No role assigned")
st.sidebar.write("Team:", st.session_state.team)
st.sidebar.write("Keycloak roles:", roles)
st.sidebar.markdown("---")

if st.sidebar.button("Logout"):
    # Capture id_token BEFORE clearing session — needed to kill Keycloak SSO
    id_token_hint = st.session_state.get("token", {}).get("id_token", "")

    # Clear ALL Streamlit session state
    for key in list(st.session_state.keys()):
        del st.session_state[key]

    # Build Keycloak end-session URL
    logout_params = {
        "client_id":                CLIENT_ID,
        "post_logout_redirect_uri": REDIRECT_URI,
    }
    if id_token_hint:
        logout_params["id_token_hint"] = id_token_hint

    logout_url = LOGOUT_URL + "?" + urllib.parse.urlencode(logout_params)
    st.markdown(
        f"<meta http-equiv='refresh' content='0; url={logout_url}'>",
        unsafe_allow_html=True,
    )
    st.stop()

# ==============================
# LOAD UI MODULES & ROUTE
# ==============================
from ui.state   import init_state
from ui.auth    import qp_autologin
from ui.runtime import handle_deferred_rerun
from ui.router  import router

init_state()
qp_autologin()
router()