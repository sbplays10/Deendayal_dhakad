
import re
import asyncio
import logging  
from pyrogram import Client, errors
from motor.motor_asyncio import AsyncIOMotorClient
from info import COLLECTION_NAME, LOG_CHANNEL, DATABASE_NAME, DATABASE_URI, GRP_LNK, FILE_UPDATE_CHANNEL
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
        (r'\bS\d{1,2}\b', lambda m: m.end()),
        (r'\b(19\d{2}|20\d{2})\b', lambda m: m.end()),
        (r'\b(2160p|1440p|1080p|720p|480p|360p|240p)\b', lambda m: m.end())
    ]

    for pattern, end_func in patterns:
        match = re.search(pattern, msg)
        if match:
            processed_msg = msg[:end_func(match)].strip()
            break

    return processed_msg if len(processed_msg) <= 100 else processed_msg[:97] + "..."

# Function to extract quality and language information
def extract_quality_and_language(file_name):
    quality_patterns = [
        r'\b(WEBRip|HDRip|HEVC|HDR|WEB[-_]?DL|BluRay|PreDVD|HDTVRip|HDCAM|CAMRip|BRRip|DVDRip|BDRip|DVDScr)\b',
       # r'\b(2160p|1440p|1080p|720p|480p|360p|240p)\b'
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
        "#𝑵𝒆𝒘_𝑭𝒊𝒍𝒆_𝑼𝒑𝒍𝒐𝒂𝒅𝒆𝒅 ✅\n\n"
        f"🪔 Name: <code>{file_name}</code>\n\n"
        f"⚜️ {quality_message}\n\n"
        f"‼️ {language_message}"
    )

    # Create inline keyboard with a button
    keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("⚡️ Sᴇᴀʀᴄʜ Fɪʟᴇ Hᴇʀᴇ", url=GRP_LNK)]])

    while True:
        try:
            await client.send_message(chat_id=FILE_UPDATE_CHANNEL, text=message, reply_markup=keyboard)
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

