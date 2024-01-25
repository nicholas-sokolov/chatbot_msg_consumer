import time
from locust import HttpUser, task, between


class QuickstartUser(HttpUser):
    wait_time = between(1, 5)

    @task
    def conversation_started(self):
        self.client.post(
            "/viber/webhook",
            json={
                "event": "conversation_started",
                "timestamp": "12345",
                "chat_hostname": "SN-563_",
                "message_token": 5916837284433914371,
                "type": "open",
                "user": {
                    "id": "12345",
                    "name": "Sergey Rùdnev",
                    "avatar": "https://media-direct.cdn.viber.com/download_photo?dlid=MFojMvbS52ZImnxNQUHeU3zomFr47zbnIu6Zj613oDvnQmtgG--p0H_1mI7PPH10Y89AEuUTXTC_7k-j9elWuN6kQ3k1-uJgNEZQ_oJCpt84AB7tGnB4YiFOfeNmFb6bH4sCLw&fltp=jpg&imsz=0000",
                    "language": "en",
                    "country": "RU",
                    "api_version": 8
                },
                "subscribed": False
            },
        )
