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
        prompt = re.sub(r"[^a-zA-Z0-9\s]+", "", prompt)
        prompt = prompt.lower()

        if seed is None:
            seed = random.randint(0, 4294967295)

        full_prompt = f"{str(prompt)} --seed {int(seed)} {flags}".strip()

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
                    "value": f"{full_prompt} --q .25",
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
