import json
import typing

from fastapi import FastAPI, HTTPException, Request, Response, status
from fastapi.requests import HTTPConnection
from starlette.types import Receive, Scope, Send

from .exceptions import InvalidCookieException
from .managers import SessionManager

__all__ = ("SessionMiddleware",)


class SessionMiddleware:
    """A middleware for initializing and managing a user session."""

    def __init__(
        self, app: FastAPI, manager: SessionManager, strict: bool = False
    ) -> "SessionMiddleware":
        """
        :param app: A fastapi app instance
        :param manager: An instance of SessionManager
        :param strict: indicates processing an incoming cookie more rigorously
        """
        self.app = app
        self.manager = manager
        self.strict = strict

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        WEBSOCKET_TYPE = "websocket"
        if scope["type"] not in ("http", WEBSOCKET_TYPE):  # pragma: no cover
            await self.app(scope, receive, send)
            return

        if scope["type"] == WEBSOCKET_TYPE:
            request = HTTPConnection(scope, receive)
        else:
            request = Request(scope, receive, send)
        scope["session"] = None

        if self.manager.has_cookie(request):
            try:
                scope["session"] = await self.manager.load_session(
                    request,
                    await self.manager.postprocess_cookie(
                        request, self.manager.get_cookie(request)
                    ),
                )
            except InvalidCookieException as exc:
                if self.strict:
                    raise exc from None

        await self.app(scope, receive, send)
