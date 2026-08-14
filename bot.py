import random
import string
import time
import requests
import pyotp
import telebot
from telebot import types

TOKEN = "8974330521:AAE_niErKnWPdQWtrmzWltd8LQ5aleUtj-E"
ADMIN_CHANNEL_ID = "-1004399480886"

SUPABASE_URL = "https://xtkdjjryooketbgdreez.supabase.co"
SUPABASE_KEY = (
    "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Inh0"
    "a2RqanJ5b29rZXRiZ2RyZWV6InRlc2wiOiJhbm9uIiwiaWF0IjoxNzg2NjM1MDE5LCJleHAi"
    "OjIxMDIyMTEwMTl9.Oi3LMmZX1m02Z3XPje-iXhQsg3pYDi6Zn80Cpi436Lk"
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


def get_user(chat_id):
  url = f"{SUPABASE_URL}/rest/v1/users?chat_id=eq.{chat_id}&select=*"
  try:
    response = requests.get(url, headers=HEADERS, timeout=10)
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
        requests.post(insert_url, headers=HEADERS, json=new_user, timeout=10)
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
  except Exception as e:
    print(f"Database connection error: {e}")

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
  try:
    requests.patch(url, headers=HEADERS, json=update_data, timeout=10)
  except Exception as e:
    print(f"Database update error: {e}")


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


def generate_fb_info():
  first_names = ["DHEARYE", "SAMUEL", "DAVID", "JOHN", "MICHAEL"]
  last_names = ["SAAWAIYE", "SMITH", "JOHNSON", "BROWN", "WILLIAMS"]
  f_name = random.choice(first_names)
  l_name = random.choice(last_names)
  full_name = f"{f_name} {l_name}"
  password = "".join(
      random.choices(string.ascii_letters + string.digits + "!@#$%", k=10)
  )
  return full_name, password


def generate_ig_info():
  first_names = ["alex", "emma", "liam", "sophia", "noah"]
  last_names = ["smith", "jones", "brown", "miller", "davis"]
  f_name = random.choice(first_names)
  l_name = random.choice(last_names)
  full_name = f"{f_name.capitalize()} {l_name.capitalize()}"
  random_num = "".join(random.choices(string.digits, k=3))
  username = f"{f_name}_{l_name}{random_num}"
  password = "".join(
      random.choices(string.ascii_letters + string.digits + "!@#$%", k=10)
  )
  return full_name, username, password


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
      "🔥 Www Earn Bot — New Instagram Task\n\n"
      "🎯 A new Instagram earning task is now available!\n\n"
      "📲 Complete the task and earn your reward.\n\n"
      "💰 Mini App: $0.032 per approved account\n"
      "⏱️ Approval/verification time: approximately 1–1.5 hours\n\n"
      "🤖 Chat Bot: $0.025 per account\n"
      "⏱️ Submit/processing time: approximately 30–50 minutes\n\n"
      "⚡ Choose your preferred method and start working!\n\n"
      "👇 Open the Mini App or type /task"
  )

  bot.send_message(chat_id, "📌 Main Menu", reply_markup=get_main_keyboard())
  bot.send_message(chat_id, text)


# --- REPLY BUTTON HANDLERS ---
@bot.message_handler(func=lambda message: message.text == "💰 Balance")
def check_balance(message):
  chat_id = message.chat.id
  user = get_user(chat_id)
  text = (
      "💰 **Your Account Balance:**\n\n"
      f"🔹 Task Balance: **${user['task_balance']:.3f}**\n"
      f"🔸 Invite Balance: **${user['invite_balance']:.3f}**\n\n"
      f"📊 Total Balance: **${(user['task_balance'] + user['invite_balance']):.3f}**"
  )
  bot.send_message(chat_id, text, parse_mode="Markdown")


@bot.message_handler(func=lambda message: message.text == "📤 Withdraw")
def withdraw_money(message):
  chat_id = message.chat.id
  user = get_user(chat_id)
  total_balance = user["task_balance"] + user["invite_balance"]
  text = (
      "📤 **Withdrawal Menu**\n\n"
      f"Your Total Balance: **${total_balance:.3f}**\n\n"
      "⚠️ Minimum withdrawal limit is **$1.00**.\n"
      "Please accumulate enough balance to request a payout."
  )
  bot.send_message(chat_id, text, parse_mode="Markdown")


