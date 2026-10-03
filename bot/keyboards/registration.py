from aiogram.types import KeyboardButton, ReplyKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder


def get_confirmation_keyboard():
    """Keyboard shown after the user enters all registration information."""

    builder = InlineKeyboardBuilder()

    builder.button(
        text="Confirm",
        callback_data="registration:confirm",
    )

    builder.button(
        text="Edit",
        callback_data="registration:edit",
    )

    builder.adjust(2)

    return builder.as_markup()


def get_edit_keyboard():
    """Keyboard for selecting which registration field to edit."""

    builder = InlineKeyboardBuilder()

    builder.button(
        text="First name",
        callback_data="registration:edit_first_name",
    )

    builder.button(
        text="Last name",
        callback_data="registration:edit_last_name",
    )

    builder.button(
        text="Group",
        callback_data="registration:edit_group",
    )

    builder.button(
        text="Student ID",
        callback_data="registration:edit_student_id",
    )

    builder.adjust(2)

    return builder.as_markup()


def get_phone_keyboard() -> ReplyKeyboardMarkup:
    """Keyboard used to request the user's phone number from Telegram."""

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


def get_student_id_retry_keyboard():
    """Keyboard shown when the entered student ID is already registered."""

    builder = InlineKeyboardBuilder()

    builder.button(
        text="Try again",
        callback_data="registration:retry_student_id",
    )

    return builder.as_markup()
