import re

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import (
    CallbackQuery,
    Message,
    ReplyKeyboardRemove,
)

from bot.keyboards.registration import (
    get_confirmation_keyboard,
    get_edit_keyboard,
    get_phone_keyboard,
)
from bot.states.registration import (
    RegistrationEditStates,
    RegistrationStates,
)


router = Router()


def normalize_name(name: str) -> str:
    """Clean and format a student's name."""

    name = name.strip()
    name = re.sub(r"\s+", " ", name)

    return name


def normalize_group(group: str) -> str:
    """Normalize a student group into a consistent format."""

    group = group.strip().upper()
    group = re.sub(r"\s+", "", group)
    group = group.replace("_", "-")

    return group


def normalize_student_id(student_id: str) -> str:
    """Normalize a student ID into a consistent format."""

    student_id = student_id.strip().upper()
    student_id = re.sub(r"\s+", "", student_id)

    return student_id


async def show_confirmation(
    message: Message,
    state: FSMContext,
) -> None:
    """Display the current registration information."""

    data = await state.get_data()

    telegram_username = data.get("telegram_username")

    username_display = (
        f"@{telegram_username}"
        if telegram_username
        else "Not set"
    )

    await message.answer(
        "Please check your information:\n\n"
        f"👤 {data['first_name']} {data['last_name']}\n\n"
        f"🎓 {data['group']}\n\n"
        f"🆔 {data['student_id']}\n\n"
        f"📱 {data['phone']}\n\n"
        f"💬 {username_display}\n\n"
        "Is everything correct?",
        reply_markup=get_confirmation_keyboard(),
    )


# ============================================================
# NORMAL REGISTRATION
# ============================================================


@router.message(RegistrationStates.first_name)
async def process_first_name(
    message: Message,
    state: FSMContext,
) -> None:
    """Save the student's first name."""

    first_name = normalize_name(message.text or "")

    if not first_name:
        await message.answer("Please enter your first name.")
        return

    await state.update_data(first_name=first_name)
    await state.set_state(RegistrationStates.last_name)

    await message.answer("What's your last name?")


@router.message(RegistrationStates.last_name)
async def process_last_name(
    message: Message,
    state: FSMContext,
) -> None:
    """Save the student's last name."""

    last_name = normalize_name(message.text or "")

    if not last_name:
        await message.answer("Please enter your last name.")
        return

    await state.update_data(last_name=last_name)
    await state.set_state(RegistrationStates.group)

    await message.answer(
        "🎓 What's your group?\n\n"
        "For example:\n"
        "• IT1-26\n"
        "• CIE1-26\n"
        "• ME-23\n\n"
        "You can type it normally — we'll format it automatically."
    )


@router.message(RegistrationStates.group)
async def process_group(
    message: Message,
    state: FSMContext,
) -> None:
    """Save the student's group."""

    group = normalize_group(message.text or "")

    if not group:
        await message.answer(
            "Please enter your group.\n\n"
            "Example: IT1-26"
        )
        return

    await state.update_data(group=group)
    await state.set_state(RegistrationStates.student_id)

    await message.answer(
        f"🎓 Group: {group}\n\n"
        "What's your student ID?"
    )


@router.message(RegistrationStates.student_id)
async def process_student_id(
    message: Message,
    state: FSMContext,
) -> None:
    """Save the student's student ID."""

    student_id = normalize_student_id(message.text or "")

    if not student_id:
        await message.answer(
            "Please enter your student ID.\n\n"
            "Example: U18042"
        )
        return

    await state.update_data(student_id=student_id)
    await state.set_state(RegistrationStates.phone)

    await message.answer(
        f"🆔 Student ID: {student_id}\n\n"
        "📱 Please share your phone number using the button below.",
        reply_markup=get_phone_keyboard(),
    )


@router.message(RegistrationStates.phone)
async def process_phone(
    message: Message,
    state: FSMContext,
) -> None:
    """Save the student's phone and Telegram information."""

    contact = message.contact

    if contact is None:
        await message.answer(
            "Please use the 📱 Share phone number button "
            "to share your phone number."
        )
        return

    if contact.user_id != message.from_user.id:
        await message.answer(
            "Please share your own phone number using the button."
        )
        return

    await state.update_data(
        phone=contact.phone_number,
        telegram_id=message.from_user.id,
        telegram_username=message.from_user.username,
    )

    await state.set_state(RegistrationStates.confirmation)

    await message.answer(
        "✅ Phone number received.",
        reply_markup=ReplyKeyboardRemove(),
    )

    await show_confirmation(message, state)


# ============================================================
# CONFIRMATION
# ============================================================


