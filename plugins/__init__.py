
from aiohttp import web
from .route import routes
from asyncio import sleep 
from datetime import datetime
from database.users_chats_db import db
from info import LOG_CHANNEL

async def web_server():
    web_app = web.Application(client_max_size=30000000)
    web_app.add_routes(routes)
    return web_app

async def check_expired_premium(client):
    while 1:
        data = await db.get_expired(datetime.now())
        for user in data:
            user_id = user["id"]
            await db.remove_premium_access(user_id)
            try:
                user = await client.get_users(user_id)
                await client.send_message(
                    chat_id=user_id,
                    text=f"<b>ʜᴇʏ {user.mention},\n\n𝑌𝑜𝑢𝑟 𝑃𝑟𝑒𝑚𝑖𝑢𝑚 𝐴𝑐𝑐𝑒𝑠𝑠 𝐻𝑎𝑠 𝐸𝑥𝑝𝑖𝑟𝑒𝑑 𝑇ℎ𝑎𝑛𝑘 𝑌𝑜𝑢 𝐹𝑜𝑟 𝑈𝑠𝑖𝑛𝑔 𝑂𝑢𝑟 𝑆𝑒𝑟𝑣𝑖𝑐𝑒 😊. 𝐼𝑓 𝑌𝑜𝑢 𝑊𝑎𝑛𝑡 𝑇𝑜 𝑇𝑎𝑘𝑒 𝑃𝑟𝑒𝑚𝑖𝑢𝑚 𝐴𝑔𝑎𝑖𝑛, 𝑇ℎ𝑒𝑛 𝐶𝑙𝑖𝑐𝑘 𝑂𝑛 𝑇ℎ𝑒 /plan 𝐹𝑜𝑟 𝑇ℎ𝑒 𝐷𝑒𝑡𝑎𝑖𝑙𝑠 𝑂𝐹 𝑇ℎ𝑒 𝑃𝑙𝑎𝑛𝑠..\n\n\n<blockquote>आपका 𝑷𝒓𝒆𝒎𝒊𝒖𝒎 𝑨𝒄𝒄𝒆𝒔𝒔 समाप्त हो गया है हमारी सेवा का उपयोग करने के लिए धन्यवाद 😊। यदि आप फिर से 𝑷𝒓𝒆𝒎𝒊𝒖𝒎 लेना चाहते हैं, तो योजनाओं के विवरण के लिए /plan पर 𝑪𝒍𝒊𝒄𝒌 करें।</blockquote></b>"
                )
                await client.send_message(LOG_CHANNEL, text=f"<b>#Premium_Expire\n\nUser name: {user.mention}\nUser id: <code>{user_id}</code>")
            except Exception as e:
                print(e)
            await sleep(0.5)
        await sleep(1)



import re
import asyncio
import logging  
from pyrogram import Client, errors
from motor.motor_asyncio import AsyncIOMotorClient
from info import COLLECTION_NAME, LOG_CHANNEL, DATABASE_NAME, DATABASE_URI, GRP_LNK
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
# Configure logging
logging.basicConfig(
    filename='app.log',
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Initialize MongoDB client and database
db_client = AsyncIOMotorClient(DATABASE_URI)
db = db_client[DATABASE_NAME]
collection = db[COLLECTION_NAME]
sent_files_collection = db["sent_files"]


initial_delay = 1.5  # Initial delay in seconds between sending messages
current_delay = initial_delay  # Current delay, adjusted dynamically


def is_alphanumeric(string):
    return bool(re.match('^[a-zA-Z0-9 ]*$', string))


def process_message(msg):
    if not is_alphanumeric(msg):
        return None

    processed_msg = msg
    patterns = [
        (r'\bE\d{1,2}\b', lambda m: m.end()),
        (r'\bS\d{1,2}E\d{1,2}\b', lambda m: m.end()),
        (r'\b(19\d{2}|20\d{2})\b', lambda m: m.end()),
        (r'\b(2160p|1440p|1080p|720p|480p|360p|240p)\b', lambda m: m.end())
    ]

    for pattern, end_func in patterns:
        match = re.search(pattern, msg)
        if match:
            processed_msg = msg[:end_func(match)].strip()
            break

    return processed_msg if len(processed_msg) <= 35 else processed_msg[:32] + "..."

# Function to extract quality and language information
def extract_quality_and_language(file_name):
    quality_patterns = [
        r'\b(WEBRip|HDRip|HEVC|HDR|WEB[-_]?DL|BluRay|PreDVD|HDTVRip|HDCAM|CAMRip|BRRip|DVDRip|BDRip|DVDScr)\b',
        r'\b(2160p|1440p|1080p|720p|480p|360p|240p)\b'
    ]
    language_patterns = [
        r'\b(Hindi|English|Tamil|Telugu|Malayalam|Punjabi|Korean)\b'
    ]

    quality = [match.group() for pattern in quality_patterns for match in re.finditer(pattern, file_name, re.IGNORECASE)]
    languages = [match.group() for pattern in language_patterns for match in re.finditer(pattern, file_name, re.IGNORECASE)]

    return quality, languages


async def send_new_file_notification(client, file_name, quality, languages):
    global current_delay

    quality_message = f"Quality: {', '.join(quality)}" if quality else "Quality: None"
    language_message = f"Audio: {', '.join(languages)}" if languages else "Audio: No idea 😄"

    message = (
        "Nᴇᴡ Fɪʟᴇ Uᴘʟᴏᴀᴅᴇᴅ ✅\n\n"
        f"Name: <code>{file_name}</code>\n\n"
        f"{quality_message}\n\n"
        f"{language_message}"
    )

    # Create inline keyboard with a button
    keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("⚡️ Sᴇᴀʀᴄʜ Fɪʟᴇ Hᴇʀᴇ", url=GRP_LNK)]])

    while True:
        try:
            await client.send_message(chat_id=LOG_CHANNEL, text=message, reply_markup=keyboard)
            await asyncio.sleep(current_delay)
            current_delay = initial_delay
            await sent_files_collection.insert_one({"file_name": file_name})
            logging.info(f"Notification sent for file: {file_name}")
            break
        except errors.FloodWait as e:
            current_delay += e.value
            logging.warning(f"Flood wait of {e.value} seconds. Retrying...")
            await asyncio.sleep(e.value)
        except errors.RPCError as rpc_error:
            logging.error(f"Error sending notification: {rpc_error}")
            break

# Function to check if a file name has already been sent
async def is_duplicate_file(file_name):
    split_file_name = re.split(r'[_\-+\.]', file_name)
    base_name = ' '.join(split_file_name).lower()
    processed_file_name = process_message(base_name)
    if processed_file_name:
        existing_file = await sent_files_collection.find_one({"file_name": processed_file_name})
        return existing_file is not None
    return False

# Create a set to store the processed file names
processed_files = set()

# Function to watch changes in the collection
async def watch_collection(client):
    async with collection.watch() as stream:
        async for change in stream:
            if change["operationType"] == "insert":
                document = change["fullDocument"]
                file_name = re.sub(r"[_\-+\.]", " ", document.get("file_name", ""))

                if await is_duplicate_file(file_name):
                    logging.debug(f"Duplicate file detected: {file_name}")
                    continue

                quality, languages = extract_quality_and_language(file_name)
                processed_file_name = process_message(file_name)
                if processed_file_name and processed_file_name not in processed_files:
                    await send_new_file_notification(client, processed_file_name, quality, languages)
                    processed_files.add(processed_file_name)
                    logging.info(f"Processed file: {file_name}")

