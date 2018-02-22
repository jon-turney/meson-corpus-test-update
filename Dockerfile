FROM ubuntu:artful

# uncomment source URIs in sources.lst so metadata required by 'apt-get build-dep' is present
RUN sed -i '/^#\sdeb-src /s/^#\s//' /etc/apt/sources.list \
&& apt-get -y update \
&& apt-get -y upgrade \
&& apt-get -y install build-essential pkg-config ninja-build python3-pip git