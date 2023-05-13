from dotenv import dotenv_values
from Sender import Sender

config = dotenv_values(".env")

sender = Sender(config=config)

prompt = sender.send(prompt="love2", flags="")

print(f"prompt: {prompt}")
# a man --seed 2763059021