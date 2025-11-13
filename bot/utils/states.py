"""FSM состояния для диалогов бота"""
from aiogram.fsm.state import State, StatesGroup


class TeamRegistration(StatesGroup):
    """Состояния регистрации команды"""
    waiting_for_team_name = State()
    waiting_for_idea_description = State()
    waiting_for_skills_selection = State()


class CofounderRegistration(StatesGroup):
    """Состояния регистрации со-фаундера"""
    waiting_for_name = State()
    waiting_for_skill = State()
    waiting_for_idea_what = State()
    waiting_for_idea_who = State()


class SeekerRegistration(StatesGroup):
    """Состояния регистрации соискателя"""
    waiting_for_name = State()
    waiting_for_skills = State()
