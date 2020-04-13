FROM ubuntu:18.04

RUN apt-get update && apt-get install -y \
    openssh-server \
    tmux \
    emacs \
    emacs-goodies.el \
    curl \
    git \
    python3 \
    python3-pip \
    python3-virtualenv \
    python3-dev \
    build-essential \
    locales \
    wget \
    unzip \
    htop

# From https://pythonspeed.com/articles/activate-virtualenv-dockerfile/
ENV VIRTUAL_ENV=/opt/venv
RUN python3 -m virtualenv --python=/usr/bin/python3 $VIRTUAL_ENV
ENV PATH="$VIRTUAL_ENV/bin:$PATH"
RUN pip install --upgrade pip setuptools wheel && \
    pip install lxml && \
    pip install elpy jedi rope yapf importmagic flake8 autopep8 black

RUN cd /root/ && \
    git clone https://github.com/RePierre/.emacs.d.git .emacs.d && \
    echo "(setq package-check-signature nil)" >> ./.emacs.d/config.el && \
    sed -i '/^.*emacs-init.*$/d' ./.emacs.d/init.el && \
    sed -i 's/(shell . t)/(sh . t)/' ./.emacs.d/common-config.org && \
    sed -i '/^.*org-config.*$/d' ./.emacs.d/init.el && \
    sed -i 's/\:defer\ t//' ./.emacs.d/python-config.org && \
    sed -i '/^.*emacs-init.*$/d' ./.emacs.d/init.el && \
    echo "(setq elpy-rpc-virtualenv-path \"$VIRTUAL_ENV\") (pyvenv-activate \"$VIRTUAL_ENV\")" >> ./.emacs.d/after-init.el

RUN emacs --daemon

# Set terminal colors https://stackoverflow.com/a/64585/844006
ENV TERM=xterm-256color

# https://serverfault.com/a/689947
RUN sed -i -e 's/# en_US.UTF-8 UTF-8/en_US.UTF-8 UTF-8/' /etc/locale.gen && \
    sed -i -e 's/# ro_RO.UTF-8 UTF-8/ro_RO.UTF-8 UTF-8/' /etc/locale.gen && \
    echo 'LANG="en_US.UTF-8"'>/etc/default/locale && \
    dpkg-reconfigure --frontend=noninteractive locales && \
    update-locale LANG=en_US.UTF-8

# http://jaredmarkell.com/docker-and-locales/
ENV LANG en_US.UTF-8
ENV LANGUAGE en_US:en
ENV LC_ALL en_US.UTF-8

ARG password

RUN mkdir /var/run/sshd
RUN echo "root:${password}" | chpasswd
RUN sed -i 's/#PermitRootLogin prohibit-password/PermitRootLogin yes/' /etc/ssh/sshd_config

# SSH login fix. Otherwise user is kicked off after login
RUN sed 's@session\s*required\s*pam_loginuid.so@session optional pam_loginuid.so@g' -i /etc/pam.d/sshd

ENV NOTVISIBLE "in users profile"
RUN echo "export VISIBLE=now" >> /etc/profile

EXPOSE 22
CMD ["/usr/sbin/sshd", "-D"]
