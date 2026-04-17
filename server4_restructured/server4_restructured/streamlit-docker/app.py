import streamlit as st
from dotenv import load_dotenv
from pathlib import Path

load_dotenv(dotenv_path=Path(__file__).resolve().parent / ".env")

# ── PAGE CONFIG — must be FIRST st call ──────────────────────────────
st.set_page_config(
    layout="wide",
    page_title="Observability Console",
    page_icon="🖥️",
)

# ── GLOBAL CSS ────────────────────────────────────────────────────────
st.markdown("""
<style>
html, body, [class*="css"] { font-size: 13px; }
textarea { font-size: 12px !important; }
input    { font-size: 12px !important; }
.successbox {
  padding: 0.75rem 1rem;
  border-radius: 0.5rem;
  background: rgba(0,255,0,0.10);
  border: 1px solid rgba(0,255,0,0.30);
}
</style>
""", unsafe_allow_html=True)

# ── LOAD UI MODULES & ROUTE ───────────────────────────────────────────
from ui.state  import init_state
from ui.router import router

init_state()
router()
