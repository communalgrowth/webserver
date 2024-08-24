FROM python:3 as compiler
ENV PYTHONUNBUFFERED 1
COPY . /myapp
RUN python3 -m venv /opt/venv && \
    /opt/venv/bin/pip3 install /myapp

FROM python:3 as runner
COPY --from=compiler /opt/venv /opt/venv
COPY . /myapp
WORKDIR /myapp
ENV PATH="/opt/venv/bin:$PATH"
ENV LITESTAR_APP=app.main:app
EXPOSE 80
ENTRYPOINT ["litestar", "run",              \
                        "--port", "80",     \
                        "--host", "0.0.0.0" \
           ]
