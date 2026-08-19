from datetime import datetime, timedelta, timezone
from jose import JWTError, jwt
from fastapi import HTTPException

secret_key="your_super_secret_key_change_this"
Algorithm="HS256"
access_token_expire_minutes = 10080

def create_access_token(data:dict):
    to_encode = data.copy()

    expire= datetime.now(timezone.utc)+timedelta(
        minutes=access_token_expire_minutes
    )
    to_encode.update(
        {
            "exp": expire
        }
    )
    encoded_jwt= jwt.encode(
        to_encode,
        secret_key,
        algorithm=Algorithm
    )
    return encoded_jwt
def verify_access_token(token: str):
    credentials_exception = HTTPException(
        status_code=401,
        detail="Could not validate credentials."
    )

    print("Received token:", token)

    try:
        payload = jwt.decode(
            token,
            secret_key,
            algorithms=[Algorithm]
        )

        print("Decoded payload:", payload)

        email = payload.get("sub")
        print("Email from token:", email)

        if email is None:
            raise credentials_exception

        return email

    except JWTError as e:
        print("JWT Error:", e)
        raise credentials_exception