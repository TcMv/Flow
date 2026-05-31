"""Auth dependencies — get_current_user and require_role."""

from __future__ import annotations

from uuid import UUID

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.app.auth.jwt_handler import decode_token
from src.app.database import get_db
from src.app.models.user import User, UserRole

_security = HTTPBearer(auto_error=False)

INVALID_CREDENTIALS = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Invalid or expired authentication token",
    headers={"WWW-Authenticate": "Bearer"},
)

MISSING_TOKEN = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Authentication required — provide a Bearer token",
    headers={"WWW-Authenticate": "Bearer"},
)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(_security),
    db: AsyncSession = Depends(get_db),
) -> User:
    """Extract and validate the JWT from the Authorization header, return the User.

    Raises 401 if the token is missing, invalid, or the user no longer exists.
    """
    if credentials is None:
        raise MISSING_TOKEN

    token = credentials.credentials
    try:
        payload = decode_token(token)
    except JWTError:
        raise INVALID_CREDENTIALS

    user_id_str: str | None = payload.get("sub")
    if user_id_str is None:
        raise INVALID_CREDENTIALS

    try:
        user_id = UUID(user_id_str)
    except ValueError:
        raise INVALID_CREDENTIALS

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if user is None:
        raise INVALID_CREDENTIALS

    return user


def require_role(*roles: UserRole):
    """Dependency factory: require the current user to have one of the given roles.

    Usage::

        @router.get("/admin-only")
        async def admin_endpoint(user: User = Depends(require_role(UserRole.admin))):
            ...
    """

    async def _role_checker(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Requires one of: {', '.join(r.value for r in roles)}",
            )
        return current_user

    return _role_checker
