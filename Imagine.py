import streamlit as st
from streamlit_pills import pills
from streamlit_extras.badges import badge
import openai
import pymysql.cursors
import time
import uuid
import re
from Sender import Sender
from Receiver import Receiver
from footer import footer
from helpers import *
from prompt_template import *


# Config
st.set_page_config(page_title="Maybejourney - YouTube 빵형의 개발도상국", page_icon="🎨")

@st.cache_data
def load_config():
    config = {
        "authorization": st.secrets["authorization"],
        "application_id": st.secrets["application_id"],
        "guild_id": st.secrets["guild_id"],
        "channel_id": st.secrets["channel_id"],
        "session_id": st.secrets["session_id"],
        "version": st.secrets["version"],
        "id": st.secrets["id"],
        "openai_api_key": st.secrets["openai_api_key"],
    }
    return config

config = load_config()
openai.api_key = config["openai_api_key"]

if "user_id" not in st.session_state:
    st.session_state["user_id"] = str(uuid.uuid4())
    print("[*] user_id", st.session_state["user_id"])
if "latest_id" not in st.session_state:
    st.session_state["latest_id"] = None
if "history" not in st.session_state:
    st.session_state["history"] = ""
if "page" not in st.session_state:
    st.session_state["page"] = 0
if "done" not in st.session_state:
    st.session_state["done"] = False
st.session_state["page"] = 0
st.session_state["done"] = False

@st.cache_resource
def load_resources(user_id):
    con = pymysql.connect(
        host=st.secrets["db_host"],
        user=st.secrets["db_username"],
        password=st.secrets["db_password"],
        database='maybejourney',
        cursorclass=pymysql.cursors.DictCursor)
    return con, Sender(config=config), Receiver(config, "images", user_id, con)
con, sender, receiver = load_resources(st.session_state["user_id"])


# UI
st.header("Maybejourney v1.3")

with st.expander("📝Update"):
    c1, c2, c3 = st.columns(3)
    with c1:
        badge(type="github", name="kairess/Maybejourney")
    with c2:
        badge(type="buymeacoffee", name="bbanghyong")
    with c3:
        st.markdown("❤️[서버 비용 후원하기](https://lnk.bio/kairess)")

    st.markdown("""
- v1.3 :: May 20, 2023
    - Add `Describe` function
- v1.2 :: May 17, 2023
    - Add `upsample` and `variation` of generated images
- v1.1 :: May 15, 2023
    - Replace sqlite3 to MariaDB on AWS (Support me a beer)
    - Show 1 image per a shot
    - With `DALL-E`
- v1.0 :: May 14, 2023
    - Launch🚀
""")

def like():
    st.session_state["input"] = ""
    latest_id = st.session_state["latest_id"]
    if not latest_id:
        return False

    con.ping()
    with con:
        with con.cursor() as cur:
            cur.execute("update prompts set is_liked = %s where id = %s and is_downloaded = 1", (1, latest_id))
        con.commit()


# Sidebar
with st.sidebar:
    with st.form("parameters-form"):
        st.subheader("Parameters")
        model = pills("🤖 Model", ["Midjourney", "Niji"])
        mid_style = pills("⭐️ Style (Only for Midjourney)", [None, "Raw"])
        niji_style = pills("💊 Style (Only for Niji)", [None, "Cute", "Expressive", "Scenic"])
        ar = pills("🖼 Aspect Ratio", ["3:4", "4:5", "9:16", "1:1", "16:9", "5:4", "4:3"])
        stylize = st.slider("🧂 Stylize", 0, 1000, 100, 50)
        quality = st.slider("🎨 Quality", .25, 2., 1., .25)
        seed = st.number_input("⚙️ Seed", -1, 4294967295, -1)
        tile = st.checkbox("Tile", False)
        creative = pills("Creative (Only for Midjourney)", [None, "test", "testp"])
        submit = st.form_submit_button("Apply")

    with st.container():
        st.subheader("History")
        history = st.empty().markdown("- Empty")

# Prompt
with st.form("prompt-form"):
    st.info("프롬프트 맨 앞에 / 를 붙여 ChatGPT에게 프롬프트를 생성하게 할 수 있습니다!", icon="🤖")
    prompt = st.text_area("Prompt", placeholder="Draw your imagination or use / to ask ChatGPT to generate prompts.", key="input")
    dalle = st.checkbox("with DALL-E")
    submit_prompt = st.form_submit_button("Submit")

prompt_helper = st.empty()
progress_bar = st.empty()
result_image = st.empty()
full_prompt_caption = st.empty()
dalle_result_image = st.empty()
dalle_prompt_caption = st.empty()

footer(*footer_content)

