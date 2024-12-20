import os

from dotenv import load_dotenv


class Config:
    def __init__(self, env_file: str = ".env"):
        if env_file:
            load_dotenv()
        self.bot_token = os.getenv("BOT_TOKEN")


config = Config()
