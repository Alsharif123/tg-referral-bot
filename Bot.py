import os
import logging
from collections import defaultdict
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

logging.basicConfig(level=logging.INFO)

TOKEN = os.getenv("BOT_TOKEN")  # from Railway variables
CHANNEL = os.getenv("CHANNEL_USERNAME")  # e.g. @YourChannelName
REF_TARGET = int(os.getenv("REF_TARGET", "3"))
REWARD_TEXT = os.getenv("REWARD_TEXT", "🎁 Congrats! Here’s your reward contact @Albusayli0.")

# In-memory store (resets if app restarts)
referrals = defaultdict(lambda: {"referred": set(), "rewarded": False})

HELP_TEXT = (
    "🎯 Invite friends to our channel @https://t.me/melovedata to get rewards!\n"
    "1) Share your link\n"
    "2) They must join the channel and start the bot\n"
    f"3) Get {REF_TARGET} valid referrals → receive reward\n\n"
    "Commands:\n"
    "/link – your referral link\n"
    "/check – your referral count\n"
)

async def is_member(context: ContextTypes.DEFAULT_TYPE, user_id: int) -> bool:
    try:
        m = await context.bot.get_chat_member(CHANNEL, user_id)
        return m.status in ("member", "administrator", "creator")
    except Exception:
        return False

async def give_reward(context: ContextTypes.DEFAULT_TYPE, inviter_id: int):
    if not referrals[inviter_id]["rewarded"]:
        await context.bot.send_message(inviter_id, REWARD_TEXT)
        referrals[inviter_id]["rewarded"] = True

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_id = user.id
    args = context.args

    # If user came via referral link
    if args:
        try:
            inviter_id = int(args[0])
            if inviter_id != user_id:
                # Only credit if the new user joined the channel
                if await is_member(context, user_id):
                    if user_id not in referrals[inviter_id]["referred"]:
                        referrals[inviter_id]["referred"].add(user_id)
                        count = len(referrals[inviter_id]["referred"])
                        # Notify inviter about progress
                        try:
                            await context.bot.send_message(
                                inviter_id,
                                f"✅ New valid referral! Total: {count}/{REF_TARGET}"
                            )
                        except Exception:
                            pass
                        # Reward on threshold
                        if count >= REF_TARGET:
                            await give_reward(context, inviter_id)
                else:
                    # Ask the referred user to join
                    await update.message.reply_text(
                        f"👋 Hi {user.first_name}! Join {CHANNEL} first, then tap /start again.\n\n"
                        f"Channel: {CHANNEL}"
                    )
                    return
        except ValueError:
            pass

    link = f"https://t.me/{context.bot.username}?start={user_id}"
    await update.message.reply_text(
        f"Hey {user.first_name}!\n{HELP_TEXT}\nYour link:\n{link}"
    )

async def link_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    link = f"https://t.me/{context.bot.username}?start={user_id}"
    await update.message.reply_text(f"🔗 Your referral link:\n{link}")

async def check(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    count = len(referrals[user_id]["referred"])
    await update.message.reply_text(f"📊 You have {count}/{REF_TARGET} valid referrals.")

async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(HELP_TEXT)

def main():
    token = TOKEN
    if not token or not CHANNEL:
        raise RuntimeError("Missing BOT_TOKEN or CHANNEL_USERNAME environment variables.")
    app = ApplicationBuilder().token(token).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("link", link_cmd))
    app.add_handler(CommandHandler("check", check))
    app.add_handler(CommandHandler("help", help_cmd))
    app.run_polling()

if __name__ == "__main__":
    main()
