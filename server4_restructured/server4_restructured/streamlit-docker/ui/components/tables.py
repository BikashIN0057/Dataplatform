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


def search_box(label: str, key: str) -> str:
    return st.text_input(label, value="", key=key, placeholder="Type to filter...").strip().lower()