@router.callback_query(
    RegistrationStates.confirmation,
    F.data == "registration:confirm",
)
async def confirm_registration(
    callback: CallbackQuery,
    state: FSMContext,
) -> None:
    """Handle confirmation of the student's registration."""

    await callback.answer()

    await callback.message.edit_reply_markup(reply_markup=None)

    await callback.message.answer(
        "✅ Your information has been confirmed.\n\n"
        "Your student profile is ready to be created."
    )


@router.callback_query(
    RegistrationStates.confirmation,
    F.data == "registration:edit",
)
async def edit_registration(
    callback: CallbackQuery,
    state: FSMContext,
) -> None:
    """Show the fields available for editing."""

    await callback.answer()

    await callback.message.edit_reply_markup(reply_markup=None)

    await callback.message.answer(
        "✏️ What would you like to edit?",
        reply_markup=get_edit_keyboard(),
    )


# ============================================================
# EDIT SELECTION
# ============================================================


@router.callback_query(
    RegistrationStates.confirmation,
    F.data == "registration:edit_first_name",
)
async def edit_first_name(
    callback: CallbackQuery,
    state: FSMContext,
) -> None:
    """Start editing the student's first name."""

    await callback.answer()
    await callback.message.edit_reply_markup(reply_markup=None)

    await state.set_state(RegistrationEditStates.first_name)

    await callback.message.answer(
        "👤 Enter your new first name:"
    )


@router.callback_query(
    RegistrationStates.confirmation,
    F.data == "registration:edit_last_name",
)
async def edit_last_name(
    callback: CallbackQuery,
    state: FSMContext,
) -> None:
    """Start editing the student's last name."""

    await callback.answer()
    await callback.message.edit_reply_markup(reply_markup=None)

    await state.set_state(RegistrationEditStates.last_name)

    await callback.message.answer(
        "👤 Enter your new last name:"
    )


@router.callback_query(
    RegistrationStates.confirmation,
    F.data == "registration:edit_group",
)
async def edit_group(
    callback: CallbackQuery,
    state: FSMContext,
) -> None:
    """Start editing the student's group."""

    await callback.answer()
    await callback.message.edit_reply_markup(reply_markup=None)

    await state.set_state(RegistrationEditStates.group)

    await callback.message.answer(
        "🎓 Enter your new group:\n\n"
        "For example:\n"
        "• IT1-26\n"
        "• CIE1-26\n"
        "• ME-23"
    )


@router.callback_query(
    RegistrationStates.confirmation,
    F.data == "registration:edit_student_id",
)
async def edit_student_id(
    callback: CallbackQuery,
    state: FSMContext,
) -> None:
    """Start editing the student's student ID."""

    await callback.answer()
    await callback.message.edit_reply_markup(reply_markup=None)

    await state.set_state(RegistrationEditStates.student_id)

    await callback.message.answer(
        "🆔 Enter your new student ID:"
)


# ============================================================
# EDIT PROCESSING
# ============================================================


@router.message(RegistrationEditStates.first_name)
async def process_edit_first_name(
    message: Message,
    state: FSMContext,
) -> None:
    """Update the student's first name and return to confirmation."""

    first_name = normalize_name(message.text or "")

    if not first_name:
        await message.answer("Please enter a valid first name.")
        return

    await state.update_data(first_name=first_name)

    await state.set_state(RegistrationStates.confirmation)

    await show_confirmation(message, state)


@router.message(RegistrationEditStates.last_name)
async def process_edit_last_name(
    message: Message,
    state: FSMContext,
) -> None:
    """Update the student's last name and return to confirmation."""

    last_name = normalize_name(message.text or "")

    if not last_name:
        await message.answer("Please enter a valid last name.")
        return

    await state.update_data(last_name=last_name)

    await state.set_state(RegistrationStates.confirmation)

    await show_confirmation(message, state)


@router.message(RegistrationEditStates.group)
async def process_edit_group(
    message: Message,
    state: FSMContext,
) -> None:
    """Update the student's group and return to confirmation."""

    group = normalize_group(message.text or "")

    if not group:
        await message.answer(
            "Please enter a valid group.\n\n"
            "Example: IT1-26"
        )
        return

    await state.update_data(group=group)

    await state.set_state(RegistrationStates.confirmation)

    await show_confirmation(message, state)


@router.message(RegistrationEditStates.student_id)
async def process_edit_student_id(
    message: Message,
    state: FSMContext,
) -> None:
    """Update the student's student ID and return to confirmation."""

    student_id = normalize_student_id(message.text or "")

    if not student_id:
        await message.answer(
            "Please enter a valid student ID.\n\n"
            "Example: U18042"
        )
        return

    await state.update_data(student_id=student_id)

    await state.set_state(RegistrationStates.confirmation)

    await show_confirmation(message, state)