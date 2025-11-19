"""
Валидаторы для входных данных.

Централизованная валидация позволяет:
1. Переиспользовать логику валидации (DRY)
2. Легко тестировать валидаторы
3. Изменять правила валидации в одном месте
4. Соблюдать Single Responsibility Principle
"""
from typing import List, Optional
from common.constants import (
    MIN_NAME_LENGTH,
    MAX_NAME_LENGTH,
    MIN_TEAM_NAME_LENGTH,
    MAX_TEAM_NAME_LENGTH,
    MAX_DESCRIPTION_LENGTH,
    MIN_SKILLS_COUNT,
    MAX_SKILLS_COUNT_TEAM,
    MAX_SKILLS_COUNT_PARTICIPANT,
    MAX_SKILLS_COUNT_COFOUNDER,
)
from common.exceptions import ValidationError


class TextValidator:
    """Валидатор для текстовых полей"""

    @staticmethod
    def validate_name(name: str) -> str:
        """
        Валидация имени пользователя.

        Args:
            name: имя для валидации

        Returns:
            str: очищенное имя

        Raises:
            ValidationError: если имя не прошло валидацию
        """
        name = name.strip()

        if len(name) < MIN_NAME_LENGTH:
            raise ValidationError(
                f"Имя слишком короткое (минимум {MIN_NAME_LENGTH} символа)",
                field="name",
            )

        if len(name) > MAX_NAME_LENGTH:
            raise ValidationError(
                f"Имя слишком длинное (максимум {MAX_NAME_LENGTH} символов)",
                field="name",
            )

        return name

    @staticmethod
    def validate_team_name(team_name: str) -> str:
        """Валидация названия команды"""
        team_name = team_name.strip()

        if len(team_name) < MIN_TEAM_NAME_LENGTH:
            raise ValidationError(
                f"Название слишком короткое (минимум {MIN_TEAM_NAME_LENGTH} символа)",
                field="team_name",
            )

        if len(team_name) > MAX_TEAM_NAME_LENGTH:
            raise ValidationError(
                f"Название слишком длинное (максимум {MAX_TEAM_NAME_LENGTH} символов)",
                field="team_name",
            )

        return team_name

    @staticmethod
    def validate_description(description: Optional[str]) -> Optional[str]:
        """Валидация описания (идеи, навыков и т.д.)"""
        if description is None:
            return None

        description = description.strip()

        if len(description) == 0:
            return None

        if len(description) > MAX_DESCRIPTION_LENGTH:
            raise ValidationError(
                f"Описание слишком длинное (максимум {MAX_DESCRIPTION_LENGTH} символов)",
                field="description",
            )

        return description


class SkillsValidator:
    """Валидатор для навыков"""

    @staticmethod
    def validate_skills_count(
        skills: List[str], min_count: int, max_count: int, entity_name: str = "навыков"
    ) -> List[str]:
        """
        Универсальная валидация количества навыков.

        Args:
            skills: список навыков
            min_count: минимальное количество
            max_count: максимальное количество
            entity_name: название сущности для сообщения об ошибке

        Returns:
            List[str]: валидированный список навыков

        Raises:
            ValidationError: если количество навыков не в допустимом диапазоне
        """
        if len(skills) < min_count:
            raise ValidationError(
                f"Выберите минимум {min_count} {entity_name}",
                field="skills",
            )

        if len(skills) > max_count:
            raise ValidationError(
                f"Выберите максимум {max_count} {entity_name}",
                field="skills",
            )

        return skills

    @staticmethod
    def validate_team_skills(skills: List[str]) -> List[str]:
        """Валидация навыков для команды"""
        return SkillsValidator.validate_skills_count(
            skills, MIN_SKILLS_COUNT, MAX_SKILLS_COUNT_TEAM, "навыков"
        )

    @staticmethod
    def validate_participant_skills(skills: List[str]) -> List[str]:
        """Валидация навыков для соискателя (1-3)"""
        return SkillsValidator.validate_skills_count(
            skills, MIN_SKILLS_COUNT, MAX_SKILLS_COUNT_PARTICIPANT, "навыка"
        )

    @staticmethod
    def validate_cofounder_skill(skill: Optional[str]) -> str:
        """Валидация навыка для со-фаундера (ровно 1)"""
        if not skill:
            raise ValidationError(
                "Необходимо выбрать один навык",
                field="skill",
            )

        return skill


class InvitationValidator:
    """Валидатор для приглашений"""

    @staticmethod
    def validate_invitation_limit(current_count: int, max_count: int) -> bool:
        """
        Проверка лимита приглашений.

        Args:
            current_count: текущее количество приглашений
            max_count: максимальное количество

        Returns:
            bool: True если лимит не превышен

        Raises:
            ValidationError: если лимит превышен
        """
        if current_count >= max_count:
            from common.exceptions import InvitationLimitExceededError

            raise InvitationLimitExceededError(current_count, max_count)

        return True

    @staticmethod
    def validate_self_invitation(from_user_id: int, to_user_id: int) -> bool:
        """
        Проверка, что пользователь не приглашает сам себя.

        Returns:
            bool: True если валидация прошла

        Raises:
            ValidationError: если пользователь пытается пригласить себя
        """
        if from_user_id == to_user_id:
            raise ValidationError(
                "Нельзя отправить приглашение самому себе",
                field="to_user_id",
            )

        return True
