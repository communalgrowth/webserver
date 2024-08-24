# -*- mode: org -*-

* Webserver with litestar

Run the example with

#+begin_src sh
  LITESTAR_APP=app.main:app litestar run --reload
#+end_src

** TODO Read tutorial

Continue tutorial from <https://docs.litestar.dev/2/tutorials/todo-app/0-application-basics.html#route-handlers>.

** Containerfile

For podman, it requires using <https://github.com/containers/podman/issues/3212> to bind port 80.

Another possibility is authbind; see <https://superuser.com/a/892391>.