# Function
if submit_prompt and prompt.strip():
    prompt = prompt.strip()
    if prompt.startswith("/"):
        new_gpt_prompt = gpt_prompt.copy()
        new_gpt_prompt.append({
            "role": "user",
            "content": prompt[1:]
        })

        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=new_gpt_prompt,
            stream=True)

        collected_messages = []
        for chunk in response:
            chunk_message = chunk['choices'][0]['delta']

            if "content" in chunk_message:
                collected_messages.append(chunk_message["content"])
                gpt_response = ''.join(collected_messages)
                prompt_helper.markdown(f"🤖 {gpt_response}")

        prompt = "".join([c for c in collected_messages])

        matches = re.findall(r'\*([^*]+)', prompt)
        if not matches or len(matches) == 0:
            st.warning("Cannot find prompt from ChatGPT response. Try again.", icon="⚠")
            st.stop()

        prompt = ""
        for match in matches:
            prompt += match.split("\n")[0] + " "

    if seed == -1:
        seed = None

    flags = ""
    if model == "Niji":
        flags += " --niji"
        if niji_style:
            flags += f" --style {niji_style.lower()}"
    else:
        if mid_style:
            flags += f" --style {mid_style.lower()}"
    if ar:
        flags += f" --ar {ar}"
    if tile:
        flags += " --tile"
    if creative:
        flags += f" --creative --{creative}"
    else:
        if quality:
            flags += f" --q {quality}"
    if stylize:
        flags += f" --stylize {stylize}"

    full_prompt = sender.send(prompt=prompt, seed=seed, flags=flags)

    st.session_state["history"] += f"- {full_prompt}\n"
    history.markdown(st.session_state["history"])

    # Result
    progress_bar.progress(0, "Waiting to start")

    while True:
        id, components = receiver.collecting_results(full_prompt)
        if not id:
            time.sleep(2.5)
            continue

        receiver.outputer()
        receiver.downloading_results()

        con.ping()
        with con:
            with con.cursor() as cur:
                cur.execute("select * from prompts where id = %s limit 1", (id,))
                row = cur.fetchone()

        if not row:
            continue

        prompt_helper.empty()

        try:
            progress_bar.progress(int(row["status"]), text=f"{row['status']}%")
        except:
            pass
        try:
            full_prompt_caption.caption(f"{row['full_prompt']} ({row['status']}%)")
        except:
            pass

        if row["url"]:
            try:
                result_image.image(row["url"])
            except:
                pass

        if row["status"] == 100:
            progress_bar.empty()
            st.session_state["latest_id"] = row["id"]

            def show_component(id, components, full_prompt):
                columns = st.columns(9)
                columns[0].button("❤️", on_click=like)

                if components:
                    column_index = 1
                    for comp in components:
                        for i, c in enumerate(comp["components"]):
                            if "upsample" in c["custom_id"]:
                                columns[column_index].button(f"U{i+1}", on_click=run_component, args=(id, "upsample", c["custom_id"], full_prompt, i))
                                column_index += 1
                            elif "variation" in c["custom_id"]:
                                columns[column_index].button(f"V{i+1}", on_click=run_component, args=(id, "variation", c["custom_id"], full_prompt, i))
                                column_index += 1

            def run_component(id, task, custom_id, full_prompt, image_index):
                sender.send_component(id, custom_id)

                with st.spinner(f"{task.capitalize()} Image #{image_index + 1}..."):
                    while True:
                        id, components = receiver.collecting_results(full_prompt)
                        if not id:
                            time.sleep(2.5)
                            continue

                        receiver.outputer()
                        receiver.downloading_results()

                        if id and components:
                            con.ping()
                            with con:
                                with con.cursor() as cur:
                                    cur.execute("select * from prompts where id = %s order by created_at desc limit 1", (id,))
                                    row = cur.fetchone()

                            if row["url"]:
                                try:
                                    st.session_state["latest_id"] = row["id"]

                                    st.image(row["url"])
                                    st.caption(full_prompt)
                                    show_component(id, components, full_prompt)
                                except:
                                    pass
                            break

                        time.sleep(2.5)

            show_component(id, components, full_prompt)

            break

        time.sleep(2.5)

    if dalle:
        with st.spinner('Waiting for DALL-E...'):
            dalle_prompt = full_prompt.split("--")[0]
            dalle_prompt = re.sub(r"[^a-zA-Z,\s]+", "", dalle_prompt).strip()
            dalle_res = openai.Image.create(
                prompt=full_prompt,
                n=1,
                size="1024x1024")
            dalle_result_image.image(dalle_res['data'][0]['url'])
            dalle_prompt_caption.caption(dalle_prompt)
