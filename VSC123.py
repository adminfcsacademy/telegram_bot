from typing import Final, Dict
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.enums import ParseMode
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
import re
import requests

# Bot token and username
TOKEN: Final = '7412731492:AAG2gzMheSCh7n72WmSljZeJV3KR3L74dvc'
BOT_USERNAME: Final = 'FCSacademy_bot'

# amoCRM credentials
AMO_SUBDOMAIN: Final = 'FCSAcademy'  # Your subdomain
AMO_API_KEY: Final = 'YOUR_AMOCRM_API_KEY'  # Replace with your amoCRM API key
AMO_API_URL: Final = f'https://{AMO_SUBDOMAIN}.amocrm.com/api/v4/'

# Initialize bot and dispatcher with in-memory storage
bot = Bot(token=TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

# FSM states for registration process
class RegistrationForm(StatesGroup):
    name = State()
    phone = State()
    course = State()
    english_proficiency = State()
    lesson_type = State()
    confirmation = State()

# Store user data temporarily
user_data: Dict[int, dict] = {}

# Available courses
COURSES = [
    "Management Accounting (F2)",
    "Financial Accounting (F3)",
    "Financial Reporting (F7)",
    "Audit and Assurance (F8)",
    "Financial Management (F9)"
]

# English proficiency options
ENGLISH_LEVELS = ["Beginner", "Intermediate", "Advanced"]

# Lesson type options
LESSON_TYPES = ["Face-to-face (offline)", "Pre-recorded (hybrid)"]

# Inline keyboard for start options
start_keyboard = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="Register", callback_data="start_registration")],
    [InlineKeyboardButton(text="View Schedule", callback_data="view_schedule")]
])

# Back button keyboard
back_keyboard = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="Back", callback_data="back_to_menu")]
])

# Function to sync data to amoCRM
def sync_to_amocrm(data: dict):
    headers = {
        'Authorization': f'Bearer {AMO_API_KEY}',
        'Content-Type': 'application/json'
    }
    
    # Prepare contact data (replace field IDs with actual IDs from your amoCRM setup)
    contact_data = [{
        "name": data["name"],
        "custom_fields_values": [
            {"field_id": 123456, "values": [{"value": data["phone"]}]},  # Replace with your phone field ID
            {"field_id": 123457, "values": [{"value": data["course"]}]},  # Replace with your course field ID
            {"field_id": 123458, "values": [{"value": data["english_proficiency"]}]},  # Replace with English field ID
            {"field_id": 123459, "values": [{"value": data["lesson_type"]}]},  # Replace with lesson type field ID
        ]
    }]

    try:
        # Send request to amoCRM API
        response = requests.post(
            f'{AMO_API_URL}contacts',
            headers=headers,
            json=contact_data
        )
        if response.status_code == 200:
            print(f"Successfully synced {data['name']} to amoCRM")
        else:
            print(f"Failed to sync to amoCRM: {response.status_code} - {response.text}")
    except requests.RequestException as e:
        print(f"Error syncing to amoCRM: {e}")

# Start command
@dp.message(Command("start"))
async def start_command(message: Message):
    await message.reply(
        "🎓 **Welcome to the Course Registration Bot!**\n"
        "We’re here to help you register for our courses or get more info.\n"
        "Choose an option below:",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=start_keyboard
    )

# Back to menu callback
@dp.callback_query(lambda c: c.data == "back_to_menu")
async def back_to_menu(callback_query: types.CallbackQuery, state: FSMContext):
    await callback_query.answer()
    await callback_query.message.reply(
        "🔙 **Back to main menu:**\nChoose an option below:",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=start_keyboard
    )
    await state.clear()  # Reset FSM state

# Start registration callback
@dp.callback_query(lambda c: c.data == "start_registration")
async def process_start_registration(callback_query: types.CallbackQuery, state: FSMContext):
    user_id = callback_query.from_user.id
    user_data[user_id] = {}
    await callback_query.answer()
    await callback_query.message.reply(
        "📝 **Let’s begin!** Please enter your full name:",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=back_keyboard
    )
    await state.set_state(RegistrationForm.name)

