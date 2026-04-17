import streamlit as st
import pandas as pd
import re


def show_table(df: pd.DataFrame, title: str | None = None):
    if title:
        st.markdown(f"### {title}")
    if df is None or df.empty:
        st.info("No rows yet.")
        return
    st.dataframe(df, use_container_width=True, hide_index=True)


def html_table(df: pd.DataFrame, title: str | None = None):
    """Render a small HTML table with clickable links."""
    if title:
        st.markdown(f"### {title}")
    if df is None or df.empty:
        st.info("No rows yet.")
        return

    def esc(s: str) -> str:
        return (s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
                .replace('"', "&quot;").replace("'", "&#39;"))

    def linkify(v):
        if v is None:
            return ""
        s = str(v)
        m = re.match(r"^\[(.*?)\]\((.*?)\)$", s.strip())
        if m:
            txt, url = m.group(1), m.group(2)
            return f'<a href="{esc(url)}">{esc(txt)}</a>'
        if s.startswith("http://") or s.startswith("https://"):
            return f'<a href="{esc(s)}" target="_blank">{esc(s)}</a>'
        return esc(s)

    cols = list(df.columns)
    thead = "".join(
        [f"<th style='text-align:left;padding:6px;border-bottom:1px solid #555;'>{esc(c)}</th>" for c in cols])
    rows_html = ""
    for _, r in df.iterrows():
        tds = "".join(
            [f"<td style='padding:6px;border-bottom:1px solid #333;'>{linkify(r[c])}</td>" for c in cols])
        rows_html += f"<tr>{tds}</tr>"
    html = (f"<table style='width:100%;border-collapse:collapse;'>"
            f"<thead><tr>{thead}</tr></thead><tbody>{rows_html}</tbody></table>")
    st.markdown(html, unsafe_allow_html=True)


def search_box(label: str, key: str) -> str:
    return st.text_input(label, value="", key=key, placeholder="Type to filter...").strip().lower()
