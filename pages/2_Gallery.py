import streamlit as st
import pymysql.cursors
import random
from helpers import *
from footer import footer

PAGE_SIZE = 9
COLUMN_SIZE = 3

st.set_page_config(page_title="Gallery", page_icon="🖼", layout="wide")

if random.random() > 0.5: st.balloons()
else: pass

con = pymysql.connect(
    host=st.secrets["db_host"],
    user=st.secrets["db_username"],
    password=st.secrets["db_password"],
    database='maybejourney',
    cursorclass=pymysql.cursors.DictCursor)

if "page" not in st.session_state:
    st.session_state["page"] = 0
if "data" not in st.session_state:
    st.session_state["data"] = []
if "done" not in st.session_state:
    st.session_state["done"] = False

def load_data(page=1, size=PAGE_SIZE):
    con.ping()
    with con:
        with con.cursor() as cur:
            cur.execute("select * from prompts where is_liked = 1 order by created_at desc limit %s offset %s", (size, (page - 1) * size))
            rows = cur.fetchall()
    return rows

def load_more(size=PAGE_SIZE):
    st.session_state["page"] += 1

    rows = load_data(page=st.session_state["page"], size=size)
    st.session_state["data"].extend(rows)

    cols = st.columns(COLUMN_SIZE)

    for i, row in enumerate(st.session_state["data"]):
        with st.container():
            cols[i % COLUMN_SIZE].image(row["url"])
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
            cols[i % COLUMN_SIZE].image(row["url"])
            cols[i % COLUMN_SIZE].caption(row["full_prompt"])

if st.session_state["page"] == 0:
    move_page(1)

col1, col2 = st.columns(2)
col1.button("Previous", on_click=move_page, args=(-1,), type="primary", use_container_width=True, disabled=True if st.session_state["page"] == 1 else False)
col2.button("Next", on_click=move_page, args=(1,), type="primary", use_container_width=True, disabled=st.session_state["done"])

footer(*footer_content)
