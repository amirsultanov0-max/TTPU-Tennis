from aiogram.fsm.state import State, StatesGroup


class RegistrationStates(StatesGroup):
    """States used during student registration."""

    first_name = State()
    last_name = State()
    group = State()
    student_id = State()
    phone = State()
    confirmation = State()


class RegistrationEditStates(StatesGroup):
    """States used when editing registration information."""

    first_name = State()
    last_name = State()
    group = State()
    student_id = State()