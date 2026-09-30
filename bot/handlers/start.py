from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from bot.states.registration import RegistrationStates


router = Router()


@router.message(CommandStart())
async def start_handler(message: Message, state: FSMContext) -> None:
    """Start the student registration process."""

    await state.clear()
    await state.set_state(RegistrationStates.first_name)

    await message.answer(
        "🎾 Welcome to TTPU Tennis!\n\n"
        "To use the tennis system, you need to create your "
        "student profile.\n\n"
        "Let's start.\n\n"
        "What's your first name?"
    )
