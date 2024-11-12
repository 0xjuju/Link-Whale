from decouple import config
import telegram
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, CallbackContext
from telegram import Update
import asyncio


class TelegramBotFactory:
    """
    Factory class to create instances of Telegram bots.
    Each bot instance uses a unique key provided by the Telegram Bot API and can automatically retrieve the group ID.
    """

    def __init__(self, bot: str, group_id: str = None) -> None:
        """
        Initialize the factory by loading the Telegram bot key from the .env file.

        Args:
            bot (str): The name identifier of the bot.
            group_id (str, optional): The Telegram group chat ID. Defaults to None.
        """
        try:
            # Load the bot key from the .env file using decouple.config().
            self.bot_key: str = config(f'BOT_KEY_{bot.upper()}')
            self.client: telegram.Bot = telegram.Bot(token=self.bot_key)
            self.group_id: str = group_id if group_id is not None else None

            # Use asyncio to run get_me and retrieve the bot username
            self.bot_username: str = asyncio.get_event_loop().run_until_complete(self.client.get_me()).username

            # If group_id is None, try to automatically retrieve it from updates
            if self.group_id is None:
                self.group_id = self._retrieve_group_id()
        except Exception as e:
            print(f"Error initializing bot for {bot}: {e}")
            raise

    def _retrieve_group_id(self) -> str:
        """
        Retrieve the group ID from recent updates if the bot is already in a group.

        Returns:
            str: The group ID if found, otherwise None.
        """
        try:
            updates = self.client.get_updates()
            for update in updates:
                if update.message and update.message.chat.type in ['group', 'supergroup']:
                    print(f"Automatically retrieved group ID: {update.message.chat.id}")
                    return update.message.chat.id
        except Exception as e:
            print(f"Error retrieving group ID from updates: {e}")
        return None

    def post_to_group(self, message: str) -> None:
        """
        Post a message to a Telegram group.

        Args:
            message (str): The message to be posted to the group.
        """
        try:
            if self.group_id is None:
                print("Group ID is not set. Please use the /setgroup command to set it.")
                return
            self.client.send_message(chat_id=self.group_id, text=message)
        except Exception as e:
            print(f"Error posting message to group {self.group_id}: {e}")
            raise

    async def handle_mentions(self, update: Update, context: CallbackContext) -> None:
        """
        Handle messages that mention the bot by username.

        Args:
            update (Update): The incoming update.
            context (CallbackContext): The context of the callback.
        """
        message_text = update.message.text
        if message_text.startswith(f"@{self.bot_username}"):
            print(f"Mentioned message: {message_text}")
            chat = update.message.chat
            print(f"Group ID: {chat.id}")
            print(f"Group Title: {chat.title}")
            print(f"Sender Username: {update.message.from_user.username}")
            print(f"Sender First Name: {update.message.from_user.first_name}")

    async def set_group_id(self, update: Update, context: CallbackContext) -> None:
        """
        Command handler to set the group ID automatically when the bot is added to a group.

        Args:
            update (Update): The incoming update.
            context (CallbackContext): The context of the callback.
        """
        chat = update.message.chat
        if chat.type in ['group', 'supergroup']:
            self.group_id = chat.id
            print(f"Group ID set to: {self.group_id}")
            await update.message.reply_text(f"Group ID has been set to: {self.group_id}")
        else:
            await update.message.reply_text("This command can only be used in a group.")

    def get_group_messages(self, limit: int = 100) -> list:
        """
        Get a list of messages from the Telegram group.

        Args:
            limit (int): The maximum number of messages to retrieve (default is 100).

        Returns:
            list: A list of messages from the group.
        """
        try:
            updates = self.client.get_updates()
            messages = [update.message for update in updates if update.message and self.group_id is not None and update.message.chat.id == int(self.group_id)]
            return messages[:limit]
        except Exception as e:
            print(f"Error getting messages from group {self.group_id}: {e}")
            raise

    def start_bot(self) -> None:
        """
        Start the Telegram bot, handling errors if any occur.
        This method will be called from a different Celery task to start the bot as a background task.
        """
        try:
            print(f"Bot for group {self.group_id if self.group_id else 'not set'} is starting...")
            application = ApplicationBuilder().token(self.bot_key).build()

            if self.group_id is None:
                # Add command handler to set the group ID
                application.add_handler(CommandHandler('setgroup', self.set_group_id))

            # Add message handler to handle mentions of the bot
            mention_filter = filters.TEXT & filters.Regex(f"^@{self.bot_username}")
            application.add_handler(MessageHandler(mention_filter, self.handle_mentions))

            print(f"Bot for group {self.group_id if self.group_id else 'not set'} is running.")
            # Start polling to receive updates from Telegram
            application.run_polling()
        except Exception as e:
            print(f"Error occurred while running the bot for group {self.group_id}: {e}")
            # Handle stopping the bot if an error occurs
            print(f"Bot for group {self.group_id} is stopping due to an error.")
            raise
