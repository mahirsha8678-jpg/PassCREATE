#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SURE X COMMUNITY — Telegram Password Bot
========================================
Password তৈরি/পরিবর্তন করার সিস্টেম। Bot টি password কে bot-এর
description-এ "SXPASS=...." লাইন হিসেবে সংরক্ষণ করে; HTML পেজ সেই
লাইন পড়ে автоматিকভাবে নতুন password নিয়ে নেয়।

চালানোর নিয়ম (সংক্ষেপে):  python3 bot.py
তারপর Telegram-এ bot-কে দিন:  /newpass  অথবা  /setpass ABC123

কোনো external library লাগবে না (শুধু Python standard library)।
"""
import json
import random
import re
import time
import urllib.parse
import urllib.request

BOT_TOKEN = "8828401523:AAG_faIFEb9Y5ADYyx2w6m_LrIkTbM6lsPM"
OWNER_CHAT_ID = 8244733612          # শুধুমাত্র এই chat ID কমান্ড দিতে পারবে
API = "https://api.telegram.org/bot" + BOT_TOKEN
PASS_RE = re.compile(r"^[A-Za-z0-9!@#%*_.\-]{3,24}$")

MENU = (
    "🔐 SURE X PASSWORD BOT\n"
    "------------------------\n"
    "/newpass  -> নতুন random password তৈরি\n"
    "/newpass 8 -> ৮ ঘরের random password\n"
    "/setpass ABC123 -> নিজের পছন্দমতো password\n"
    "/current  -> বর্তমান password দেখুন\n"
    "/help     -> এই মেনু"
)


def api(method, **params):
    data = urllib.parse.urlencode(params).encode("utf-8")
    req = urllib.request.Request(API + "/" + method, data=data)
    with urllib.request.urlopen(req, timeout=40) as r:
        return json.loads(r.read().decode("utf-8"))


def send(chat_id, text):
    try:
        api("sendMessage", chat_id=chat_id, text=text, disable_web_page_preview=True)
    except Exception as e:
        print("send error:", e)


def get_description():
    try:
        return (api("getMyDescription")["result"].get("description") or "")
    except Exception:
        return ""


def current_password():
    m = re.search(r"SXPASS=(\S+)", get_description())
    return m.group(1) if m else None


def publish_password(passw):
    """Description-এর বাকি টেক্সট অক্ষত রেখে শুধু SXPASS লাইন আপডেট করে।"""
    lines = [ln for ln in get_description().split("\n") if not ln.startswith("SXPASS=")]
    lines.append("SXPASS=" + passw)
    desc = "\n".join(lines)
    if len(desc) > 512:                      # Telegram limit
        base = "\n".join(ln for ln in lines[:-1])
        desc = (base[:512 - len(lines[-1]) - 1] + "\n" + lines[-1])
    api("setMyDescription", description=desc)


def gen_password(n=6):
    alphabet = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
    return "".join(random.choice(alphabet) for _ in range(int(n)))


def handle(text, chat_id):
    text = (text or "").strip()
    if text.startswith("/start") or text.startswith("/help"):
        send(chat_id, MENU)
        return
    if text.startswith("/newpass"):
        parts = text.split()
        n = 6
        if len(parts) > 1 and parts[1].isdigit():
            n = max(4, min(16, int(parts[1])))
        p = gen_password(n)
        publish_password(p)
        send(chat_id, "✅ নতুন password তৈরি হয়েছে:\n\n " + p +
             "\n\nHTML পেজ ~২০ সেকেন্ডের মধ্যে নিজে থেকেই নিয়ে নেবে (নাহলে রিফ্রেশ দিন)।")
        return
    if text.startswith("/setpass"):
        parts = text.split(None, 1)
        if len(parts) < 2 or not PASS_RE.match(parts[1].strip()):
            send(chat_id, "❌ সঠিক ফরম্যাট নয়। উদাহরণ: /setpass ABC123\n"
                          "(৩-২৪ অক্ষর: A-Z a-z 0-9 ! @ # % * _ . -)")
            return
        p = parts[1].strip()
        publish_password(p)
        send(chat_id, "✅ password সেট হয়েছে: 🔑 " + p)
        return
    if text.startswith("/current"):
        p = current_password()
        send(chat_id, ("🔑 বর্তমান password: " + p) if p else "❌ এখনো কোনো password সেট করা হয়নি।")
        return
    send(chat_id, MENU)


def main():
    me = api("getMe")["result"]
    print("Bot running:", me["username"], "| owner chat:", OWNER_CHAT_ID)
    offset = None
    while True:
        try:
            params = {"timeout": 30}
            if offset is not None:
                params["offset"] = offset
            res = api("getUpdates", **params)
            for up in res.get("result", []):
                offset = up["update_id"] + 1
                msg = up.get("message") or up.get("edited_message")
                if not msg or "text" not in msg:
                    continue
                chat_id = msg["chat"]["id"]
                if chat_id != OWNER_CHAT_ID:
                    send(chat_id, " আপনি authorized নন।\nআপনার chat id: " + str(chat_id))
                    continue
                handle(msg["text"], chat_id)
        except Exception as e:
            print("loop error:", e)
            time.sleep(3)


if __name__ == "__main__":
    main()
