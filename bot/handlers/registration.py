import re

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import (
    CallbackQuery,
    Message,
    ReplyKeyboardRemove,
)

from bot.keyboards.main_menu import get_main_menu_keyboard
from bot.keyboards.registration import (
    get_confirmation_keyboard,
    get_edit_keyboard,
    get_phone_keyboard,
    get_student_id_retry_keyboard,
)
from bot.states.registration import (
    RegistrationEditStates,
    RegistrationStates,
)
from services.users import (
    create_user,
    get_user_by_student_id,
    get_user_by_telegram_id,
)


router = Router()


# ============================================================
# NORMALIZATION
# ============================================================


def normalize_name(name: str) -> str:
    """Normalize a student's name."""

    name = name.strip()
    name = re.sub(r"\s+", " ", name)

    return name


def normalize_group(group: str) -> str:
    """Normalize a student's group."""

    group = group.strip().upper()
    group = re.sub(r"\s+", "", group)
    group = group.replace("_", "-")

    return group


def normalize_student_id(student_id: str) -> str:
    """Normalize a student's ID."""

    student_id = student_id.strip().upper()
    student_id = re.sub(r"\s+", "", student_id)

    return student_id


# ============================================================
# CONFIRMATION
# ============================================================


async def show_confirmation(
    message: Message,
    state: FSMContext,
) -> None:
    """Show the information collected during registration."""

    data = await state.get_data()

    telegram_username = data.get(
        "telegram_username"
    )

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
# FIRST NAME
# ============================================================


@router.message(RegistrationStates.first_name)
async def process_first_name(
    message: Message,
    state: FSMContext,
) -> None:
    """Process the student's first name."""

    first_name = normalize_name(
        message.text or ""
    )

    if not first_name:
        await message.answer(
            "Please enter your first name."
        )
        return

    await state.update_data(
        first_name=first_name
    )

    await state.set_state(
        RegistrationStates.last_name
    )

    await message.answer(
        "What's your last name?"
    )


# ============================================================
# LAST NAME
# ============================================================


@router.message(RegistrationStates.last_name)
async def process_last_name(
    message: Message,
    state: FSMContext,
) -> None:
    """Process the student's last name."""

    last_name = normalize_name(
        message.text or ""
    )

    if not last_name:
        await message.answer(
            "Please enter your last name."
        )
        return

    await state.update_data(
        last_name=last_name
    )

    await state.set_state(
        RegistrationStates.group
    )

    await message.answer(
        "🎓 What's your group?\n\n"
        "For example:\n"
        "• IT1-26\n"
        "• CIE1-26\n"
        "• ME-23\n\n"
        "You can type it normally — "
        "we'll format it automatically."
    )


# ============================================================
# GROUP
# ============================================================


@router.message(RegistrationStates.group)
async def process_group(
    message: Message,
    state: FSMContext,
) -> None:
    """Process the student's group."""

    group = normalize_group(
        message.text or ""
    )

    if not group:
        await message.answer(
            "Please enter your group.\n\n"
            "Example: IT1-26"
        )
        return

    await state.update_data(
        group=group
    )

    await state.set_state(
        RegistrationStates.student_id
    )

    await message.answer(
        f"🎓 Group: {group}\n\n"
        "What's your student ID?"
    )


# ============================================================
# STUDENT ID
# ============================================================


@router.message(RegistrationStates.student_id)
async def process_student_id(
    message: Message,
    state: FSMContext,
) -> None:
    """Process and validate the student's ID."""

    student_id = normalize_student_id(
        message.text or ""
    )

    if not student_id:
        await message.answer(
            "Please enter your student ID.\n\n"
            "Example: U18042"
        )
        return

    existing_user = await get_user_by_student_id(
        student_id
    )

    if existing_user:
        await message.answer(
            "❌ This student ID is already registered.\n\n"
            "Please check your student ID and try again.",
            reply_markup=get_student_id_retry_keyboard(),
        )
        return

    await state.update_data(
        student_id=student_id
    )

    await state.set_state(
        RegistrationStates.phone
    )

    await message.answer(
        f"🆔 Student ID: {student_id}\n\n"
        "📱 Please share your phone number "
        "using the button below.",
        reply_markup=get_phone_keyboard(),
    )


# ============================================================
# STUDENT ID RETRY
# ============================================================


