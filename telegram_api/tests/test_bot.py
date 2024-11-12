from django.test import TestCase
from unittest.mock import patch, MagicMock, AsyncMock
from telegram_api.bot_factory import TelegramBotFactory
import asyncio


class TelegramBotIntegrationTest(TestCase):
    """
    Integration test for the TelegramBotFactory.
    Simulate starting a bot instance, sending a message to a group, and asserting if the message is contained in the group messages.
    """

    @patch('telegram_api.bot_factory.telegram.Bot')
    @patch('telegram_api.bot_factory.asyncio.get_event_loop')
    def test_bot_send_and_receive_message(self, mock_get_event_loop, MockBot):
        # Mock Telegram Bot API
        mock_bot_instance = MockBot.return_value
        mock_message = MagicMock()
        mock_message.text = "Hello, Test Group!"
        mock_message.chat.id = 123456789  # Example group ID

        # Mock get_updates to return a list containing our mock message
        mock_bot_instance.get_updates.return_value = [MagicMock(message=mock_message)]

        # Mock the async call to get_me()
        mock_future = AsyncMock()
        mock_future.return_value.username = "example_bot"
        mock_get_event_loop.return_value.run_until_complete.return_value = mock_future.return_value

        # Initialize the bot factory with mocked group ID and bot token
        bot_name = "example"
        bot_factory = TelegramBotFactory(bot_name, group_id=mock_message.chat.id)

        # Send a message to the group
        test_message = "Hello, Test Group!"
        bot_factory.post_to_group(test_message)

        # Get messages from the group
        messages = bot_factory.get_group_messages()

        # Assert if the sent message is in the retrieved messages
        message_texts = [message.text for message in messages]
        self.assertIn(test_message, message_texts)
