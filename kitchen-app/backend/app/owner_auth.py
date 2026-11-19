from hmac import compare_digest
from os import getenv
from typing import Annotated

from fastapi import Depends, HTTPException
from fastapi.security import HTTPBasic, HTTPBasicCredentials

basic = HTTPBasic(realm="Percy Kitchen Owner", auto_error=False)


def require_owner(credentials: Annotated[HTTPBasicCredentials | None, Depends(basic)]) -> None:
    password = getenv("OWNER_PASSWORD", "")
    headers = {"Cache-Control": "no-store", "X-Robots-Tag": "noindex, nofollow"}
    if len(password) < 32:
        raise HTTPException(503, "Owner access is unavailable.", headers=headers)
    if credentials is not None:
        valid_user = compare_digest(credentials.username.encode(), b"owner")
        valid_password = compare_digest(credentials.password.encode(), password.encode())
        if valid_user and valid_password:
            return
    headers["WWW-Authenticate"] = 'Basic realm="Percy Kitchen Owner"'
    raise HTTPException(401, "Owner authentication required.", headers=headers)


kitchen_basic = HTTPBasic(realm="Percy Kitchen Staff", auto_error=False)


def require_kitchen(credentials: Annotated[HTTPBasicCredentials | None, Depends(kitchen_basic)]) -> None:
    password = getenv("KITCHEN_PASSWORD", "")
    headers = {"Cache-Control": "no-store", "X-Robots-Tag": "noindex, nofollow"}
    if len(password) < 32:
        raise HTTPException(503, "Kitchen access is unavailable.", headers=headers)
    if credentials is not None:
        valid_user = compare_digest(credentials.username.encode(), b"kitchen")
        valid_password = compare_digest(credentials.password.encode(), password.encode())
        if valid_user and valid_password:
            return
    headers["WWW-Authenticate"] = 'Basic realm="Percy Kitchen Staff"'
    raise HTTPException(401, "Kitchen authentication required.", headers=headers)
