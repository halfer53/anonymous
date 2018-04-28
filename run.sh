#!/bin/sh

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd $DIR

IMG_NAME=pptp-proxy
IMG_VERSION=v1

PROXY_IP=''
PROXY_TJ_IP=''
PROXY_PORT=8900
HTTP_PORT=8800

ips=$(ip addr |grep "global" | grep -v "secondary" | grep -v "docker" | grep -v "vm" | awk -F " " '{print $2}' | cut -d / -f 1)
for ip in $ips
do
    test_ip=$(echo $ip | grep -e "^10\.10\.10\.")
    if [ $test_ip ]
    then
        PROXY_TJ_IP=$test_ip
    fi

    test_ip=$(echo $ip | grep -E "^172.16|^192.168")
    if [ $test_ip ]
    then
        PROXY_IP=$test_ip
    fi
done

function docker_run_dev()
{
    echo nf_conntrack_pptp | tee /etc/modules-load.d/pptp.conf
    modprobe nf_conntrack_pptp

    docker run -i -t -d --name ${IMG_NAME}-dev --privileged --cap-add=ALL \
        -v /dev:/dev \
        -v /lib/modules:/lib/modules \
        -v /usr/share/fontconfig:/usr/share/fontconfig \
        -v /usr/share/fonts:/usr/share/fonts \
        -v ${DIR}/source:/app/pptp_proxy \
        -v ${DIR}/tools:/tools \
        --dns=114.114.114.114 \
        -e "FATHER_HOST_NAME"=$(hostname) \
        -e "PROXY_PORT"=${PROXY_PORT} \
        -e "PROXY_IP"=${PROXY_IP} \
        -e "PROXY_TJ_IP"=${PROXY_TJ_IP} \
        -p ${PROXY_PORT}:${PROXY_PORT} \
        -p ${HTTP_PORT}:${HTTP_PORT} \
        ${IMG_NAME}:${IMG_VERSION} /usr/bin/supervisord
}

function docker_run()
{
    echo nf_conntrack_pptp | tee /etc/modules-load.d/pptp.conf
    modprobe nf_conntrack_pptp

    docker run -i -t -d --name ${IMG_NAME} --privileged --cap-add=ALL \
        -v /dev:/dev \
        -v /lib/modules:/lib/modules \
        -v /usr/share/fontconfig:/usr/share/fontconfig \
        -v /usr/share/fonts:/usr/share/fonts \
        --dns=114.114.114.114 \
        -e "FATHER_HOST_NAME"=$(hostname) \
        -e "PROXY_PORT"=${PROXY_PORT} \
        -e "PROXY_IP"=${PROXY_IP} \
        -e "PROXY_TJ_IP"=${PROXY_TJ_IP} \
        -p ${PROXY_PORT}:${PROXY_PORT} \
        -p ${HTTP_PORT}:${HTTP_PORT} \
        ${IMG_NAME}:${IMG_VERSION} /usr/bin/supervisord
}

if [ x$1 = xdev ]
then
    docker_run_dev
else
    docker_run
fi
