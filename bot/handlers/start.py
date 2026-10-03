from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from bot.keyboards.main_menu import get_main_menu_keyboard
from bot.states.registration import RegistrationStates
from bot.ui.messages.profile import profile_message
from services.users import get_user_by_telegram_id
from services.ranking import get_player_rank


router = Router()


@router.message(CommandStart())
async def start_handler(
    message: Message,
    state: FSMContext,
) -> None:
    """
    Handle user login and registration.

    Existing users:
    - Clear any active state.
    - Show their profile.
    - Open the main menu.

    New users:
    - Clear any active state.
    - Start registration.
    """

    telegram_id = message.from_user.id

    user = await get_user_by_telegram_id(
        telegram_id
    )

    # ========================================================
    # EXISTING USER
    # ========================================================

    if user:
        await state.clear()

        rank, total_players = await get_player_rank(user.id)

        await message.answer(
            profile_message(user, rank, total_players),
            reply_markup=get_main_menu_keyboard(),
        )

        return

    # ========================================================
    # NEW USER
    # ========================================================

    await state.clear()

    await state.set_state(
        RegistrationStates.first_name
    )

    await message.answer(
        "Welcome to TTPU Tennis.\n\n"
        "To use the tennis system, you need "
        "to create your student profile.\n\n"
        "Let's start.\n\n"
        "What's your first name?"
    )