# Handle name input
@dp.message(RegistrationForm.name)
async def process_name(message: Message, state: FSMContext):
    user_id = message.from_user.id
    name = message.text.strip()
    if len(name) < 2 or not name.replace(" ", "").isalpha():
        await message.reply(
            "⚠️ Please enter a valid name (letters only, min 2 characters).",
            reply_markup=back_keyboard
        )
        return
    user_data[user_id]["name"] = name
    await message.reply(
        "📞 Thanks! Now, please enter your phone number (e.g., +1234567890):",
        reply_markup=back_keyboard
    )
    await state.set_state(RegistrationForm.phone)

# Handle phone input
@dp.message(RegistrationForm.phone)
async def process_phone(message: Message, state: FSMContext):
    user_id = message.from_user.id
    phone = message.text.strip()
    if not re.match(r"^\+?\d{9,15}$", phone):
        await message.reply(
            "⚠️ Please enter a valid phone number (e.g., +1234567890).",
            reply_markup=back_keyboard
        )
        return
    user_data[user_id]["phone"] = phone
    await message.reply(
        "📚 Which course would you like to register for?\n" +
        "\n".join(f"{i+1}. {course}" for i, course in enumerate(COURSES)),
        reply_markup=back_keyboard
    )
    await state.set_state(RegistrationForm.course)

# Handle course selection
@dp.message(RegistrationForm.course)
async def process_course(message: Message, state: FSMContext):
    user_id = message.from_user.id
    try:
        choice = int(message.text.strip()) - 1
        if 0 <= choice < len(COURSES):
            user_data[user_id]["course"] = COURSES[choice]
            await message.reply(
                "🗣️ What’s your English proficiency level?\n" +
                "\n".join(f"{i+1}. {level}" for i, level in enumerate(ENGLISH_LEVELS)),
                reply_markup=back_keyboard
            )
            await state.set_state(RegistrationForm.english_proficiency)
        else:
            await message.reply(
                "⚠️ Please enter a valid number from the list.",
                reply_markup=back_keyboard
            )
    except ValueError:
        await message.reply(
            "⚠️ Please enter a number corresponding to a course.",
            reply_markup=back_keyboard
        )

# Handle English proficiency
@dp.message(RegistrationForm.english_proficiency)
async def process_english_proficiency(message: Message, state: FSMContext):
    user_id = message.from_user.id
    try:
        choice = int(message.text.strip()) - 1
        if 0 <= choice < len(ENGLISH_LEVELS):
            user_data[user_id]["english_proficiency"] = ENGLISH_LEVELS[choice]
            await message.reply(
                "🎥 What type of lesson do you prefer?\n" +
                "\n".join(f"{i+1}. {type_}" for i, type_ in enumerate(LESSON_TYPES)),
                reply_markup=back_keyboard
            )
            await state.set_state(RegistrationForm.lesson_type)
        else:
            await message.reply(
                "⚠️ Please enter a valid number from the list.",
                reply_markup=back_keyboard
            )
    except ValueError:
        await message.reply(
            "⚠️ Please enter a number corresponding to a level.",
            reply_markup=back_keyboard
        )

# Handle lesson type
@dp.message(RegistrationForm.lesson_type)
async def process_lesson_type(message: Message, state: FSMContext):
    user_id = message.from_user.id
    try:
        choice = int(message.text.strip()) - 1
        if 0 <= choice < len(LESSON_TYPES):
            user_data[user_id]["lesson_type"] = LESSON_TYPES[choice]
            await show_confirmation(message, state)
        else:
            await message.reply(
                "⚠️ Please enter a valid number from the list.",
                reply_markup=back_keyboard
            )
    except ValueError:
        await message.reply(
            "⚠️ Please enter a number corresponding to a lesson type.",
            reply_markup=back_keyboard
        )

# Show confirmation
async def show_confirmation(message: Message, state: FSMContext):
    user_id = message.from_user.id
    data = user_data[user_id]
    confirmation_text = (
        f"📋 **Please confirm your details:**\n"
        f"**Name**: {data['name']}\n"
        f"**Phone**: {data['phone']}\n"
        f"**Course**: {data['course']}\n"
        f"**English Proficiency**: {data['english_proficiency']}\n"
        f"**Lesson Type**: {data['lesson_type']}"
    )
    confirm_keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Confirm", callback_data="confirm"),
         InlineKeyboardButton(text="Edit", callback_data="edit")],
        [InlineKeyboardButton(text="Back", callback_data="back_to_menu")]
    ])
    await message.reply(confirmation_text, parse_mode=ParseMode.MARKDOWN, reply_markup=confirm_keyboard)
    await state.set_state(RegistrationForm.confirmation)

