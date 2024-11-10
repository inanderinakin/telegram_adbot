
![Logo](https://i.imgur.com/7ex7Loz.png)


# Python Ad Bot

A simple Telegram bot that automatically collects messages sent to the groups it is in, analyzes each message using the Google Gemini API, determines whether it is an advertisement, and deletes the message if it is.

When the bot deletes a message, it adds a warning to the user who sent the message and stores the warnings in a local database. When the warning count reaches 3, it automatically bans the user.

I used the Gemini 1.5 Flash model to analyze messages, the SQLite3 library to log warning counts, and the python-telegram-bot to set up the bot.






## Setting up

Clone the project

```bash
  git clone https://github.com/inanderinakin/telegram_adbot.git
```

Go to the project directory

```bash
  cd telegram_adbot
```

Download necessary libraries using pip

```bash
  pip install -r requirements.txt
```

Get your API key from AI Studio

```bash
  https://aistudio.google.com/app/apikey
```

Create a Telegram bot using the username @BotFather in Telegram and obtain its TOKEN.

```bash
  https://t.me/BotFather
```

Paste in the key and the token to the given area

```bash
  BOT_TOKEN = 'YOUR_TELEGRAM_BOT_API_KEY'
  API_KEY = 'YOUR_GEMINI_API_KEY'
```

Start the bot

```bash
python main.py
```


## Documentation

[Google Gemini API](https://ai.google.dev/gemini-api/docs/quickstart?lang=python)

[python-telegram-bot](https://docs.python-telegram-bot.org/en/v21.7/)