@router.callback_query(
    RegistrationStates.student_id,
    F.data == "registration:retry_student_id",
)
async def retry_student_id(
    callback: CallbackQuery,
    state: FSMContext,
) -> None:
    """Allow the user to enter another Student ID."""

    await callback.answer()

    await callback.message.edit_reply_markup(
        reply_markup=None
    )

    await state.set_state(
        RegistrationStates.student_id
    )

    await callback.message.answer(
        "🆔 Please enter your student ID again.\n\n"
        "Example: U18042"
    )


# ============================================================
# PHONE
# ============================================================


@router.message(RegistrationStates.phone)
async def process_phone(
    message: Message,
    state: FSMContext,
) -> None:
    """Process the student's phone number."""

    contact = message.contact

    if contact is None:
        await message.answer(
            "Please use the 📱 Share phone number "
            "button to share your phone number."
        )
        return

    if contact.user_id != message.from_user.id:
        await message.answer(
            "Please share your own phone number "
            "using the button."
        )
        return

    await state.update_data(
        phone=contact.phone_number,
        telegram_id=message.from_user.id,
        telegram_username=message.from_user.username,
    )

    await state.set_state(
        RegistrationStates.confirmation
    )

    await message.answer(
        "✅ Phone number received.",
        reply_markup=ReplyKeyboardRemove(),
    )

    await show_confirmation(
        message,
        state,
    )


# ============================================================
# CONFIRM REGISTRATION
# ============================================================


@router.callback_query(
    RegistrationStates.confirmation,
    F.data == "registration:confirm",
)
async def confirm_registration(
    callback: CallbackQuery,
    state: FSMContext,
) -> None:
    """
    Confirm registration.

    An existing Telegram account is handled before attempting
    to create a new database record.
    """

    await callback.answer()

    data = await state.get_data()

    telegram_id = data.get(
        "telegram_id"
    )

    # --------------------------------------------------------
    # Safety check
    # --------------------------------------------------------

    if telegram_id is None:
        await callback.message.edit_reply_markup(
            reply_markup=None
        )

        await state.clear()

        await callback.message.answer(
            "❌ Your registration session has expired.\n\n"
            "Please use /start to begin again."
        )

        return

    # --------------------------------------------------------
    # Check whether this Telegram account is already registered.
    #
    # This is especially important when:
    # - the user is testing with an existing account
    # - the FSM still contains an old registration session
    # - /start was triggered after a previous registration
    # --------------------------------------------------------

    existing_user = await get_user_by_telegram_id(
        telegram_id
    )

    if existing_user:
        await callback.message.edit_reply_markup(
            reply_markup=None
        )

        await state.clear()

        await callback.message.answer(
            "👋 This Telegram account is already registered.\n\n"
            "You can continue using your existing "
            "TTPU Tennis profile.",
            reply_markup=get_main_menu_keyboard(),
        )

        return

    # --------------------------------------------------------
    # Account does not exist.
    #
    # Create the new user.
    # --------------------------------------------------------

    try:
        await create_user(
            telegram_id=telegram_id,
            telegram_username=data.get(
                "telegram_username"
            ),
            first_name=data["first_name"],
            last_name=data["last_name"],
            group_name=data["group"],
            student_id=data["student_id"],
            phone=data.get("phone"),
        )

    except ValueError as error:
        await callback.message.edit_reply_markup(
            reply_markup=None
        )

        await callback.message.answer(
            "❌ Registration could not be completed.\n\n"
            f"{error}"
        )

        return

    # --------------------------------------------------------
    # Registration successful.
    # --------------------------------------------------------

    await callback.message.edit_reply_markup(
        reply_markup=None
    )

    await state.clear()

    await callback.message.answer(
        "🎾 Registration complete!\n\n"
        "Your TTPU Tennis profile has been "
        "created successfully.\n\n"
        "🏆 Starting ranking points: 0",
        reply_markup=get_main_menu_keyboard(),
    )


# ============================================================
# EDIT REGISTRATION
# ============================================================


@router.callback_query(
    RegistrationStates.confirmation,
    F.data == "registration:edit",
)
async def edit_registration(
    callback: CallbackQuery,
    state: FSMContext,
) -> None:
    """Show registration fields that can be edited."""

    await callback.answer()

    await callback.message.edit_reply_markup(
        reply_markup=None
    )

    await callback.message.answer(
        "✏️ What would you like to edit?",
        reply_markup=get_edit_keyboard(),
    )


# ============================================================
# EDIT FIRST NAME
# ============================================================


