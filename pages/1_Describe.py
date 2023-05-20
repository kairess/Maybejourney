import streamlit as st
import time
import openai
import requests
from Sender import Sender
from Receiver import Receiver
from footer import footer
from helpers import *


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
        "version": "1092492867185950853",
        "id": "1092492867185950852",
        "openai_api_key": st.secrets["openai_api_key"],
    }
    return config

config = load_config()
openai.api_key = config["openai_api_key"]

if "page" not in st.session_state:
    st.session_state["page"] = 0
if "done" not in st.session_state:
    st.session_state["done"] = False
st.session_state["page"] = 0
st.session_state["done"] = False

@st.cache_resource
def load_resources():
    return Sender(config=config), Receiver(config, "images", None, None)
sender, receiver = load_resources()

# https://stackoverflow.com/questions/76092002/uploading-files-to-discord-api-thought-put-using-python-requests
def upload_file(file):
    filename = file.name
    file_size = file.size

    api_response = requests.post(
        f"https://discord.com/api/v9/channels/{config['channel_id']}/attachments",
        headers={"authorization": config["authorization"]},
        json={"files": [{"filename": filename, "file_size": file_size, "id": 1}]},
    )
    api_response.raise_for_status()
    attachment_info = api_response.json()["attachments"][0]
    put_url = attachment_info["upload_url"]
    put_response = requests.put(
        put_url,
        headers={
            "Content-Length": str(file_size),
            "Content-Type": "image/png",
            "authorization": config["authorization"],
        },
        data=file,
    )
    put_response.raise_for_status()
    return attachment_info


# UI
st.header("Describe")

# Prompt
with st.form("prompt-form"):
    file = st.file_uploader("Image", type=["png", "jpg", "jpeg", "webp", "heic"])
    submit_button = st.form_submit_button("Submit")

footer(*footer_content)

# Function
if submit_button and file:
    with st.spinner("Describing..."):
        attachment = upload_file(file)

        filename = file.name
        uploaded_filename = attachment["upload_filename"]

        sender.send_describe(filename, uploaded_filename)

        while True:
            time.sleep(2.5)

            description, image = receiver.collecting_describes(filename)

            if description and image:
                st.markdown(description)
                st.image(image)
                break
