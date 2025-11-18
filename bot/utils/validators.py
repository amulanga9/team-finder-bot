"""Input validation utilities"""
from typing import Optional


class ValidationError(Exception):
    """Custom validation error"""

    pass


def validate_name(name: str, min_length: int = 2, max_length: int = 50) -> str:
    """
    Validate user/team name

    Args:
        name: Name to validate
        min_length: Minimum length
        max_length: Maximum length

    Returns:
        Validated name (stripped)

    Raises:
        ValidationError: If validation fails
    """
    name = name.strip()

    if len(name) < min_length or len(name) > max_length:
        raise ValidationError(
            f"Name must be between {min_length} and {max_length} characters"
        )

    return name


def validate_description(
    text: str, max_length: int = 200, allow_empty: bool = False
) -> Optional[str]:
    """
    Validate description text

    Args:
        text: Text to validate
        max_length: Maximum length
        allow_empty: Allow empty strings

    Returns:
        Validated text or None

    Raises:
        ValidationError: If validation fails
    """
    text = text.strip()

    if not text:
        if allow_empty:
            return None
        raise ValidationError("Description cannot be empty")

    if len(text) > max_length:
        raise ValidationError(f"Description too long (max {max_length} characters)")

    return text


def validate_skills(skills: list, min_count: int = 1, max_count: int = 10) -> list:
    """
    Validate skills list

    Args:
        skills: List of skill keys
        min_count: Minimum number of skills
        max_count: Maximum number of skills

    Returns:
        Validated skills list

    Raises:
        ValidationError: If validation fails
    """
    if len(skills) < min_count:
        raise ValidationError(f"Select at least {min_count} skill(s)")

    if len(skills) > max_count:
        raise ValidationError(f"Maximum {max_count} skills allowed")

    return skills
