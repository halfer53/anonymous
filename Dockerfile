# Version 0.1

FROM centos:latest
MAINTAINER mabosen@hc360.com

ENV FATHER_HOST_NAME="spider_tj_3"

COPY software/zookeeper-3.4.9-1.x86_64.rpm /
COPY config/supervisord.conf /etc/
COPY config/squid.conf /etc/squid/
COPY config/resolv.conf /etc/
COPY source/*.py /app/pptp_proxy/
COPY tools/python_common/*.py /tools/python_common/

RUN rpm -i zookeeper-3.4.9-1.x86_64.rpm && rm -rf zookeeper-3.4.9-1.x86_64.rpm
RUN yum clean all && yum install net-tools pptp pptp-setup fontconfig squid -y && yum clean all
RUN mkdir /etc/ppp/peers
RUN cp /usr/share/zoneinfo/Asia/Shanghai /etc/localtime
RUN curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py \
        && python get-pip.py \
        && rm -rf get-pip.py \
        && pip install --no-cache-dir requests supervisor kazoo pymongo \
        && pip install --no-cache-dir 'meld3 == 1.0.1' \
