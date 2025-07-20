from pathlib import Path
from invoke import Collection, task

app_dir = Path("src/app")
app_templ_dir = app_dir.joinpath("templates")
app_static_dir = app_dir.joinpath("static")
html_dir = Path("_build/static_website")
html_static_dir = html_dir.joinpath("static")


@task
def build_website(c):
    """
    Build the website locally.
    """
    templates = Path(app_templ_dir).glob("*.jinja2")
    c.run(f"mkdir -p {html_static_dir}")
    for template in templates:
        c.run(
            f"""
            jinja -d {app_templ_dir.joinpath('local_render.json')} {template} \
                  -o {html_dir.joinpath(template.stem)}
            """
        )
    c.run(f"cp {app_static_dir.joinpath('style.css')} {html_static_dir}")


@task
def view_website(c):
    """
    View the website index with Firefox.
    """
    c.run(f"firefox {html_dir.joinpath('search.html')}")


@task
def clean_website(c):
    """
    Remove the build artifacts.
    """
    c.run(f"rm -rf {html_dir}")


col_website = Collection("static_website")
col_website.add_task(build_website, "build")
col_website.add_task(view_website, "view")
col_website.add_task(clean_website, "clean")

namespace = Collection(col_website)
