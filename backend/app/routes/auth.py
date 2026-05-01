from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert

from app.deps import SessionDep
from app.models import User
from app.schemas.auth import LoginOut, WechatLoginIn
from app.schemas.user import UserOut
from app.services.jwt_service import issue_token
from app.services.wechat import WechatLoginError, code2session

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/wechat/login", response_model=LoginOut, response_model_by_alias=True)
async def wechat_login(payload: WechatLoginIn, session: SessionDep) -> LoginOut:
    try:
        wx_session = await code2session(payload.code)
    except WechatLoginError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"wechat code invalid: {e.errcode} {e.errmsg}",
        ) from e

    # Upsert by openid: 老用户更新 unionid，新用户落库
    stmt = (
        pg_insert(User)
        .values(openid=wx_session.openid, unionid=wx_session.unionid)
        .on_conflict_do_update(
            index_elements=["openid"],
            set_={"unionid": wx_session.unionid},
        )
        .returning(User.id)
    )
    result = await session.execute(stmt)
    user_id = result.scalar_one()
    await session.commit()

    user = await session.scalar(select(User).where(User.id == user_id))
    assert user is not None  # 刚 upsert，必定存在

    token, expires_in = issue_token(user.id)
    return LoginOut(token=token, expires_in=expires_in, user=UserOut.model_validate(user))
