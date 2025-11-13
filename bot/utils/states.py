"""FSM состояния для диалогов бота"""
from aiogram.fsm.state import State, StatesGroup


class TeamRegistration(StatesGroup):
    """Состояния регистрации команды"""
    waiting_for_team_name = State()
    waiting_for_idea_description = State()
    waiting_for_skills_selection = State()


class ParticipantRegistration(StatesGroup):
    """Состояния регистрации участника"""
    # TODO: будет реализовано позже
    pass


class CofounderRegistration(StatesGroup):
    """Состояния регистрации со-фаундера"""
    # TODO: будет реализовано позже
    pass
