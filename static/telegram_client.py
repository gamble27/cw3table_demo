import requests


class APIClientError(BaseException):
    def __init__(self, *args):
        BaseException.__init__(self, *args)


class TelegramAPIClient:
    def __init__(self, api=""):
        """
        Initializes a client for telegram bot
        :param api: telegram API key of your bot
        """
        if not api:
            raise APIClientError("no api detected")

        # part of url for bot api commands via POST http method
        self.url = "https://api.telegram.org/bot{API}/".format(API=api)

    def send_message(self, chat_id, text="Hello World"):
        """
        Sends an ordinary text message
        :param chat_id: id of recipient
        :param text: message text
        :return: None
        """
        if not chat_id:
            raise APIClientError("no chat id defined")
        parameters = {
            "chat_id": chat_id,
            "text":    text
        }
        requests.post(self.url + "sendMessage", json=parameters)

    def send_message_with_markdown(self, chat_id, text="Hello World", markdown="Markdown"):
        """
        Sends a message with markdown chosen
        :param chat_id:  id of recipient
        :param text: message text
        :param markdown: markdown type, can be "Markdown" or "HTML"
        :return: None
        """
        if not chat_id:
            raise APIClientError("no chat id defined")
        parameters = {
            "chat_id":      chat_id,
            "text":         text,
            "parse_mode":   markdown
        }
        requests.post(self.url + "sendMessage", json=parameters)

    def get_updates(self):
        """
        performs getUpdates API method
        :return: JSON dictionary containing
                 list of recent updates
        """
        response = requests.get(self.url + "getUpdates")
        update = response.json(encoding="utf-8")
        try:
            return update["result"]
        except KeyError:
            return None
        except Exception as e:
            return e

    def set_webhook(self, host):
        """
        Sets a web hook on given SSL protected server
        :param host: protected https server
        :return: None
        """
        if host:
            requests.post(self.url + 'setWebhook?url={}'.format(host))
        else:
            raise APIClientError("No host given")
