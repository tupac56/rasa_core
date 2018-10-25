FROM python:2.7-slim

SHELL ["/bin/bash", "-c"]

RUN apt-get update -qq && \
  apt-get install -y --no-install-recommends \
  build-essential \
  wget \
  openssh-client \
  graphviz-dev \
  pkg-config \
  git-core \
  openssl \
  libssl-dev \
  libffi6 \
  libffi-dev \
  libpng-dev \
  libc6-dev \
  freetds-bin \
  freetds-common \
  freetds-dev \
  curl && \
  apt-get clean && \
  rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/* && \
  mkdir /app

WORKDIR /app

ADD .freetds.conf /root

# Copy as early as possible so we can cache ...
ADD requirements.txt .

RUN pip install -r requirements.txt --no-cache-dir

ADD . .

RUN pip install -e . --no-cache-dir

RUN python -m spacy download en

VOLUME ["/app/dialogue", "/app/nlu", "/app/out"]

EXPOSE 5005

ENTRYPOINT ["./entrypoint.sh"]

CMD ["start", "-d", "./dialogue", "-u", "./nlu"]