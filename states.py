from aiogram.fsm.state import State, StatesGroup


class AdminUploadStates(StatesGroup):
    """Промокодтар файлын жүктеу күйі."""
    waiting_for_file = State()


class AdminBroadcastStates(StatesGroup):
    """Жаппай хабарлама тарату күйі."""
    waiting_for_message = State()
