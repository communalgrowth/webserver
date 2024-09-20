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

* Running the test suite

Install the ~tests~ variant of the package, e.g. via

#+begin_src sh
  pip install .[tests]
#+end_src

and execute the tests in parallel with:

#+begin_src sh
  pytest -n auto
#+end_src
