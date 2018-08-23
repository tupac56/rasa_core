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
  curl && \
  apt-get clean && \
  rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/* && \
  mkdir /app

# for pyodbc
RUN apt-get update && apt-get install -y gcc unixodbc-dev
RUN apt-get update && apt-get install -y tdsodbc unixodbc-dev \
  && apt install unixodbc-bin -y  \
  && apt-get clean -y

RUN echo "[FreeTDS]\n\
  Description = FreeTDS unixODBC Driver\n\
  Driver = /usr/lib/x86_64-linux-gnu/odbc/libtdsodbc.so\n\
  Setup = /usr/lib/x86_64-linux-gnu/odbc/libtdsS.so" >> /etc/odbcinst.ini

WORKDIR /app

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