from aiogram.fsm.state import State, StatesGroup


class SchedulingStates(StatesGroup):
    """States used when proposing a match schedule."""

    date = State()
    time = State()