@bot.message_handler(func=lambda message: message.text == "👩‍👧‍👦 REFERRAL 👩‍👧‍👦")
def referral_menu(message):
  chat_id = message.chat.id
  user = get_user(chat_id)
  bot_info = bot.get_me()
  ref_link = f"https://t.me/{bot_info.username}?start=ref_{chat_id}"

  text = (
      "👩‍👧‍👦 **Referral Program**\n\n"
      "Invite your friends and earn **10% commission** from their task earnings!\n\n"
      f"👥 Total Referrals: **{user['referrals']}**\n"
      f"🎁 Invite Balance Earnings: **${user['invite_balance']:.3f}**\n\n"
      "🔗 **Your Referral Link:**\n"
      f"`{ref_link}`"
  )
  bot.send_message(chat_id, text, parse_mode="Markdown")


@bot.message_handler(commands=["task"])
def show_tasks_command(message):
  markup = types.InlineKeyboardMarkup()
  btn_fb = types.InlineKeyboardButton(
      "Fb Task ($0.055)", callback_data="task_fb"
  )
  btn_ig = types.InlineKeyboardButton(
      "Ig Task ($0.03)", callback_data="task_ig"
  )
  markup.add(btn_fb, btn_ig)
  bot.send_message(
      message.chat.id, "👉 Please select a category:", reply_markup=markup
  )


@bot.callback_query_handler(func=lambda call: call.data == "back_to_tasks")
def back_to_tasks(call):
  markup = types.InlineKeyboardMarkup()
  btn_fb = types.InlineKeyboardButton(
      "Fb Task ($0.055)", callback_data="task_fb"
  )
  btn_ig = types.InlineKeyboardButton(
      "Ig Task ($0.03)", callback_data="task_ig"
  )
  markup.add(btn_fb, btn_ig)
  bot.edit_message_text(
      "👉 Please select a category:",
      call.message.chat.id,
      call.message.message_id,
      reply_markup=markup,
  )


# --- FB TASK FLOW ---
@bot.callback_query_handler(func=lambda call: call.data == "task_fb")
def select_fb_task(call):
  markup = types.InlineKeyboardMarkup()
  btn_cookies = types.InlineKeyboardButton(
      "Cookies ($0.056)", callback_data="fb_cookies"
  )
  btn_back = types.InlineKeyboardButton("🔙 Back", callback_data="back_to_tasks")
  markup.add(btn_cookies, btn_back)

  bot.edit_message_text(
      "Select the fb task please select from below:",
      call.message.chat.id,
      call.message.message_id,
      reply_markup=markup,
  )


@bot.callback_query_handler(func=lambda call: call.data == "fb_cookies")
def start_fb_cookies_task(call):
  chat_id = call.message.chat.id
  full_name, password = generate_fb_info()

  user_data[chat_id] = {
      "task_type": "fb_cookies",
      "full_name": full_name,
      "password": password,
      "step": "waiting_for_fb_uid",
  }

  text = (
      "Task: 📱 Facebook Cookies\n\n"
      "Please create a new account using the details below:\n"
      f"First name & Last name: {full_name}\n"
      f"Password: {password}\n\n"
      "👉 Please enter the FB UID:"
  )
  bot.edit_message_text(text, chat_id, call.message.message_id)


@bot.message_handler(
    func=lambda message: message.chat.id in user_data
    and user_data[message.chat.id].get("step") == "waiting_for_fb_uid"
)
def handle_fb_uid(message):
  chat_id = message.chat.id
  fb_uid = message.text.strip()

  user_data[chat_id]["fb_uid"] = fb_uid
  user_data[chat_id]["step"] = "waiting_for_fb_cookies"

  bot.send_message(
      chat_id,
      "✅ Your UID has been saved successfully!\n\n👉 Now Paste your FB Cookies"
      " below:",
  )