@router.callback_query(
    RegistrationStates.confirmation,
    F.data == "registration:edit_first_name",
)
async def edit_first_name(
    callback: CallbackQuery,
    state: FSMContext,
) -> None:
    """Start editing the first name."""

    await callback.answer()

    await callback.message.edit_reply_markup(
        reply_markup=None
    )

    await state.set_state(
        RegistrationEditStates.first_name
    )

    await callback.message.answer(
        "👤 Enter your new first name:"
    )


# ============================================================
# EDIT LAST NAME
# ============================================================


@router.callback_query(
    RegistrationStates.confirmation,
    F.data == "registration:edit_last_name",
)
async def edit_last_name(
    callback: CallbackQuery,
    state: FSMContext,
) -> None:
    """Start editing the last name."""

    await callback.answer()

    await callback.message.edit_reply_markup(
        reply_markup=None
    )

    await state.set_state(
        RegistrationEditStates.last_name
    )

    await callback.message.answer(
        "👤 Enter your new last name:"
    )


# ============================================================
# EDIT GROUP
# ============================================================


@router.callback_query(
    RegistrationStates.confirmation,
    F.data == "registration:edit_group",
)
async def edit_group(
    callback: CallbackQuery,
    state: FSMContext,
) -> None:
    """Start editing the group."""

    await callback.answer()

    await callback.message.edit_reply_markup(
        reply_markup=None
    )

    await state.set_state(
        RegistrationEditStates.group
    )

    await callback.message.answer(
        "🎓 Enter your new group:\n\n"
        "For example:\n"
        "• IT1-26\n"
        "• CIE1-26\n"
        "• ME-23"
    )


# ============================================================
# EDIT STUDENT ID
# ============================================================


@router.callback_query(
    RegistrationStates.confirmation,
    F.data == "registration:edit_student_id",
)
async def edit_student_id(
    callback: CallbackQuery,
    state: FSMContext,
) -> None:
    """Start editing the Student ID."""

    await callback.answer()

    await callback.message.edit_reply_markup(
        reply_markup=None
    )

    await state.set_state(
        RegistrationEditStates.student_id
    )

    await callback.message.answer(
        "🆔 Enter your new student ID:"
    )


# ============================================================
# PROCESS EDITED FIRST NAME
# ============================================================


@router.message(RegistrationEditStates.first_name)
async def process_edit_first_name(
    message: Message,
    state: FSMContext,
) -> None:
    """Update the first name."""

    first_name = normalize_name(
        message.text or ""
    )

    if not first_name:
        await message.answer(
            "Please enter a valid first name."
        )
        return

    await state.update_data(
        first_name=first_name
    )

    await state.set_state(
        RegistrationStates.confirmation
    )

    await show_confirmation(
        message,
        state,
    )


# ============================================================
# PROCESS EDITED LAST NAME
# ============================================================


@router.message(RegistrationEditStates.last_name)
async def process_edit_last_name(
    message: Message,
    state: FSMContext,
) -> None:
    """Update the last name."""

    last_name = normalize_name(
        message.text or ""
    )

    if not last_name:
        await message.answer(
            "Please enter a valid last name."
        )
        return

    await state.update_data(
        last_name=last_name
    )

    await state.set_state(
        RegistrationStates.confirmation
    )

    await show_confirmation(
        message,
        state,
    )


# ============================================================
# PROCESS EDITED GROUP
# ============================================================


@router.message(RegistrationEditStates.group)
async def process_edit_group(
    message: Message,
    state: FSMContext,
) -> None:
    """Update the group."""

    group = normalize_group(
        message.text or ""
    )

    if not group:
        await message.answer(
            "Please enter a valid group.\n\n"
            "Example: IT1-26"
        )
        return

    await state.update_data(
        group=group
    )

    await state.set_state(
        RegistrationStates.confirmation
    )

    await show_confirmation(
        message,
        state,
    )


# ============================================================
# PROCESS EDITED STUDENT ID
# ============================================================


@router.message(RegistrationEditStates.student_id)
async def process_edit_student_id(
    message: Message,
    state: FSMContext,
) -> None:
    """Validate and update the Student ID."""

    student_id = normalize_student_id(
        message.text or ""
    )

    if not student_id:
        await message.answer(
            "Please enter a valid student ID.\n\n"
            "Example: U18042"
        )
        return

    existing_user = await get_user_by_student_id(
        student_id
    )

    if existing_user:
        await message.answer(
            "❌ This student ID is already registered.\n\n"
            "Please enter a different student ID."
        )
        return

    await state.update_data(
        student_id=student_id
    )

    await state.set_state(
        RegistrationStates.confirmation
    )

    await show_confirmation(
        message,
        state,
    )