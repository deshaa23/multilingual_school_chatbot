from fastapi.security import OAuth2PasswordBearer
from fastapi import Depends,HTTPException
from backend.database import fetch_one
from backend.auth_utils import verify_access_token
from fastapi import HTTPException
 
oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/auth/login"
)

def get_current_user(
        token:str= Depends(oauth2_scheme)
):
    print("TOKEN RECEIVED:", token)
    email = verify_access_token(token)

    query="""
    select 
    user_id,
    email,
    role
    from users
    where email = %s;
    """
    user = fetch_one(
        query,
        (email,)
    )
    if user is None:
        raise HTTPException(
            status_code=401,
            detail="User not found."
        )
    return user

def require_role(*allowed_roles):
    def role_checker(
            current_user= Depends(get_current_user)
    ):
        print("current user:", current_user)
        print("role:", repr(current_user["role"]))
        print("allowed:", allowed_roles)
        if current_user["role"] not in allowed_roles:
            raise HTTPException(
                status_code=403,
                detail="You do not have permission to perform this action."
            )
        return current_user
    return role_checker