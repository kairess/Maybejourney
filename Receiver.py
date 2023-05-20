from datetime import datetime
import os
import time
import requests
import re

class Receiver():
    def __init__(self, config, local_path, user_id, con):
        self.params = config
        self.local_path = local_path
        self.user_id = user_id
        self.con = con

        self.sender_initializer()

    def sender_initializer(self):
        self.channel_id = self.params["channel_id"]
        self.authorization = self.params["authorization"]
        self.headers = {"authorization" : self.authorization}

    def retrieve_messages(self):
        r = requests.get(
            f"https://discord.com/api/v10/channels/{self.channel_id}/messages?limit={10}", headers=self.headers)
        return r.json()
    
    def collecting_describes(self, filename):
        message_list  = self.retrieve_messages()

        for message in message_list:
            if (message["author"]["username"] == "Midjourney Bot"):
                if "embeds" in message and len(message["embeds"]) > 0 and "image" in message["embeds"][0] and "description" in message["embeds"][0]:
                    if filename not in message["embeds"][0]["image"]["url"]:
                        continue

                    return message["embeds"][0]["description"], message["embeds"][0]["image"]["url"]

        return None, None

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
                        components = message["components"]

                        self.con.ping()
                        with self.con:
                            with self.con.cursor() as cur:
                                cur.execute("select * from prompts where id = %s limit 1", (id,))
                                row = cur.fetchone()
                            if not row:
                                with self.con.cursor() as cur:
                                    cur.execute("insert into prompts (id, user_id, prompt, full_prompt, url, filename, is_downloaded, status) values (%s, %s, %s, %s, %s, %s, %s, %s)", (id, self.user_id, prompt, full_prompt, url, filename, 0, 100))
                                    self.con.commit()

                                    cur.execute("delete from prompts where user_id = %s and status != %s", (self.user_id, 100))
                                    self.con.commit()
                                return id, components
                    ### Rendering
                    else:
                        id = message["id"]
                        full_prompt = message["content"].split("**")[1]
                        prompt = full_prompt.split(" --")[0]
                        url = message["attachments"][0]["url"]

                        if ("(fast)" in message["content"]) or ("(relaxed)" in message["content"]) or ("(fast, stealth)" in message["content"]) :
                            try:
                                status = int(re.findall("(\d+)%", message["content"])[0])
                            except:
                                status = -1

                        self.con.ping()
                        with self.con:
                            with self.con.cursor() as cur:
                                cur.execute("select * from prompts where id = %s limit 1", (id,))
                            row = cur.fetchone()
                            if not row:
                                with self.con.cursor() as cur:
                                    cur.execute("insert into prompts (id, user_id, prompt, full_prompt, url, is_downloaded, status) values (%s, %s, %s, %s, %s, %s, %s)", (id, self.user_id, prompt, full_prompt, url, 0, status))
                                    self.con.commit()
                                return id, None
                            else:
                                with self.con.cursor() as cur:
                                    cur.execute("update prompts set url = %s, status = %s where id = %s", (url, status, id))
                                    self.con.commit()
                                return id, None
                ### Add to queue
                else:
                    id = message["id"]
                    full_prompt = message["content"].split("**")[1]
                    prompt = full_prompt.split(" --")[0]

                    status = -1
                    if "(Waiting to start)" in message["content"]:
                        status = 0

                    self.con.ping()
                    with self.con:
                        with self.con.cursor() as cur:
                            cur.execute("select * from prompts where id = %s limit 1", (id,))
                            row = cur.fetchone()

                    if not row:
                        self.con.ping()
                        with self.con:
                            with self.con.cursor() as cur:
                                cur.execute("insert into prompts (id, user_id, prompt, full_prompt, is_downloaded, status) values (%s, %s, %s, %s, %s, %s)", (id, self.user_id, prompt, full_prompt, 0, -1))
                                self.con.commit()
                            return id, None
        return False, None

    def outputer(self):
        self.con.ping()
        with self.con:
            with self.con.cursor() as cur:
                cur.execute("select full_prompt from prompts where is_downloaded = 0 and filename is not null and status = 100")
                waiting_for_download = cur.fetchall()
        if len(waiting_for_download) > 0:
            print(datetime.now().strftime("%H:%M:%S"))
            print("waiting for download prompts: ", waiting_for_download)
            print("=========================================")

    def downloading_results(self):
        processed_prompts = []

        self.con.ping()
        with self.con:
            with self.con.cursor() as cur:
                cur.execute("select * from prompts where is_downloaded = 0 and filename is not null and status = 100")
                for row in cur.fetchall():
                    response = requests.get(row["url"])
                    with open(os.path.join(self.local_path, row["filename"]), "wb") as req:
                        req.write(response.content)

                    cur.execute("update prompts set is_downloaded = %s where id = %s", (1, row["id"]))
                    self.con.commit()
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
