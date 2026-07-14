#!/usr/bin/env python3
"""
Telegram Bot Token Checker & Setup Helper
Run this after setting your BOT_TOKEN to verify everything works.
"""

import os
import sys
import json

BOT_TOKEN = os.environ.get("TELEGRAM_WIG_BOT_TOKEN", "")

if not BOT_TOKEN or BOT_TOKEN == "YOUR_BOT_TOKEN_HERE":
    print("=" * 60)
    print("TELEGRAM BOT SETUP REQUIRED")
    print("=" * 60)
    print()
    print("You need a dedicated bot for the WorthItGoods channel.")
    print()
    print("1. Open Telegram and search for @BotFather")
    print("2. Send: /newbot")
    print("3. Name: WorthItGoods Bot")
    print("4. Username: worthitgoods_bot (or similar)")
    print("5. BotFather will give you an API token like:")
    print("   1234567890:ABCdefGHIjklmNOPqrstUVwxyz")
    print()
    print("6. Then create a channel:")
    print("   - Open Telegram → New Channel")
    print("   - Name: WorthItGoods — Honest Product Finds")
    print("   - Public link: @worthitgoods")
    print("   - Add your new bot as an Administrator")
    print()
    print("7. Set the token when you run the poster:")
    print("   TELEGRAM_WIG_BOT_TOKEN=your_token_here python3 telegram_poster.py")
    print()
    print("Or add it to your .env file:")
    print('   echo \'export TELEGRAM_WIG_BOT_TOKEN="your_token_here"\' >> ~/.bashrc')
    print('   echo \'export TELEGRAM_WIG_CHANNEL_ID="@worthitgoods"\' >> ~/.bashrc')
    print()
    sys.exit(1)

# Test the token
import requests

resp = requests.get(f"https://api.telegram.org/bot{BOT_TOKEN}/getMe", timeout=10)
if resp.status_code == 200:
    bot_info = resp.json()
    print(f"✅ Bot connected: @{bot_info['result']['username']} ({bot_info['result']['first_name']})")
else:
    print(f"❌ Bot connection failed: {resp.text}")
    sys.exit(1)

# Test channel access
channel = os.environ.get("TELEGRAM_WIG_CHANNEL_ID", "@worthitgoods")
resp = requests.get(
    f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
    json={"chat_id": channel, "text": "🤖 WorthItGoods bot connected. Ready to post deals."},
    timeout=10,
)
if resp.status_code == 200:
    print(f"✅ Channel access verified: {channel}")
    print("   Check your channel for the test message.")
else:
    print(f"❌ Channel access failed: {resp.text}")
    print(f"   Make sure you've added the bot as admin to {channel}")
    sys.exit(1)