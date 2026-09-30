from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
)


def get_phone_keyboard() -> ReplyKeyboardMarkup:
    """Create the keyboard used to request the student's phone number."""

    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(
                    text="📱 Share phone number",
                    request_contact=True,
                )
            ]
        ],
        resize_keyboard=True,
        one_time_keyboard=True,
    )


def get_confirmation_keyboard() -> InlineKeyboardMarkup:
    """Create the registration confirmation keyboard."""

    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✅ Confirm",
                    callback_data="registration:confirm",
                ),
                InlineKeyboardButton(
                    text="✏️ Edit",
                    callback_data="registration:edit",
                ),
            ]
        ]
    )


def get_edit_keyboard() -> InlineKeyboardMarkup:
    """Create the keyboard used to select a registration field to edit."""

    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="👤 First name",
                    callback_data="registration:edit_first_name",
                ),
                InlineKeyboardButton(
                    text="👤 Last name",
                    callback_data="registration:edit_last_name",
                ),
            ],
            [
                InlineKeyboardButton(
                    text="🎓 Group",
                    callback_data="registration:edit_group",
                ),
                InlineKeyboardButton(
                    text="🆔 Student ID",
                    callback_data="registration:edit_student_id",
                ),
            ],
        ]
    )