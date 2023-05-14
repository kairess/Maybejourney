import pandas as pd
from datetime import datetime
import os
import time
import requests
import re
from pprint import pprint

class Receiver():
    def __init__(self, config, local_path, user_id, con):
        self.params = config
        self.local_path = local_path
        self.user_id = user_id
        self.con = con
        self.last_full_prompt = None

        self.sender_initializer()

    def sender_initializer(self):
        self.channel_id = self.params["channel_id"]
        self.authorization = self.params["authorization"]
        self.headers = {"authorization" : self.authorization}

    def retrieve_messages(self):
        r = requests.get(
            f"https://discord.com/api/v10/channels/{self.channel_id}/messages?limit={10}", headers=self.headers)
        return r.json()

    def collecting_results(self, full_prompt_user):
        message_list  = self.retrieve_messages()

        for message in message_list:
            if (message["author"]["username"] == "Midjourney Bot") and ("**" in message["content"]):

                if full_prompt_user not in message["content"]:
                    continue

                ### Has attachments
                if len(message["attachments"]) > 0:
                    ### Done
                    if (message["attachments"][0]["filename"][-4:] == ".png") or ("(Open on website for full quality)" in message["content"]):
                        id = message["id"]
                        full_prompt = message["content"].split("**")[1]
                        prompt = full_prompt.split(" --")[0]
                        url = message["attachments"][0]["url"]
                        filename = message["attachments"][0]["filename"]

                        if not self.con.execute("select * from prompts where id = ? limit 1", (id,)).fetchone():
                            self.con.execute("insert into prompts (id, user_id, prompt, full_prompt, url, filename, is_downloaded, status, created_at) values (?, ?, ?, ?, ?, ?, ?, ?, ?)", (id, self.user_id, prompt, full_prompt, url, filename, 0, 100, str(datetime.now())))

                            self.con.execute("delete from prompts where user_id = ? and status != ?", (self.user_id, 100))
                            break
                    ### Rendering
                    else:
                        id = message["id"]
                        full_prompt = message["content"].split("**")[1]
                        prompt = full_prompt.split(" --")[0]
                        url = message["attachments"][0]["url"]

                        if ("(fast)" in message["content"]) or ("(relaxed)" in message["content"]):
                            try:
                                # status = re.findall("(\w*%)", message["content"])[0]
                                status = int(re.findall("(\d+)%", message["content"])[0])
                            except:
                                status = -1

                        if not self.con.execute("select * from prompts where id = ? limit 1", (id,)).fetchone():
                            self.con.execute("insert into prompts (id, user_id, prompt, full_prompt, url, is_downloaded, status, created_at) values (?, ?, ?, ?, ?, ?, ?, ?)", (id, self.user_id, prompt, full_prompt, url, 0, status, str(datetime.now())))
                            break
                        else:
                            self.con.execute("update prompts set url = ?, status = ? where id = ?", (url, status, id))
                            break
                ### Add to queue
                else:
                    id = message["id"]
                    full_prompt = message["content"].split("**")[1]
                    prompt = full_prompt.split(" --")[0]

                    status = -1
                    if "(Waiting to start)" in message["content"]:
                        status = 0

                    if not self.con.execute("select * from prompts where id = ? limit 1", (id,)).fetchone():
                        self.con.execute("insert into prompts (id, user_id, prompt, full_prompt, is_downloaded, status, created_at) values (?, ?, ?, ?, ?, ?, ?)", (id, self.user_id, prompt, full_prompt, 0, -1, str(datetime.now())))
                        break

    def outputer(self):
        waiting_for_download = self.con.execute("select full_prompt from prompts where is_downloaded = 0 and filename is not null and status = 100").fetchall()
        if len(waiting_for_download) > 0:
            print(datetime.now().strftime("%H:%M:%S"))
            print("waiting for download prompts: ", waiting_for_download)
            print("=========================================")

    def downloading_results(self):
        processed_prompts = []

        for row in self.con.execute("select * from prompts where is_downloaded = 0 and filename is not null and status = 100").fetchall():
            response = requests.get(row["url"])
            with open(os.path.join(self.local_path, row["filename"]), "wb") as req:
                req.write(response.content)

            self.con.execute("update prompts set is_downloaded = ? where id = ?", (1, row["id"]))
            processed_prompts.append(row["full_prompt"])

        if len(processed_prompts) > 0:
            print(datetime.now().strftime("%H:%M:%S"))
            print("processed prompts: ", processed_prompts)
            print("=========================================")


    def main(self):
        while True:
            self.collecting_results()
            self.outputer()
            self.downloading_results()
            time.sleep(5)


if __name__ == "__main__":
    from dotenv import dotenv_values
    import apsw
    import apsw.ext
    config = dotenv_values(".env")

    con = apsw.Connection("mj.db")
    def row_factory(cursor, row):
        columns = [t[0] for t in cursor.getdescription()]
        return dict(zip(columns, row))
    con.setrowtrace(row_factory)

    receiver = Receiver(config, "images", "fa632476-11ad-4052-b573-daa11e5ad4d0", con)
    receiver.main()
