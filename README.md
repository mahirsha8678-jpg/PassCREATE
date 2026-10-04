# SURE X Password Bot — Render

## Files

- `bot.py` — Telegram bot
- `requirements.txt` — no third-party dependencies
- `render.yaml` — Render Background Worker configuration

## Deploy

1. Upload these files to a GitHub repository.
2. In Render, create a new Blueprint from the repository, or create a Background Worker.
3. If using `render.yaml`, Render will create the worker from the file.
4. Set these environment variables:
   - `BOT_TOKEN` = your current Telegram BotFather token
   - `OWNER_CHAT_ID` = your Telegram owner chat ID
5. Deploy.

## Important

Do not commit a real Telegram bot token to GitHub.
If a bot token was previously exposed publicly, regenerate it in BotFather and use the new token as `BOT_TOKEN`.

This bot uses Telegram long polling (`getUpdates`), so it is configured as a Render Background Worker rather than a Web Service.
