class RedisConfig:
    def __init__(self, host, port, password):
        self.host = host
        self.port = port
        self.password = password


class TelegramConfig:
    def __init__(self):
        # USE FROM CONFIG
        bot_key = "845629642:AAH83c0oyPH8MT5QuuuoP-KtqbVdb4mufoE"
        self.base = "https://api.telegram.org"
        self.path = f"/bot{bot_key}/sendMessage"
        self.params = {"chat_id": "-1001431223078", "text": ""}

    def get_params(self, text):
        self.params["text"] = text
        return self.params
