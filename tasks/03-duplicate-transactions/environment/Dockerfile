FROM python:3.12-slim@sha256:5e2bdb1b0d542d5039cffb8181c65930093949194a65c365dfb1b0fe13a4fa5b
WORKDIR /workspace
# requirements.txt is supplied by runner, not by candidate code.
COPY requirements.txt /tmp/requirements.txt
RUN python -m pip install --no-cache-dir --disable-pip-version-check -r /tmp/requirements.txt
COPY . .
CMD ["python", "-m", "pytest", "-q", "/verifier"]
