import structlog
from fastapi import FastAPI, status
from fastapi.responses import JSONResponse
from fastapi_jwt_auth import AuthJWT
from gunicorn import glogging
from pydantic.main import BaseModel
from starlette.requests import Request

from app.core.database import get_database, get_test_database
from app.core.events import startup_event, shutdown_event, startup_test_event, shutdown_test_event
from app.core.log_config import configure_logging
from app.orders.routes import order_router
from app.settings import settings
from app.users.routes import user_router

configure_logging(log_level=settings.LOG_LEVEL, log_format=settings.LOG_FORMAT)
logger = structlog.get_logger("app")


class UniformLogger(glogging.Logger):
    def setup(self, cfg):
        configure_logging(log_level=settings.LOG_LEVEL, log_format=settings.LOG_FORMAT)


async def logging_dependency(request: Request):
    path_params = getattr(request, "path_params", None)
    query_params = getattr(request, "query_params", None)
    body = getattr(request, "_json", None)

    logger.debug(
        f'{request.method} {request.url}, path_params={path_params}, query_params={query_params}, body={body}'
    )


async def health_check():
    return JSONResponse(
        content={"Health": "Ok"},
        status_code=status.HTTP_200_OK
    )


class AuthJWTSettings(BaseModel):
    authjwt_secret_key = settings.JWT_SECRET_KEY
    authjwt_access_token_expires = settings.ACCESS_TOKEN_EXPIRE


@AuthJWT.load_config
def get_config():
    return AuthJWTSettings()


app = FastAPI(
    title="Pocket Law",
    version="0.0.1",
    openapi_version="3.0.0",
    # root_path="/api",
)

app.include_router(user_router)
app.include_router(order_router)

app.add_api_route("/service/health/", health_check)


testing = False
if not testing:
    app.add_event_handler("startup", startup_event)
    app.add_event_handler("shutdown", shutdown_event)
else:
    app.dependency_overrides[get_database] = get_test_database

    app.add_event_handler("startup", startup_test_event)
    app.add_event_handler("shutdown", shutdown_test_event)

