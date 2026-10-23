# Technique: Custom Exception Hierarchy
class ValidationError(Exception):
    """Base exception class for application data validation errors."""
    pass

class EmptyFieldError(ValidationError):
    """Raised when a required form field is missing or empty."""
    pass

class WeakPasswordError(ValidationError):
    """Raised when a password fails complexity guidelines."""
    pass

class DuplicateUserError(ValidationError):
    """Raised when registering an existing email or username."""
    pass

class InvalidAmountError(ValidationError):
    """Raised when an monetary amount is negative or zero."""
    pass

def validate_password_strength(password):
    if len(password) < 8:
        raise WeakPasswordError("Password must be at least 8 characters long.")
    if not any(char.isupper() for char in password):
        raise WeakPasswordError("Password must contain at least one uppercase letter.")
    if not any(char.isdigit() for char in password):
        raise WeakPasswordError("Password must contain at least one number.")