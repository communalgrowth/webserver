# -*- mode: org -*-

* Webserver with litestar

Run the example with

#+begin_src sh
  python3 -m venv .venv
  source .venv/bin/activate
  pip install .
  LITESTAR_APP=app.main:app litestar run --reload
#+end_src
