FROM ubuntu:18.04
MAINTAINER a.matveev

ARG DEBIAN_FRONTEND=noninteractive

COPY requirements.txt requirements.txt

RUN apt	update && \
	apt install -y --no-install-recommends tzdata vim wget unzip && \
	apt install -y --no-install-recommends \
		python3 python3-pip python3-idna python3-six python3-setuptools \
		python3-dev build-essential \
		locales git \
		libpq-dev && \
	pip3 install --no-cache-dir -r requirements.txt && \
	apt remove -y python3-dev build-essential && \
	apt -y autoremove && \
	rm -rf /var/lib/apt/lists/*

COPY ["./source/server/", "/opt/shanno/"]
COPY ["./contribute/docker/run.sh", "/opt/shanno/"]

# setup
RUN cd /opt/shanno && \
	python3 ./manage.py collectstatic --noinput

EXPOSE 8000
WORKDIR /opt/shanno
ENTRYPOINT ["/opt/shanno/run.sh"]
# CMD ["--help"]