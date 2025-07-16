import os
from importlib.resources import files, as_file
from contextlib import asynccontextmanager
from collections.abc import AsyncGenerator

import psycopg

from litestar import Controller, Litestar, MediaType, Request, Response, get
from litestar.contrib.jinja import JinjaTemplateEngine
from litestar.datastructures import CacheControlHeader, State
from litestar.exceptions import HTTPException
from litestar.response import Template
from litestar.static_files import create_static_files_router
from litestar.status_codes import HTTP_404_NOT_FOUND, HTTP_500_INTERNAL_SERVER_ERROR
from litestar.template.config import TemplateConfig
from litestar.params import Parameter

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

from app.search import search_documents, search_recent
from app.utils import parse_pgpass

global_ctx = {"website_name": "Communal Growth"}

with as_file(files("app").joinpath("static")) as static_dir:
    static_router = create_static_files_router(path="/static", directories=[static_dir])

with as_file(files("app").joinpath("templates")) as templates_dir_str:
    templates_dir = templates_dir_str


def generic_exception_handler(_: Request, exc: Exception) -> Response:
    """Default handler for exceptions subclassed from HTTPException."""
    status_code = getattr(exc, "status_code", HTTP_500_INTERNAL_SERVER_ERROR)
    detail = "Error."
    return Response(
        media_type=MediaType.TEXT,
        content=detail,
        status_code=status_code,
    )


def server_error_404(router: Request, exc: Exception) -> Template:
    """Handler for HTTP 404."""
    del router, exc
    return Template(
        template_name="404.html.jinja2", context=global_ctx, status_code=404
    )


class MyController(Controller):
    # TODO turn on in production
    # cache_control = CacheControlHeader(max_age=86_400, public=True)
    @get("/")
    async def index(self) -> Template:
        return Template(template_name="index.html.jinja2", context=global_ctx)

    @get("/howto")
    async def howto(self) -> Template:
        return Template(template_name="howto.html.jinja2", context=global_ctx)

    @get("/search", cache_control=CacheControlHeader(no_store=True))
    async def search(
        self, state: State, s: str = Parameter(default="", max_length=300)
    ) -> Template:
        d = dict(
            search_value=s,
            results=[],
        )
        if s:
            Session = async_sessionmaker(bind=state.engine)
            results = await search_documents(Session, s)
            d["results"] = results
        else:
            Session = async_sessionmaker(bind=state.engine)
            results = await search_recent(Session)
            d["results"] = results
        ctx = global_ctx | d
        return Template(template_name="search.html.jinja2", context=ctx)

    @get("/subscribe")
    async def subscribe(self) -> Template:
        return Template(template_name="subscribe.html.jinja2", context=global_ctx)

    @get("/contact")
    async def contact(self) -> Template:
        return Template(template_name="contact.html.jinja2", context=global_ctx)


@asynccontextmanager
async def db_connection(app: Litestar) -> AsyncGenerator[None, None]:
    engine = getattr(app.state, "engine", None)
    if engine is None:
        # TODO normally I should be using conf.DB_URL but there is a
        # bug preventing me from doing so; see the documentation of
        # parse_pgpass.
        db_url = parse_pgpass(os.environ["PGPASSFILE"])
        engine = create_async_engine(db_url)
        setattr(app.state, "engine", engine)
    try:
        yield
    finally:
        await engine.dispose()


app = Litestar(
    route_handlers=[MyController, static_router],
    template_config=TemplateConfig(directory=templates_dir, engine=JinjaTemplateEngine),
    openapi_config=None,
    exception_handlers={
        HTTP_404_NOT_FOUND: server_error_404,
        HTTPException: generic_exception_handler,
    },
    lifespan=[db_connection],
)
