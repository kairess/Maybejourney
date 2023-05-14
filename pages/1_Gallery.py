import streamlit as st
import apsw
import os
from helpers import *
from footer import footer

PAGE_SIZE = 9
COLUMN_SIZE = 3

st.set_page_config(page_title="Gallery", page_icon="🖼", layout="wide")

@st.cache_resource
def load_resources():
    con = apsw.Connection("mj.db")
    def row_factory(cursor, row):
        columns = [t[0] for t in cursor.getdescription()]
        return dict(zip(columns, row))
    con.setrowtrace(row_factory)
    return con
con = load_resources()

if "page" not in st.session_state:
    st.session_state["page"] = 0
if "data" not in st.session_state:
    st.session_state["data"] = []
if "done" not in st.session_state:
    st.session_state["done"] = False

def load_data(page=1, size=PAGE_SIZE):
    rows = con.execute("select * from prompts where is_liked = 1 order by created_at desc limit ? offset ?", (size, (page -1) * size)).fetchall()
    return rows

def load_more(size=PAGE_SIZE):
    st.session_state["page"] += 1

    rows = load_data(page=st.session_state["page"], size=size)
    st.session_state["data"].extend(rows)

    cols = st.columns(COLUMN_SIZE)

    for i, row in enumerate(st.session_state["data"]):
        with st.container():
            cols[i % COLUMN_SIZE].image(os.path.join("images", row["filename"]))
            cols[i % COLUMN_SIZE].caption(row["full_prompt"])

def move_page(move=1, size=PAGE_SIZE):
    st.session_state["page"] += move
    rows = load_data(page=st.session_state["page"], size=size)

    if len(rows) < size:
        st.session_state["done"] = True
    else:
        st.session_state["done"] = False
    if len(rows) == 0:
        st.session_state["done"] = True
        return False

    st.session_state["data"] = rows

    cols = st.columns(COLUMN_SIZE)

    for i, row in enumerate(st.session_state["data"]):
        with st.container():
            cols[i % COLUMN_SIZE].image(os.path.join("images", row["filename"]))
            cols[i % COLUMN_SIZE].caption(row["full_prompt"])

if st.session_state["page"] == 0:
    move_page(1)

col1, col2 = st.columns(2)
col1.button("Previous", on_click=move_page, args=(-1,), type="primary", use_container_width=True, disabled=True if st.session_state["page"] == 1 else False)
col2.button("Next", on_click=move_page, args=(1,), type="primary", use_container_width=True, disabled=st.session_state["done"])

footer(*footer_content)
