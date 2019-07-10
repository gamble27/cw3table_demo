import requests


class APIClientError(BaseException):
    def __init__(self, *args):
        BaseException.__init__(self, *args)


class TelegramAPIClient:
    def __init__(self, api=""):
        if not api:
            raise APIClientError("no api detected")
        self.url = "https://api.telegram.org/bot{API}/".format(API=api)

    def send_message(self, chat_id, text="Hello World"):
        if not chat_id:
            raise APIClientError("no chat id defined")
        parameters = {
            "chat_id": chat_id,
            "text":    text
        }
        requests.post(self.url + "sendMessage", json=parameters)

    def get_updates(self):
        response = requests.get(self.url + "getUpdates")
        update = response.json(encoding="utf-8")
        try:
            return update["result"]
        except KeyError:
            return None
        except Exception as e:
            return e

    def set_webhook(self, host):
        if host:
            requests.post(self.url + 'setWebhook?url={}'.format(host))
        else:
            raise APIClientError("No host given")
