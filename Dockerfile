FROM python:3.9.5-buster

ENV PIP_DISABLE_PIP_VERSION_CHECK=on

WORKDIR /usr/src/app

COPY ./requirements-nogpu.txt /usr/src/app/requirements.txt
RUN pip install -r requirements.txt

RUN pip install gunicorn

COPY ./entrypoint.sh /usr/src/app/entrypoint.sh
RUN chmod +x /usr/src/app/entrypoint.sh

COPY . /usr/src/app

CMD ["/usr/src/app/entrypoint.sh"]