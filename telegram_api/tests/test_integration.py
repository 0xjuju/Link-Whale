from django.test import TestCase
from telegram_api.bot_factory import TelegramBotFactory


class TestIntegration(TestCase):
    def setUp(self):
        bot = TelegramBotFactory("example")

    def test_post_message(self):
        pass



