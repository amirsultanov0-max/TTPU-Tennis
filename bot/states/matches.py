from aiogram.fsm.state import State, StatesGroup


class MatchResultStates(StatesGroup):
    """States used while submitting a Best-of-3 match result."""

    waiting_for_set_1_score = State()
    waiting_for_set_2_score = State()
    waiting_for_set_3_score = State()
