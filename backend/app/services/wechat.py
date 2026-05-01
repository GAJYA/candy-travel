from dataclasses import dataclass

import httpx

from app.config import settings

CODE2SESSION_URL = "https://api.weixin.qq.com/sns/jscode2session"


class WechatLoginError(Exception):
    """微信登录失败，errcode 来自微信侧"""

    def __init__(self, errcode: int, errmsg: str):
        self.errcode = errcode
        self.errmsg = errmsg
        super().__init__(f"wechat code2session failed: [{errcode}] {errmsg}")


@dataclass
class WechatSession:
    openid: str
    session_key: str
    unionid: str | None = None


async def code2session(code: str) -> WechatSession:
    """用 jscode 换 openid + session_key。"""
    if not settings.wechat_appid or not settings.wechat_appsecret:
        raise RuntimeError("WECHAT_APPID / WECHAT_APPSECRET not configured")

    params = {
        "appid": settings.wechat_appid,
        "secret": settings.wechat_appsecret,
        "js_code": code,
        "grant_type": "authorization_code",
    }
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.get(CODE2SESSION_URL, params=params)
        resp.raise_for_status()
        data = resp.json()

    errcode = data.get("errcode", 0)
    if errcode:
        raise WechatLoginError(errcode, data.get("errmsg", "unknown"))

    return WechatSession(
        openid=data["openid"],
        session_key=data["session_key"],
        unionid=data.get("unionid"),
    )
