import asyncio
import sys
from datetime import datetime, time as dt_time, timedelta
from pytz import timezone
from telethon import TelegramClient, functions, types

# ================= SETTINGS =================
API_ID = 34953498
API_HASH = "12c4099cecb691f89f6b4b7d911f4489"
BOT_TOKEN = "8595114858:AAHsnPql_AO5Xj8bVp0EEmVlBVJYZjmk9uQ"
GROUP_ID = -1003672239001
TIMEZONE = "Asia/Kolkata"

SCHEDULE = [
    {"market": "FARIDABAD", "open": dt_time(16, 50), "close": dt_time(17, 50)},
    {"market": "GHAZIABAD", "open": dt_time(18, 20), "close": dt_time(21, 0)},
    {"market": "GALI", "open": dt_time(22, 0), "close": dt_time(23, 30)},
    {"market": "DESAWAR", "open": dt_time(0, 0), "close": dt_time(5, 0)},
]

client = TelegramClient("one_group_manager", API_ID, API_HASH)

lock_rights = types.ChatBannedRights(until_date=None, send_messages=True)
unlock_rights = types.ChatBannedRights(until_date=None, send_messages=False)

async def scheduler(target):
    print("⏰ Scheduler is active and watching the clock...")
    executed_today = set()
    last_reset_date = None

    while True:
        try:
            tz = timezone(TIMEZONE)
            now = datetime.now(tz)
            current_date = now.strftime("%Y-%m-%d")
            current_min = now.strftime("%H:%M")

            if last_reset_date != current_date:
                executed_today.clear()
                last_reset_date = current_date
                print(f"📅 Date changed. Resetting for {current_date}")

            for s in SCHEDULE:
                m_name = s["market"]
                open_t = datetime.combine(now.date(), s["open"])
                close_t = datetime.combine(now.date(), s["close"])

                if s["close"] < s["open"]:
                    if now.time() >= s["open"]: close_t += timedelta(days=1)
                    else: open_t -= timedelta(days=1)

                times = {
                    "w10": (close_t - timedelta(minutes=10)).strftime("%H:%M"),
                    "w5": (close_t - timedelta(minutes=5)).strftime("%H:%M"),
                    "open": open_t.strftime("%H:%M"),
                    "close": close_t.strftime("%H:%M")
                }

                # --- Independent 'if' blocks ensure nothing is skipped ---
                
                # Open
                if current_min == times["open"]:
                    key = f"{m_name}_{current_date}_open"
                    if key not in executed_today:
                        executed_today.add(key) # Mark as done first
                        await client(functions.messages.EditChatDefaultBannedRightsRequest(peer=target, banned_rights=unlock_rights))
                        await client.send_message(target, f"🔓 {m_name} शुरू हो गया है!\nअब एंट्री चालू है।")

                # 10 Min Warning
                if current_min == times["w10"]:
                    key = f"{m_name}_{current_date}_w10"
                    if key not in executed_today:
                        executed_today.add(key)
                        await client.send_message(target, f"⚠️ ध्यान दें!\n\n{m_name} ग्रुप 10 मिनट में बंद होने वाला है।")

                # 5 Min Warning
                if current_min == times["w5"]:
                    key = f"{m_name}_{current_date}_w5"
                    if key not in executed_today:
                        executed_today.add(key)
                        await client.send_message(target, f"🚨 अंतिम चेतावनी!\n\n{m_name} ग्रुप 5 मिनट में बंद हो जाएगा।")

                # Close
                if current_min == times["close"]:
                    key = f"{m_name}_{current_date}_close"
                    if key not in executed_today:
                        executed_today.add(key)
                        await client(functions.messages.EditChatDefaultBannedRightsRequest(peer=target, banned_rights=lock_rights))
                        await client.send_message(target, f"🔒 {m_name} अब बंद हो गया है!")

        except Exception as e:
            print(f"⚠️ Error: {e}")
            await asyncio.sleep(5)
            continue

        # Precision sleep to start of next minute
        now_end = datetime.now(timezone(TIMEZONE))
        await asyncio.sleep(60 - now_end.second)

async def main():
    # 'async with' automatically handles connecting and disconnecting
    async with client:
        await client.start(bot_token=BOT_TOKEN)
        
        try:
            target = await client.get_input_entity(GROUP_ID)
            await client.get_entity(target) 
            print("✅ Bot is connected and group is resolved.")
            
            # Use asyncio.create_task to run scheduler in background
            asyncio.create_task(scheduler(target))
            
            # Keep the bot running
            await client.run_until_disconnected()
            
        except Exception as e:
            print(f"❌ Startup Error: {e}")

if __name__ == "__main__":
    try:
        # This is the modern way to run the bot in Python 3.12/3.14
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n🛑 Bot stopped.")
    except Exception as e:
        print(f"❌ Unexpected Error: {e}")