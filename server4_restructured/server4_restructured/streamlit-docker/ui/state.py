import streamlit as st


def init_state():
    defaults = {
        "page": "Home",
        "request_rerun": False,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v
