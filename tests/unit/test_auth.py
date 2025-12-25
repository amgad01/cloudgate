import pytest

from services.auth.services.password_service import hash_password, verify_password
from shared.schemas.auth import UserCreate


class TestPasswordService:
    def test_hash_password(self) -> None:
        password = "SecurePassword123!"
        hashed = hash_password(password)
        assert hashed != password
        assert len(hashed) > 0

    def test_verify_password_correct(self) -> None:
        password = "SecurePassword123!"
        hashed = hash_password(password)
        assert verify_password(password, hashed) is True

    def test_verify_password_incorrect(self) -> None:
        password = "SecurePassword123!"
        wrong_password = "WrongPassword123!"
        hashed = hash_password(password)
        assert verify_password(wrong_password, hashed) is False

    def test_different_hashes_same_password(self) -> None:
        password = "SecurePassword123!"
        hash1 = hash_password(password)
        hash2 = hash_password(password)
        assert hash1 != hash2
        assert verify_password(password, hash1) is True
        assert verify_password(password, hash2) is True


class TestUserCreateSchema:
    def test_valid_user(self) -> None:
        user = UserCreate(
            email="test@example.com",
            password="SecurePass123!",
            first_name="John",
            last_name="Doe",
        )
        assert user.email == "test@example.com"
        assert user.password == "SecurePass123!"

    def test_invalid_email(self) -> None:
        with pytest.raises(ValueError):
            UserCreate(
                email="invalid-email",
                password="SecurePass123!",
                first_name="John",
                last_name="Doe",
            )

    def test_password_too_short(self) -> None:
        with pytest.raises(ValueError):
            UserCreate(
                email="test@example.com",
                password="Short1!",
                first_name="John",
                last_name="Doe",
            )

    def test_password_no_uppercase(self) -> None:
        with pytest.raises(ValueError):
            UserCreate(
                email="test@example.com",
                password="lowercase123!",
                first_name="John",
                last_name="Doe",
            )

    def test_password_no_lowercase(self) -> None:
        with pytest.raises(ValueError):
            UserCreate(
                email="test@example.com",
                password="UPPERCASE123!",
                first_name="John",
                last_name="Doe",
            )

    def test_password_no_digit(self) -> None:
        with pytest.raises(ValueError):
            UserCreate(
                email="test@example.com",
                password="NoDigits!!!",
                first_name="John",
                last_name="Doe",
            )

    def test_password_no_special(self) -> None:
        with pytest.raises(ValueError):
            UserCreate(
                email="test@example.com",
                password="NoSpecial123",
                first_name="John",
                last_name="Doe",
            )