@bot.message_handler(
    func=lambda message: message.chat.id in user_data
    and user_data[message.chat.id].get("step") == "waiting_for_fb_cookies"
)
def handle_fb_cookies(message):
  chat_id = message.chat.id
  fb_cookies = message.text.strip()
  data = user_data[chat_id]

  admin_markup = types.InlineKeyboardMarkup()
  btn_approve = types.InlineKeyboardButton(
      "✅ Approve", callback_data=f"approve_fb_{chat_id}"
  )
  btn_reject = types.InlineKeyboardButton(
      "❌ Reject", callback_data=f"reject_fb_{chat_id}"
  )
  admin_markup.add(btn_approve, btn_reject)

  admin_text = (
      "🚨 New Facebook Cookies Submission:\n\n"
      f"User ID: {chat_id}\n"
      f"Full Name: {data['full_name']}\n"
      f"Password: {data['password']}\n"
      f"FB UID: {data['fb_uid']}\n"
      f"Cookies: {fb_cookies}"
  )

  bot.send_message(ADMIN_CHANNEL_ID, admin_text, reply_markup=admin_markup)

  join_markup = types.InlineKeyboardMarkup()
  btn_join = types.InlineKeyboardButton(
      "JOIN CHANNEL", url="https://t.me/wwearnoffice"
  )
  join_markup.add(btn_join)

  success_text = (
      "✅ Task submitted successfully!\n\n"
      "⏱️ Please note: Account verification may take 1–2 hours."
  )
  bot.send_message(chat_id, success_text, reply_markup=join_markup)

  del user_data[chat_id]


# --- IG TASK FLOW ---
@bot.callback_query_handler(func=lambda call: call.data == "task_ig")
def select_ig_task(call):
  chat_id = call.message.chat.id
  markup = types.InlineKeyboardMarkup()
  btn_start = types.InlineKeyboardButton("Start", callback_data="ig_start")
  btn_cancel = types.InlineKeyboardButton("Cancel", callback_data="ig_cancel")
  markup.add(btn_start, btn_cancel)

  text = (
      "📱 Ig Task ($0.03)\n\n"
      "⏱️ Review Time: 30–50 Min\n\n"
      "Choose an option below to proceed:"
  )
  bot.edit_message_text(
      text, chat_id, call.message.message_id, reply_markup=markup
  )


@bot.callback_query_handler(func=lambda call: call.data == "ig_cancel")
def cancel_ig_task(call):
  chat_id = call.message.chat.id
  if chat_id in user_data:
    del user_data[chat_id]
  bot.edit_message_text(
      "❌ IG Task cancelled.", chat_id, call.message.message_id
  )


@bot.callback_query_handler(func=lambda call: call.data == "ig_start")
def start_ig_task_details(call):
  chat_id = call.message.chat.id
  full_name, username, password = generate_ig_info()

  user_data[chat_id] = {
      "task_type": "ig_2fa",
      "full_name": full_name,
      "username": username,
      "password": password,
      "step": "waiting_for_ig_2fa",
  }

  text = (
      "📱 IG Task Details:\n\n"
      f"First name: {full_name}\n"
      f"Username: {username}\n"
      f"Password: {password}\n\n"
      "👉 Please enter your 2fa key to get the code:"
  )
  bot.edit_message_text(text, chat_id, call.message.message_id)


@bot.message_handler(
    func=lambda message: message.chat.id in user_data
    and user_data[message.chat.id].get("step") == "waiting_for_ig_2fa"
)
def handle_ig_2fa_key(message):
  chat_id = message.chat.id
  secret_key = message.text.replace(" ", "").strip().upper()

  try:
    totp = pyotp.TOTP(secret_key)
    one_time_code = totp.now()

    user_data[chat_id]["2fa_key"] = secret_key
    user_data[chat_id]["one_time_code"] = one_time_code

    markup = types.InlineKeyboardMarkup()
    btn_confirm = types.InlineKeyboardButton(
        "✅ Confirm Registration", callback_data="ig_confirm"
    )
    btn_cancel = types.InlineKeyboardButton(
        "❌ Cancel", callback_data="ig_cancel"
    )
    markup.add(btn_confirm, btn_cancel)

    bot.send_message(
        chat_id, f"Your one time code is: <code>{one_time_code}</code>", parse_mode="HTML"
    )
    bot.send_message(
        chat_id,
        "👉 Press the button to confirm registration or cancel the task:",
        reply_markup=markup,
    )
  except Exception as e:
    bot.send_message(
        chat_id, "❌ Invalid 2FA Key! Please check the key and send it again correctly."
    )


