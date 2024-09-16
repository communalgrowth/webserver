# -*- mode: org -*-

* Webserver with litestar

Run the example with

#+begin_src sh
  python3 -m venv .venv
  source .venv/bin/activate
  pip install .
  LITESTAR_APP=app.main:app litestar run --reload
#+end_src

* Change log

The change log can be viewed with:

#+begin_src sh
  git tag --sort=committerdate | grep -E v[0-9]+\. | tac | xargs -d'\n' -L1 git tag -n9999
#+end_src
