from backend.auth_utils import (
    create_access_token,
    verify_access_token
)

token = create_access_token(
    {
        "sub": "Atisha@school.com"
    }
)

print("Token:")
print(token)

print()

email = verify_access_token(token)

print("Decoded Email:")
print(email)