# Handle confirmation/edit
@dp.callback_query(lambda c: c.data in ["confirm", "edit"], RegistrationForm.confirmation)
async def process_confirmation(callback_query: types.CallbackQuery, state: FSMContext):
    user_id = callback_query.from_user.id
    data = user_data[user_id]
    await callback_query.answer()

    if callback_query.data == "confirm":
        # Sync data to amoCRM before confirming
        sync_to_amocrm(data)
        await callback_query.message.reply(
            f"✅ **Thank you, {data['name']}!** You’re registered for {data['course']}.\n"
            f"We’ll contact you soon!",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=back_keyboard
        )
        del user_data[user_id]
        await state.clear()
    elif callback_query.data == "edit":
        await callback_query.message.reply(
            "✏️ Let’s edit. Please enter your full name again:",
            reply_markup=back_keyboard
        )
        await state.set_state(RegistrationForm.name)

# Schedule command and callback
@dp.message(Command("schedule"))
async def schedule_command(message: types.Message):
    schedule_text = (
        "📅 **Course Schedule**\n"
        "Here are the available courses:\n\n"
        "1. **Financial Accounting (F3)**\n   - Time: Tue/Thu/Fri 7:00 PM - 8:00 PM\n   - Ends: June 1, 2025\n"
        "2. **Financial Reporting (F7)**\n   - Starts from 24th of March\n   - Ends: June 25, 2025\n"
    )
    await message.reply(schedule_text, parse_mode=ParseMode.MARKDOWN, reply_markup=back_keyboard)

@dp.callback_query(lambda c: c.data == "view_schedule")
async def schedule_callback(callback_query: types.CallbackQuery):
    schedule_text = (
        "📅 **Course Schedule**\n"
        "Here are the available courses:\n\n"
        "1. **Financial Accounting (F3)**\n   - Time: Tue/Thu/Fri 7:00 PM - 8:00 PM\n   - Ends: June 1, 2025\n"
        "2. **Financial Reporting (F7)**\n   - Starts from 24th of March\n   - Ends: June 25, 2025\n"
    )
    await callback_query.answer()
    await callback_query.message.reply(schedule_text, parse_mode=ParseMode.MARKDOWN, reply_markup=back_keyboard)

# Contact command and callback
@dp.message(Command("contact"))
async def contact_command(message: types.Message):
    print("Contact command triggered")  # Debug print
    contact_text = (
        "📞 **Contact Us**\n"
        "We’d love to hear from you! Reach out via:\n\n"
        "📱 **Phone**: +998 (90) 335-82-25\n"
        "🌐 **Website**: www.fcs-experts.uz/fcs-academy.com\n"
        "📍 **Location**: Uzbekistan, Tashkent, Niyozbek str, 30, 4th floor, room 415\n"
        "💬 **Telegram**: @FCSACADEMY_admin\n\n"
        "Feel free to ask questions or visit us!"
    )
    await message.reply(contact_text, parse_mode=ParseMode.MARKDOWN, reply_markup=back_keyboard)

@dp.callback_query(lambda c: c.data == "view_contact")
async def contact_callback(callback_query: types.CallbackQuery):
    print("Contact callback triggered")  # Debug print
    contact_text = (
        "📞 **Contact Us**\n"
        "We’d love to hear from you! Reach out via:\n\n"
        "📱 **Phone**: +998 (90) 335-82-25\n"
        "🌐 **Website**: www.fcs-experts.uz/fcs-academy.com\n"
        "📍 **Location**: Uzbekistan, Tashkent, Niyozbek str, 30, 4th floor, room 415\n"
        "💬 **Telegram**: @FCSACADEMY_admin\n\n"
        "Feel free to ask questions or visit us!"
    )
    await callback_query.answer()
    await callback_query.message.reply(contact_text, parse_mode=ParseMode.MARKDOWN, reply_markup=back_keyboard)

# Startup and shutdown
async def on_startup():
    # Delete any existing webhook to avoid conflicts
    await bot.delete_webhook(drop_pending_updates=True)
    print("Webhook deleted. Course Registration Bot is running...")

async def on_shutdown():
    print("Course Registration Bot is shutting down...")

# Main function to run the bot
async def main():
    # Register startup and shutdown hooks
    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)
    # Start polling
    await dp.start_polling(bot)

if __name__ == '__main__':
    print("Starting polling...")
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Bot stopped by user.")
    except Exception as e:
        print(f"Polling failed: {e}")