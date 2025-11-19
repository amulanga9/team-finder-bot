"""
Unit tests для validators.

Тестируем валидацию входных данных.
"""
import pytest
from bot.common.validators import TextValidator, SkillsValidator, InvitationValidator
from bot.common.exceptions import ValidationError, InvitationLimitExceededError


class TestTextValidator:
    """Тесты для TextValidator"""

    def test_validate_name_success(self):
        """Валидное имя проходит проверку"""
        name = "John Doe"
        result = TextValidator.validate_name(name)
        assert result == "John Doe"

    def test_validate_name_strips_whitespace(self):
        """Пробелы удаляются"""
        name = "  John Doe  "
        result = TextValidator.validate_name(name)
        assert result == "John Doe"

    def test_validate_name_too_short(self):
        """Слишком короткое имя вызывает ошибку"""
        with pytest.raises(ValidationError) as exc_info:
            TextValidator.validate_name("A")
        assert "слишком короткое" in str(exc_info.value.message).lower()

    def test_validate_name_too_long(self):
        """Слишком длинное имя вызывает ошибку"""
        long_name = "A" * 51
        with pytest.raises(ValidationError) as exc_info:
            TextValidator.validate_name(long_name)
        assert "слишком длинное" in str(exc_info.value.message).lower()

    def test_validate_team_name_success(self):
        """Валидное название команды"""
        team_name = "Awesome Team"
        result = TextValidator.validate_team_name(team_name)
        assert result == "Awesome Team"

    def test_validate_team_name_too_short(self):
        """Слишком короткое название команды"""
        with pytest.raises(ValidationError):
            TextValidator.validate_team_name("AB")

    def test_validate_description_none(self):
        """None description возвращает None"""
        result = TextValidator.validate_description(None)
        assert result is None

    def test_validate_description_empty(self):
        """Пустое описание возвращает None"""
        result = TextValidator.validate_description("   ")
        assert result is None

    def test_validate_description_too_long(self):
        """Слишком длинное описание вызывает ошибку"""
        long_description = "A" * 201
        with pytest.raises(ValidationError):
            TextValidator.validate_description(long_description)


class TestSkillsValidator:
    """Тесты для SkillsValidator"""

    def test_validate_team_skills_success(self):
        """Валидные навыки для команды"""
        skills = ["Python", "React", "Design"]
        result = SkillsValidator.validate_team_skills(skills)
        assert result == skills

    def test_validate_team_skills_empty(self):
        """Пустой список навыков вызывает ошибку"""
        with pytest.raises(ValidationError):
            SkillsValidator.validate_team_skills([])

    def test_validate_participant_skills_success(self):
        """Валидные навыки для соискателя (1-3)"""
        skills = ["Python", "React"]
        result = SkillsValidator.validate_participant_skills(skills)
        assert result == skills

    def test_validate_participant_skills_too_many(self):
        """Слишком много навыков для соискателя"""
        skills = ["Python", "React", "Design", "Marketing"]
        with pytest.raises(ValidationError):
            SkillsValidator.validate_participant_skills(skills)

    def test_validate_cofounder_skill_success(self):
        """Валидный навык для co-founder"""
        skill = "Backend (Python/Go)"
        result = SkillsValidator.validate_cofounder_skill(skill)
        assert result == skill

    def test_validate_cofounder_skill_none(self):
        """None навык вызывает ошибку"""
        with pytest.raises(ValidationError):
            SkillsValidator.validate_cofounder_skill(None)


class TestInvitationValidator:
    """Тесты для InvitationValidator"""

    def test_validate_self_invitation_fail(self):
        """Нельзя приглашать самого себя"""
        with pytest.raises(ValidationError) as exc_info:
            InvitationValidator.validate_self_invitation(1, 1)
        assert "самому себе" in str(exc_info.value.message).lower()

    def test_validate_self_invitation_success(self):
        """Можно приглашать других"""
        result = InvitationValidator.validate_self_invitation(1, 2)
        assert result is True

    def test_validate_invitation_limit_success(self):
        """Лимит не превышен"""
        result = InvitationValidator.validate_invitation_limit(3, 5)
        assert result is True

    def test_validate_invitation_limit_exceeded(self):
        """Лимит превышен"""
        with pytest.raises(InvitationLimitExceededError) as exc_info:
            InvitationValidator.validate_invitation_limit(5, 5)
        assert exc_info.value.current_count == 5
        assert exc_info.value.max_count == 5
