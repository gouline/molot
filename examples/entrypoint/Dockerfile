FROM python:3.11-slim

RUN pip install molot requests

COPY entrypoint.py ./

ENTRYPOINT [ "python3", "entrypoint.py" ]
