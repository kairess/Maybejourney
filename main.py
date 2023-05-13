import openai
import streamlit as st
from streamlit_pills import pills
from dotenv import dotenv_values
from footer import footer, link

import time
import uuid
from datetime import datetime
import apsw
import apsw.ext
from Sender import Sender
from Receiver import Receiver
from helpers import *


# Config
@st.cache_data
def load_config(path=".env"):
    return dotenv_values(path)

config = load_config(".env")
openai.api_key = config["openai_api_key"]

if "requests" not in st.session_state:
    st.session_state["requests"] = []
if "responses" not in st.session_state:
    st.session_state["responses"] = []
if "user_id" not in st.session_state:
    st.session_state["user_id"] = str(uuid.uuid4())
    print("[*] user_id", st.session_state["user_id"])

@st.cache_resource
def load_resources(user_id):
    con = apsw.Connection("mj.db")
    def row_factory(cursor, row):
        columns = [t[0] for t in cursor.getdescription()]
        return dict(zip(columns, row))
    con.setrowtrace(row_factory)
    return con, Sender(config=config), Receiver(config, "images", user_id, con)
con, sender, receiver = load_resources(st.session_state["user_id"])


# UI
st.header("Middlejourney")
selected = pills("", ["NO Streaming", "Streaming"], ["🎈", "🌈"])


# Form
with st.sidebar:
    st.subheader("History")
    history = st.empty().markdown("👋")

prompt = st.text_input("Prompt", placeholder="Imagine...", key="input")

focus()

# Footer
footer_content = [
    "Made with ❤️ by ",
    link("https://github.com/kairess", "kairess"),
    " / ",
    link("https://www.youtube.com/@bbanghyong", "빵형의 개발도상국"),
]

footer(*footer_content)


# Function
if prompt:
    full_prompt = sender.send(prompt=prompt)

    st.session_state["requests"].append(prompt)

    con.execute(f"insert into queues (user_id, full_prompt, created_at) values('{st.session_state['user_id']}', '{full_prompt}', '{datetime.now()}')")

    imgs, prompts, breaks = [], [], []

    for req in st.session_state["requests"]:
        prompts.append(st.empty())
        imgs.append(st.empty())
        breaks.append(st.empty())

    history_text = ""
    for i, row in enumerate(con.execute("select * from queues where user_id = ? order by created_at desc", (st.session_state["user_id"],)).fetchall()):
        history_text += f"- {row['full_prompt']}\n"
    history.markdown(history_text)

    while True:
        receiver.collecting_results(full_prompt)
        receiver.outputer()
        receiver.downloading_results()

        # TODO: Error sometimes KeyError: 'user_id'
        rows = con.execute("select * from prompts where user_id = ? order by created_at desc", (st.session_state["user_id"],)).fetchall()

        if rows and len(st.session_state["requests"]) == len(rows):
            is_all_done = True

            for i, row in enumerate(rows):
                try:
                    prompts[i].text(f"{row['full_prompt']} ({row['status']}%)")
                except:
                    pass

                if row["url"]:
                    try:
                        imgs[i].image(row["url"])
                    except:
                        pass

                breaks[i].markdown("----")

                if row["status"] != 100:
                    is_all_done = False

            if is_all_done:
                focus()
                break

        time.sleep(5)

    # res_box = st.empty()
    # report = []
    # for res in openai.Completion.create(model='text-davinci-003',
    #                                     prompt=prompt,
    #                                     max_tokens=120, 
    #                                     temperature=0.5,
    #                                     stream=True):
    #     report.append(res.choices[0].text)
    #     result = "".join(report).strip()
    #     # result = result.replace("\n", "")
    #     res_box.markdown(f'*{result}*') 

    # result = "".join(report).strip()
    # st.session_state['responses'].append(result)
