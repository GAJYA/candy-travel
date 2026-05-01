from pydantic import BaseModel, ConfigDict, Field

from app.schemas.user import UserOut


class WechatLoginIn(BaseModel):
    code: str = Field(min_length=1, max_length=128)


class LoginOut(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    token: str
    expires_in: int = Field(serialization_alias="expiresIn")
    user: UserOut
