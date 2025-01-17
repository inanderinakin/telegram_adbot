from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold
import sqlite3
import requests
import os

BOT_TOKEN = 'YOUR_TELEGRAM_BOT_API_KEY'
API_KEY = 'YOUR_GEMINI_API_KEY'

conn = sqlite3.connect('warnings.db')
cursor = conn.cursor()
cursor.execute('CREATE TABLE IF NOT EXISTS warnings(user_id int NOT NULL PRIMARY KEY, chat_id int, warning int)')

genai.configure(api_key=API_KEY)

generation_config = {
    "temperature": 1,
    "top_p": 0.95,
    "top_k": 40,
    "max_output_tokens": 8192,
    "response_mime_type": "text/plain",
}

model = genai.GenerativeModel(
    model_name="gemini-1.5-flash",
    generation_config=generation_config,
    system_instruction="""
    You will receive messages sent to a group. Your task is to determine whether these messages are advertisements.
    Respond only with 'Advertisement' or 'Not'. Do not include any additional sentences or explanations.
    Advertisers often manipulate words by adding excessive letters (e.g., "addddveeertissemennttt"). First, simplify the message by removing unnecessary letters to identify the core content.
    Advertisers often use words like 'VIP', 'Money', 'Special group', 'in my profile' and their various combinations. Be aware of these words because there is a high chance that the message is an advertisement.
    If the message promotes a product, service, or group (including links to groups), respond with 'Advertisement'.
    If the message does not contain any promotional content or inappropriate language, respond with 'Not'.
    If the message is unclear or incomplete, do not respond.
    Ensure your responses accurately reflect the nature of the messages to avoid false negatives.
    """
)

chat_session = model.start_chat()

def handle_response(text: str) -> str:
    processed: str = text.lower()
    response = chat_session.send_message(processed, safety_settings={
        HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
        HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
        HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
        HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE
    })
    return response.text

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text: str = update.message.text
    chatid = update.message.chat_id
    userid = update.message.from_user.id
    messageid = update.message.message_id

    chat_admins = await update.effective_chat.get_administrators()

    print(f'User  ({userid}): {text}')
    try:
        response: str = handle_response(text)
    except Exception as e:
        print(e)
        return
        
    print('Bot:', response.replace('\n', ''))
    if 'Advertisement' in response.strip():
        if update.effective_user not in (admin.user for admin in chat_admins):
            await context.bot.delete_message(chat_id=chatid, message_id=messageid)
            cursor.execute(f"SELECT warning FROM warnings WHERE user_id={userid} AND chat_id={chatid}")
            warningCount = cursor.fetchone()

            if warningCount is None:
                warningCount = 0 
                cursor.execute(f"INSERT INTO warnings (user_id, chat_id, warning) VALUES ({userid}, {chatid}, {warningCount + 1})")
            else:
                warningCount = warningCount[0]

                if warningCount == 2:
                    await context.bot.ban_chat_member(chat_id=chatid, user_id=userid)
                    return
                else:
                    cursor.execute(f"UPDATE warnings SET warning = {warningCount + 1} WHERE user_id = {userid} AND chat_id={chatid}")

            conn.commit()
        else:
            print("Won't delete the message because the user is admin")

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_admins = await update.effective_chat.get_administrators()
    chatid = update.message.chat_id
    messageid = update.message.message_id
    userid = update.message.from_user.id

    if update.message.photo[-1]:
        photo = update.message.photo[-1]
        file = await photo.get_file()
        file_path = os.path.join(os.getcwd(), photo.file_id + '.jpg')
        await file.download_to_drive(file_path)
    else:
        await update.message.reply_text("Couldn't download the image.")
    
    sample_file = genai.upload_file(path=file_path, display_name="AdOrNot")
    response = model.generate_content([sample_file, "In the provided image, you will see advertisements for Telegram groups. If you see any advertisement related content on the image, just type out 'Advertisement'. If you don't see any, type out 'Not'."])
    if 'Advertisement' in response.text:
        if update.effective_user not in (admin.user for admin in chat_admins):
            await context.bot.delete_message(chat_id=chatid, message_id=messageid)
            cursor.execute(f"SELECT warning FROM warnings WHERE user_id={userid} AND chat_id={chatid}")
            warningCount = cursor.fetchone()

            if warningCount is None:
                warningCount = 0 
                cursor.execute(f"INSERT INTO warnings (user_id, chat_id, warning) VALUES ({userid}, {chatid}, {warningCount + 1})")
            else:
                warningCount = warningCount[0]

                if warningCount == 2:
                    await context.bot.ban_chat_member(chat_id=chatid, user_id=userid)
                    return
                else:
                    cursor.execute(f"UPDATE warnings SET warning = {warningCount + 1} WHERE user_id = {userid} AND chat_id={chatid}")

            conn.commit()
        else:
            print("Won't delete the message because the user is admin")
    os.remove(file_path)

async def error(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print(f'{context.error}')

if __name__ == '__main__':
    print('Starting bot...')
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(MessageHandler(filters.TEXT, handle_message))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    app.add_error_handler(error)

    print('Polling...')
    app.run_polling(poll_interval=3)
