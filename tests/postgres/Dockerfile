FROM postgres:16-alpine
RUN apk add --no-cache python3 py3-pip nodejs && python3 -m venv /opt/hnsg-test
RUN node --experimental-default-type=module --eval 'void 0'
COPY requirements.txt requirements-postgres.txt /tmp/requirements/
RUN /opt/hnsg-test/bin/python -m pip install --no-cache-dir -r /tmp/requirements/requirements-postgres.txt pytest==9.0.2
RUN touch /opt/hnsg-postgres-fixture
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /workspace
