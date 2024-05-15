import telebot
from dotenv import load_dotenv
from os import environ
import google.generativeai as genai
import os
from dotenv import load_dotenv
from PIL import Image
import fitz

load_dotenv()
bot_token = environ.get("bot_token")
GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')
genai.configure(api_key=GOOGLE_API_KEY)
model = genai.GenerativeModel('gemini-1.5-pro-latest')
chat = model.start_chat(history=[])

# Inicializa o bot do Telegram
bot = telebot.TeleBot(bot_token)

def get_document(pdf_file_path):
    doc = fitz.open(pdf_file_path)
    page_num = doc.page_count
    output = []
    for i in range(page_num):
        page = doc.load_page(i)  # number of page
        pix = page.get_pixmap()
        output.append("./outfile{}.png".format(i))
        pix.save(output[i])
    doc.close()
    return output

# Manipulador de mensagens de texto
@bot.message_handler(func=lambda message: True)
def handle_message(message):
    chat_id = message.chat.id
    text = message.text 
    try:
        response = chat.send_message(text)
        bot.send_message(chat_id, response.text, parse_mode='markdown')
    except:
        try:
            bot.send_message(chat_id, response.text)
        except Exception as inst:
            print(inst)

# Manipulador de fotos
@bot.message_handler(content_types=['photo'])
def handle_photo(message):
    chat_id = message.chat.id
    file_id = message.photo[-1].file_id # Pega a foto de maior resolução
    text = message.caption 

    file_info = bot.get_file(file_id)
    downloaded_file = bot.download_file(file_info.file_path)

    with open('./temp.jpg', 'wb') as new_file:
        new_file.write(downloaded_file)

    image = Image.open('./temp.jpg')
    response = chat.send_message([text, image])
    try:
        bot.send_message(chat_id, response.text, parse_mode='markdown')
    except:
        try:
            bot.send_message(chat_id, response.text)
        except Exception as inst:
            print(inst)   

    os.remove('./temp.jpg')

# Manipulador de documentos PDF
@bot.message_handler(content_types=['document'])
def handle_document(message):
    chat_id = message.chat.id
    file_id = message.document.file_id
    text = message.caption 

    file_info = bot.get_file(file_id)
    downloaded_file = bot.download_file(file_info.file_path)

    with open('./temp.pdf', 'wb') as new_file:
        new_file.write(downloaded_file)

    pdf_obj = get_document('./temp.pdf')
    os.remove('./temp.pdf')

    # Implemente a lógica para enviar as imagens do PDF para o Gemini
    files = []
    for p in range(len(pdf_obj)):
        files.append(genai.upload_file(path=pdf_obj[p]))
    try:
        response = chat.send_message([text] + files)
        bot.send_message(chat_id, response.text, parse_mode='markdown')
    except:
        try:
            bot.send_message(chat_id, response.text)   
        except Exception as inst:
            print(inst)
    for arquivo in pdf_obj:
            os.remove(arquivo)
            
# Manipulador de áudios
@bot.message_handler(content_types=['audio'])
def handle_audio(message):
    chat_id = message.chat.id
    
    if message.audio:
        file_id = message.audio.file_id
        text = message.caption
        #file_name = 'temp.ogg' 
    elif message.document.mime_type in ['audio/mpeg', 'audio/wav', 'audio/ogg']:
        file_id = message.document.file_id
        text = message.caption
        #file_name = f'temp.{message.document.mime_type.split("/")[-1]}'
    else:
        bot.reply_to(message, "Formato de áudio não suportado. Envie um arquivo MP3, WAV, OGA ou uma gravação de voz.")
        return

    file_info = bot.get_file(file_id)
    downloaded_file = bot.download_file(file_info.file_path)

    with open(f'./{file_info.file_path}', 'wb') as new_file:
        new_file.write(downloaded_file)

    audio_file = genai.upload_file(f'./{file_info.file_path}')  
    try:        
        response = chat.send_message([text, audio_file])
        bot.send_message(chat_id, response.text, parse_mode='markdown')
    except:
        try:
            bot.send_message(chat_id, response.text)
        except Exception as inst:
            print(inst)
    os.remove(f'./{file_info.file_path}')
    
# Manipulador de mensagens de voz
@bot.message_handler(content_types=['voice'])
def handle_voice(message):
    chat_id = message.chat.id
    file_id = message.voice.file_id
    if message.voice:
        file_id = message.voice.file_id
        file_name = 'temp.ogg' 
        text = ''
    elif message.document.mime_type in ['audio/mpeg', 'audio/wav', 'audio/ogg']:
        file_id = message.document.file_id
        text = message.caption
        file_name = f'temp.{message.document.mime_type.split("/")[-1]}'
    else:
        bot.reply_to(message, "Formato de áudio não suportado. Envie um arquivo MP3, WAV, OGA ou uma gravação de voz.")
        return

    file_info = bot.get_file(file_id)
    downloaded_file = bot.download_file(file_info.file_path)
    with open(f'./{file_name}', 'wb') as new_file:
        new_file.write(downloaded_file)

    audio_file = genai.upload_file(f'./{file_name}',mime_type='audio/ogg')          
    response = chat.send_message([text, audio_file])
    try:
        bot.send_message(chat_id, response.text, parse_mode='markdown')
    except: 
        try:
            bot.send_message(chat_id, response.text)
        except Exception as inst:
            print(inst)       
              
    os.remove(f'./{file_name}')
    
# Inicia o bot..
bot.polling()