@bot.callback_query_handler(func=lambda call: call.data == "ig_confirm")
def confirm_ig_registration(call):
  chat_id = call.message.chat.id
  if chat_id in user_data:
    data = user_data[chat_id]

    admin_markup = types.InlineKeyboardMarkup()
    btn_approve = types.InlineKeyboardButton(
        "✅ Approve", callback_data=f"approve_ig_{chat_id}"
    )
    btn_reject = types.InlineKeyboardButton(
        "❌ Reject", callback_data=f"reject_ig_{chat_id}"
    )
    admin_markup.add(btn_approve, btn_reject)

    admin_text = (
        "🚨 New Instagram Task Submission:\n\n"
        f"User ID: {chat_id}\n"
        f"Full Name: {data['full_name']}\n"
        f"Username: {data['username']}\n"
        f"Password: {data['password']}\n"
        f"2FA Key: {data.get('2fa_key', 'N/A')}\n"
        f"Generated Code: {data.get('one_time_code', 'N/A')}"
    )

    bot.send_message(ADMIN_CHANNEL_ID, admin_text, reply_markup=admin_markup)

    join_markup = types.InlineKeyboardMarkup()
    btn_join = types.InlineKeyboardButton(
        "JOIN CHANNEL", url="https://t.me/wwearnoffice"
    )
    join_markup.add(btn_join)

    success_text = (
        "✅ Task submitted successfully!\n\n"
        "⏱️ Please Account Verification may take 1-2 h"
    )
    bot.edit_message_text(
        success_text, chat_id, call.message.message_id, reply_markup=join_markup
    )

    del user_data[chat_id]


# --- ADMIN APPROVAL HANDLERS ---
@bot.callback_query_handler(
    func=lambda call: call.data.startswith("approve_fb_")
    or call.data.startswith("reject_fb_")
)
def handle_admin_fb_decision(call):
  data_parts = call.data.split("_")
  action = data_parts[0]
  target_user_id = int(data_parts[3])

  if action == "approve":
    task_reward = 0.056
    add_task_balance_with_commission(target_user_id, task_reward)
    try:
      bot.send_message(
          target_user_id,
          "🎉 Congratulations! Your Facebook task has been APPROVED ✅\n$0.056"
          " has been added to your Task Balance.",
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
      bot.send_message(
          target_user_id, "❌ Your Facebook task submission was REJECTED."
      )
    except:
      pass
    bot.edit_message_text(
        f"{call.message.text}\n\nStatus: REJECTED ❌",
        call.message.chat.id,
        call.message.message_id,
    )


@bot.callback_query_handler(
    func=lambda call: call.data.startswith("approve_ig_")
    or call.data.startswith("reject_ig_")
)
def handle_admin_ig_decision(call):
  data_parts = call.data.split("_")
  action = data_parts[0]
  target_user_id = int(data_parts[3])

  if action == "approve":
    task_reward = 0.03
    add_task_balance_with_commission(target_user_id, task_reward)
    try:
      bot.send_message(
          target_user_id,
          "🎉 Congratulations! Your Instagram task has been APPROVED ✅\n$0.03"
          " has been added to your Task Balance.",
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
      bot.send_message(
          target_user_id, "❌ Your Instagram task submission was REJECTED."
      )
    except:
      pass
    bot.edit_message_text(
        f"{call.message.text}\n\nStatus: REJECTED ❌",
        call.message.chat.id,
        call.message.message_id,
    )


if __name__ == "__main__":
  while True:
    try:
      print("Bot is running...")
      bot.infinity_polling(timeout=60, long_polling_timeout=60)
    except Exception as e:
      print(f"Error: {e}")
      time.sleep(5)
