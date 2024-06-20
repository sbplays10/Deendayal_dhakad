
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
                    text=f"<b>ʜᴇʏ {user.mention},\n\n𝒀𝒐𝒖𝒓 𝑷𝒓𝒆𝒎𝒊𝒖𝒎 𝑨𝒄𝒄𝒆𝒔𝒔 𝑯𝒂𝒔 𝑬𝒙𝒑𝒊𝒓𝒆𝒅 𝑻𝒉𝒂𝒏𝒌 𝒀𝒐𝒖 𝑭𝒐𝒓 𝑼𝒔𝒊𝒏𝒈 𝑶𝒖𝒓 𝑺𝒆𝒓𝒗𝒊𝒄𝒆 😊.\n\n𝑰𝒇 𝒀𝒐𝒖 𝑾𝒂𝒏𝒕 𝑻𝒐 𝑻𝒂𝒌𝒆 𝑷𝒓𝒆𝒎𝒊𝒖𝒎 𝑨𝒈𝒂𝒊𝒏, 𝑻𝒉𝒆𝒏 𝑪𝒍𝒊𝒄𝒌 𝑶𝒏 𝑻𝒉𝒆 /plan 𝑭𝒐𝒓 𝑻𝒉𝒆 𝑫𝒆𝒕𝒂𝒊𝒍𝒔 𝑶𝑭 𝑻𝒉𝒆 𝑷𝒍𝒂𝒏𝒔...\n\n\nआपका 𝑷𝒓𝒆𝒎𝒊𝒖𝒎 𝑨𝒄𝒄𝒆𝒔𝒔 समाप्त हो गया है हमारी सेवा का उपयोग करने के लिए धन्यवाद 😊।\n\nयदि आप फिर से 𝑷𝒓𝒆𝒎𝒊𝒖𝒎 लेना चाहते हैं, तो योजनाओं के विवरण के लिए /𝒑𝒍𝒂𝒏 पर 𝑪𝒍𝒊𝒄𝒌 करें।</b>"
                )
                await client.send_message(LOG_CHANNEL, text=f"<b>#Premium_Expire\n\nUser name: {user.mention}\nUser id: <code>{user_id}</code>")
            except Exception as e:
                print(e)
            await sleep(0.5)
        await sleep(1)
    
