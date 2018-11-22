FROM python:2.7-slim

SHELL ["/bin/bash", "-c"]

RUN apt-get update -qq && \
  apt-get install -y --no-install-recommends \
  build-essential \
  apt-transport-https \
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
  tdsodbc \
  gnupg \
  curl && \
  apt-get clean && \
  rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/* && \
  mkdir /app

# Add latest MS packages
RUN curl https://packages.microsoft.com/keys/microsoft.asc | apt-key add -
RUN curl https://packages.microsoft.com/config/debian/9/prod.list > /etc/apt/sources.list.d/mssql-release.list

# install SQL Server drivers
RUN apt-get update && ACCEPT_EULA=Y apt-get install -y msodbcsql17 unixodbc-dev

WORKDIR /app

# install SQL Server Python SQL Server connector module - pyodbc
RUN pip install --upgrade pip

# Copy as early as possible so we can cache ...
ADD requirements.txt .

RUN pip install -r requirements.txt --no-cache-dir

ADD . .

RUN pip install -e . --no-cache-dir

RUN python -m spacy download en

ADD mssql-setup/.freetds.conf /root
ADD mssql-setup/etc_freetds_freetds.conf /etc/freetds/freetds.conf
ADD mssql-setup/etc_odbc.ini /etc/odbc.ini
ADD mssql-setup/etc_odbcinst.ini /etc/odbcinst.ini

VOLUME ["/app/dialogue", "/app/nlu", "/app/out"]

EXPOSE 5005

ENTRYPOINT ["./entrypoint.sh"]

CMD ["start", "-d", "./dialogue", "-u", "./nlu"]