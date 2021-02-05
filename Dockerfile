FROM ubuntu:20.04

ENV BROWSER=/browser \
    LC_ALL=en_US.UTF-8 \
    SETUPTOOLS_USE_DISTUTILS=stdlib

RUN echo '#!/bin/bash\n\
\n\
echo\n\
echo "  $@"\n\
echo\n' > /browser && \
    chmod +x /browser

# runtime environment
RUN apt-get update && \
    apt-get install -y --no-install-suggests --no-install-recommends \
      apt-utils ca-certificates gnupg2 locales curl python3 python3-distutils && \
    echo "en_US.UTF-8 UTF-8" > /etc/locale.gen && \
    locale-gen && \
    curl -L https://bootstrap.pypa.io/get-pip.py | python3 && \
    pip3 install --no-cache-dir cython && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

ADD requirements.txt /project/requirements.txt
RUN apt-get update && \
    apt-get install -y --no-install-suggests --no-install-recommends python3-dev gcc && \
    pip3 install -r /project/requirements.txt && \
    apt-get purge -y python3-dev gcc && \
    apt-get -y autoremove && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

ADD . /project
RUN pip3 install -e /project
ARG COMMIT
RUN echo "__commit__ = \"$COMMIT\"" >>/project/names_matcher/metadata.py && \
    echo "__date__ = \"$(date -u +'%Y-%m-%dT%H:%M:%SZ')\"" >>/project/names_matcher/metadata.py

ENTRYPOINT ["python3", "-m", "names_matcher"]