ARG PYTHON_VERSION="3.11"

FROM docker.io/library/python:"${PYTHON_VERSION}-slim" as builder

COPY requirements.txt /tmp/
COPY pip.conf /etc/pip.conf

ENV VENV="/venv"
ENV PATH="${VENV}/bin:${PATH}"

RUN python -m venv "${VENV}" \
    && pip install --no-cache-dir -r /tmp/requirements.txt

FROM docker.io/library/python:"${PYTHON_VERSION}-slim"

ENV VENV="/venv"
ENV PATH="${VENV}/bin:${PATH}"

COPY --from=builder "${VENV}" "${VENV}"

WORKDIR /app

COPY src/ .
COPY debian.sources /etc/apt/sources.list.d/
COPY root-ca.pem /usr/local/share/ca-certificates/root-ca.crt

# DL3008 warning: Pin versions in apt get install
# hadolint ignore=DL3008
RUN apt-get update \
    && apt-get install --no-install-recommends -y git \
    && apt-get upgrade -y \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* \
    && adduser --disabled-password --comment "Speos NV/SA" speos \
    && chown -R speos:speos /app \
    && update-ca-certificates \
    && pip uninstall -y setuptools

USER speos

RUN git config --global --add safe.directory "${PWD}"

ENV TZ="Europe/Brussels"

ENTRYPOINT [ "python", "main.py" ]
