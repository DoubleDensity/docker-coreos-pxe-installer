FROM debian

MAINTAINER Quanlong He <kyan.ql.he@gmail.com>

# Install deps
RUN apt-get update
RUN apt-get install -y \ 
    net-tools \
    dnsmasq \
    syslinux \
    wget \
    python3-systemd \
    python3-pip \
    python3-dev \
    gawk \
    iptables

RUN pip3 install RandomWords --no-compile

COPY app /app

# Install pxelinux.0
WORKDIR /tmp
RUN wget http://ftp.debian.org/debian/dists/jessie/main/installer-amd64/current/images/netboot/netboot.tar.gz
RUN tar zxvf netboot.tar.gz
RUN mkdir /app/tftp && cp /tmp/debian-installer/amd64/pxelinux.0 /app/tftp && cp /tmp/debian-installer/amd64/boot-screens/ldlinux.c32 /app/tftp

# Install coreos pxe images
WORKDIR /app/tftp
RUN wget -q http://stable.release.core-os.net/amd64-usr/current/coreos_production_pxe.vmlinuz
RUN wget -q http://stable.release.core-os.net/amd64-usr/current/coreos_production_pxe_image.cpio.gz

# RUN chmod 644 pxe/pxelinux.cfg/default && \
ENV ETCS=3

# Customizations
ENV INTERFACE=eno1

CMD /app/init
