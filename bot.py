#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
SURE X COMMUNITY — Telegram Password Bot
Render-ready Background Worker.

Required environment variables:
    BOT_TOKEN
    OWNER_CHAT_ID

Run:
    python bot.py
"""

import json
import os
import random
import re
import time
import urllib.parse
import urllib.request


BOT_TOKEN = os.getenv("BOT_TOKEN")
OWNER_CHAT_ID_RAW = os.getenv("OWNER_CHAT_ID")

if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN environment variable is missing.")

if not OWNER_CHAT_ID_RAW:
    raise RuntimeError("OWNER_CHAT_ID environment variable is missing.")

try:
    OWNER_CHAT_ID = int(OWNER_CHAT_ID_RAW)
except ValueError as exc:
    raise RuntimeError("OWNER_CHAT_ID must be a valid integer.") from exc

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
    req = urllib.request.Request(
        API + "/" + method,
        data=data,
        headers={"User-Agent": "SURE-X-Password-Bot/1.0"},
    )
    with urllib.request.urlopen(req, timeout=40) as response:
        return json.loads(response.read().decode("utf-8"))


def send(chat_id, text):
    try:
        api(
            "sendMessage",
            chat_id=chat_id,
            text=text,
            disable_web_page_preview=True,
        )
    except Exception as exc:
        print("send error:", repr(exc), flush=True)


def get_description():
    try:
        result = api("getMyDescription")
        return result.get("result", {}).get("description") or ""
    except Exception as exc:
        print("description error:", repr(exc), flush=True)
        return ""


def current_password():
    match = re.search(r"SXPASS=(\S+)", get_description())
    return match.group(1) if match else None


def publish_password(password):
    old_description = get_description()

    lines = [
        line
        for line in old_description.split("\n")
        if not line.startswith("SXPASS=")
    ]
    lines.append("SXPASS=" + password)

    description = "\n".join(lines)

    if len(description) > 512:
        password_line = lines[-1]
        base = "\n".join(lines[:-1])
        available = 512 - len(password_line) - 1

        if available < 0:
            raise RuntimeError("Password is too long for Telegram description.")

        description = base[:available] + "\n" + password_line

    result = api("setMyDescription", description=description)

    if not result.get("ok"):
        raise RuntimeError("Telegram setMyDescription failed: " + str(result))


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

        try:
            password = gen_password(n)
            publish_password(password)
            send(
                chat_id,
                "✅ নতুন password তৈরি হয়েছে:\n\n"
                + password
                + "\n\n"
                "HTML পেজ ~২০ সেকেন্ডের মধ্যে নিজে থেকেই "
                "নিয়ে নেবে (নাহলে রিফ্রেশ দিন)।",
            )
        except Exception as exc:
            print("newpass error:", repr(exc), flush=True)
            send(chat_id, "❌ Password update করতে সমস্যা হয়েছে। Render logs দেখুন.")
        return

    if text.startswith("/setpass"):
        parts = text.split(None, 1)

        if len(parts) < 2 or not PASS_RE.match(parts[1].strip()):
            send(
                chat_id,
                "❌ সঠিক ফরম্যাট নয়। উদাহরণ:\n"
                "/setpass ABC123\n\n"
                "(৩-২৪ অক্ষর: A-Z a-z 0-9 ! @ # % * _ . -)",
            )
            return

        password = parts[1].strip()

        try:
            publish_password(password)
            send(chat_id, "✅ password সেট হয়েছে: 🔑 " + password)
        except Exception as exc:
            print("setpass error:", repr(exc), flush=True)
            send(chat_id, "❌ Password update করতে সমস্যা হয়েছে। Render logs দেখুন.")
        return

    if text.startswith("/current"):
        password = current_password()
        send(
            chat_id,
            ("🔑 বর্তমান password: " + password)
            if password
            else "❌ এখনো কোনো password সেট করা হয়নি.",
        )
        return

    send(chat_id, MENU)


def main():
    me = api("getMe")["result"]

    print(
        "Bot running:",
        me.get("username"),
        "| owner chat:",
        OWNER_CHAT_ID,
        flush=True,
    )

    offset = None

    while True:
        try:
            params = {"timeout": 30}

            if offset is not None:
                params["offset"] = offset

            result = api("getUpdates", **params)

            if not result.get("ok"):
                print("Telegram API error:", result, flush=True)
                time.sleep(5)
                continue

            for update in result.get("result", []):
                offset = update["update_id"] + 1

                message = (
                    update.get("message")
                    or update.get("edited_message")
                )

                if not message or "text" not in message:
                    continue

                chat_id = message["chat"]["id"]

                if chat_id != OWNER_CHAT_ID:
                    send(
                        chat_id,
                        "❌ আপনি authorized নন.\n"
                        "আপনার chat id: " + str(chat_id),
                    )
                    continue

                handle(message["text"], chat_id)

        except KeyboardInterrupt:
            print("Bot stopped.", flush=True)
            break
        except Exception as exc:
            print("loop error:", repr(exc), flush=True)
            time.sleep(5)


if __name__ == "__main__":
    main()
