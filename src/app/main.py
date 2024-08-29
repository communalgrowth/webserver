from importlib.resources import files

from litestar import Controller, Litestar, MediaType, Request, Response, get
from litestar.status_codes import HTTP_404_NOT_FOUND, HTTP_500_INTERNAL_SERVER_ERROR
from litestar.contrib.jinja import JinjaTemplateEngine
from litestar.response import Template
from litestar.template.config import TemplateConfig
from litestar.static_files import create_static_files_router
from litestar.datastructures import CacheControlHeader
from litestar.exceptions import HTTPException

global_ctx = {"website_name": "Communal Growth"}

static_router = create_static_files_router(
    path="/static", directories=[files("static").name]
)


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
    async def search(self, d: str = "") -> Template:
        ctx = global_ctx | dict(search_value=d)
        return Template(template_name="search.html.jinja2", context=ctx)

    @get("/submit")
    async def submit(self) -> Template:
        return Template(template_name="submit.html.jinja2", context=global_ctx)

    @get("/contact")
    async def contact(self) -> Template:
        return Template(template_name="contact.html.jinja2", context=global_ctx)


app = Litestar(
    route_handlers=[MyController, static_router],
    template_config=TemplateConfig(
        directory=files("templates").name, engine=JinjaTemplateEngine
    ),
    openapi_config=None,
    exception_handlers={
        HTTP_404_NOT_FOUND: server_error_404,
        HTTPException: generic_exception_handler,
    },
)
