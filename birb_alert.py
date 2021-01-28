from discord_webhooks import DiscordWebhooks


class BirbAlert:
    def __init__(self, url):
        self.url = url
        self.webhook = DiscordWebhooks(self.url)

    def send_message(self, msg):
        self.webhook.set_content(content=msg)
        self.webhook.send()


if __name__ == '__main__':
    print('This is not standalone script')

