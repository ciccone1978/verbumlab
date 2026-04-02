from typing import Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import get_db, get_current_user
from app.models.user import User
from app.schemas.user import UserOut, UserUpdate, PasswordChange
from app.services.user_service import user_service
from app.core.security import verify_password

router = APIRouter()

@router.get("/me", response_model=UserOut)
async def read_user_me(
    current_user: User = Depends(get_current_user),
) -> Any:
    """
    Get current user profile.
    """
    return current_user

@router.patch("/me", response_model=UserOut)
async def update_user_me(
    *,
    db: AsyncSession = Depends(get_db),
    user_in: UserUpdate,
    current_user: User = Depends(get_current_user),
) -> Any:
    """
    Update own user profile.
    """
    return await user_service.update(db, db_obj=current_user, obj_in=user_in)

@router.post("/me/password")
async def update_password_me(
    *,
    db: AsyncSession = Depends(get_db),
    password_in: PasswordChange,
    current_user: User = Depends(get_current_user),
) -> Any:
    """
    Update own password.
    """
    if not verify_password(password_in.old_password, current_user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect password",
        )
    if password_in.old_password == password_in.new_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="New password must be different from old password",
        )
    
    await user_service.update(db, db_obj=current_user, obj_in={"password": password_in.new_password})
    return {"message": "Password updated successfully"}
