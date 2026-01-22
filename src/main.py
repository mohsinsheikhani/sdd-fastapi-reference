from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from src.api.v1.router import router as v1_router
from src.core.exceptions import (
    AccountLockedError,
    InvalidCredentialsError,
    RateLimitError,
    ResetTokenInvalidError,
    TokenExpiredError,
    TokenInvalidError,
    TokenRevokedError,
    UserExistsError,
    UserNotFoundError,
)
from src.schemas.error import ErrorResponse

app = FastAPI(
    title="User Authentication API",
    description="User authentication endpoints for the Task Management API",
    version="1.0.0",
)

app.include_router(v1_router)


@app.exception_handler(UserExistsError)
async def user_exists_handler(request: Request, exc: UserExistsError) -> JSONResponse:
    return JSONResponse(
        status_code=409,
        content=ErrorResponse(
            code="USER_EMAIL_EXISTS",
            message="A user with this email already exists",
        ).model_dump(),
    )


@app.exception_handler(UserNotFoundError)
async def user_not_found_handler(
    request: Request, exc: UserNotFoundError
) -> JSONResponse:
    return JSONResponse(
        status_code=404,
        content=ErrorResponse(
            code="USER_NOT_FOUND",
            message="User not found",
        ).model_dump(),
    )


@app.exception_handler(InvalidCredentialsError)
async def invalid_credentials_handler(
    request: Request, exc: InvalidCredentialsError
) -> JSONResponse:
    return JSONResponse(
        status_code=401,
        content=ErrorResponse(
            code="AUTH_INVALID_CREDENTIALS",
            message="Invalid email or password",
        ).model_dump(),
    )


@app.exception_handler(AccountLockedError)
async def account_locked_handler(
    request: Request, exc: AccountLockedError
) -> JSONResponse:
    return JSONResponse(
        status_code=403,
        content=ErrorResponse(
            code="AUTH_ACCOUNT_LOCKED",
            message="Account is temporarily locked due to too many failed attempts",
        ).model_dump(),
    )


@app.exception_handler(TokenExpiredError)
async def token_expired_handler(
    request: Request, exc: TokenExpiredError
) -> JSONResponse:
    return JSONResponse(
        status_code=401,
        content=ErrorResponse(
            code="AUTH_TOKEN_EXPIRED",
            message="Token has expired",
        ).model_dump(),
    )


@app.exception_handler(TokenInvalidError)
async def token_invalid_handler(
    request: Request, exc: TokenInvalidError
) -> JSONResponse:
    return JSONResponse(
        status_code=401,
        content=ErrorResponse(
            code="AUTH_TOKEN_INVALID",
            message="Invalid token",
        ).model_dump(),
    )


@app.exception_handler(TokenRevokedError)
async def token_revoked_handler(
    request: Request, exc: TokenRevokedError
) -> JSONResponse:
    return JSONResponse(
        status_code=401,
        content=ErrorResponse(
            code="AUTH_TOKEN_REVOKED",
            message="Token has been revoked",
        ).model_dump(),
    )


@app.exception_handler(ResetTokenInvalidError)
async def reset_token_invalid_handler(
    request: Request, exc: ResetTokenInvalidError
) -> JSONResponse:
    return JSONResponse(
        status_code=400,
        content=ErrorResponse(
            code="RESET_TOKEN_INVALID",
            message="Reset token is invalid, expired, or already used",
        ).model_dump(),
    )


@app.exception_handler(RateLimitError)
async def rate_limit_handler(request: Request, exc: RateLimitError) -> JSONResponse:
    return JSONResponse(
        status_code=429,
        content=ErrorResponse(
            code="RATE_LIMIT_EXCEEDED",
            message="Too many requests. Please try again later.",
        ).model_dump(),
    )
