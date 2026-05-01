from datetime import UTC, datetime

from fastapi import APIRouter

from app.deps import CurrentUser, SessionDep
from app.schemas.user import UserOut, UserPatchIn

router = APIRouter(prefix="/me", tags=["me"])


@router.get("", response_model=UserOut, response_model_by_alias=True)
async def get_me(user: CurrentUser) -> UserOut:
    return UserOut.model_validate(user)


@router.patch("", response_model=UserOut, response_model_by_alias=True)
async def patch_me(
    payload: UserPatchIn, user: CurrentUser, session: SessionDep
) -> UserOut:
    updates = payload.model_dump(exclude_unset=True)
    for key, value in updates.items():
        setattr(user, key, value)
    if updates:
        user.updated_at = datetime.now(UTC)
        await session.commit()
        await session.refresh(user)
    return UserOut.model_validate(user)
