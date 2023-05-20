import requests
import re
import time
import random

class Sender():
    def __init__(self, config):
        self.params = config
        self.sender_initializer()

    def sender_initializer(self):
        self.channel_id = self.params["channel_id"]
        self.authorization = self.params["authorization"]
        self.application_id = self.params["application_id"]
        self.guild_id = self.params["guild_id"]
        self.session_id = self.params["session_id"]
        self.version = self.params["version"]
        self.id = self.params["id"]

    def send(self, prompt, seed=None, flags=""):
        header = {
            "authorization": self.authorization
        }

        prompt = prompt.replace("_", " ")
        prompt = " ".join(prompt.split())
        prompt = re.sub(r"[^a-zA-Z0-9:,\-\s]+", "", prompt)
        prompt = prompt.lower()

        if seed is None:
            seed = random.randint(0, 4294967295)

        full_prompt = f"{str(prompt)} --seed {int(seed)} {flags}".strip()
        full_prompt = re.sub(r"\s+", " ", full_prompt)

        payload = {
            "type": 2, 
            "application_id": self.application_id,
            "guild_id": self.guild_id,
            "channel_id": self.channel_id,
            "session_id": self.session_id,
            "data": {
                "version": self.version,
                "id": self.id,
                "name": "imagine",
                "type": 1,
                "options": [{
                    "type": 3,
                    "name": "prompt",
                    "value": f"{full_prompt}",
                }],
                "attachments": []
            },
        }

        r = requests.post("https://discord.com/api/v9/interactions", json = payload , headers = header)
        while r.status_code != 204:
            r = requests.post("https://discord.com/api/v9/interactions", json = payload , headers = header)
            time.sleep(1)

        print(f"Prompt [{full_prompt}] successfully sent!")

        return full_prompt

    def send_component(self, message_id, custom_id):
        header = {
            "authorization": self.authorization
        }

        payload = {
            "type": 3,
            "application_id": self.application_id,
            "guild_id": self.guild_id,
            "channel_id": self.channel_id,
            "session_id": self.session_id,
            "data": {
                "component_type": 2,
                "custom_id": custom_id,
            },
            "message_flags": 0,
            "message_id": message_id,
        }

        r = requests.post("https://discord.com/api/v9/interactions", json = payload , headers = header)
        while r.status_code != 204:
            r = requests.post("https://discord.com/api/v9/interactions", json = payload , headers = header)
            time.sleep(1)

        print(f"[{custom_id}] successfully sent!")

    def send_describe(self, filename, uploaded_filename):
        header = {
            "authorization": self.authorization
        }

        payload = {
            "type": 2, 
            "application_id": self.application_id,
            "guild_id": self.guild_id,
            "channel_id": self.channel_id,
            "session_id": self.session_id,
            "data": {
                "version": self.version,
                "id": self.id,
                "name": "describe",
                "type": 1,
                "options": [{
                    "type": 11,
                    "name": "image",
                    "value": 0
                }],
                "attachments": [{
                    "id": "0",
                    "filename": filename,
                    "uploaded_filename": uploaded_filename
                }],
            },
        }

        r = requests.post("https://discord.com/api/v9/interactions", json = payload , headers = header)
        while r.status_code != 204:
            r = requests.post("https://discord.com/api/v9/interactions", json = payload , headers = header)
            time.sleep(1)

        print(f"Describe [{filename}] successfully sent!")

    def send_info(self):
        header = {
            "authorization": self.authorization
        }

        payload = {
            "type": 2, 
            "application_id": self.application_id,
            "guild_id": self.guild_id,
            "channel_id": self.channel_id,
            "session_id": self.session_id,
            "data": {
                "version": self.version,
                "id": self.id,
                "name": "info",
                "type": 1,
                "options": [],
                "attachments": [],
            },
        }

        r = requests.post("https://discord.com/api/v9/interactions", json = payload , headers = header)
        while r.status_code != 204:
            r = requests.post("https://discord.com/api/v9/interactions", json = payload , headers = header)
            time.sleep(1)

        print(f"Info successfully sent!")
