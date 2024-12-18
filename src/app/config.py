from dotenv import load_dotenv

import os


class Config:
    def __init__(self, env_file: str = ".env"):
        if env_file:
            load_dotenv()
        self.api_key = os.getenv("API_KEY", "")


config = Config()