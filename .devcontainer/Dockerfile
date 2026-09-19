FROM osrf/ros:jazzy-desktop-full

ENV DEBIAN_FRONTEND=noninteractive

# 1. Base tools, X11/VNC fallback, build accelerators, and Foxglove Bridge
RUN apt-get update && apt-get install -y --no-install-recommends \
    software-properties-common \
    && add-apt-repository universe \
    && apt-get update && apt-get install -y --no-install-recommends \
    bash-completion \
    build-essential \
    ccache \
    cmake \
    curl \
    dbus-x11 \
    git \
    iputils-ping \
    libgl1 \
    libgl1-mesa-dri \
    libglx-mesa0 \
    mesa-utils \
    net-tools \
    novnc \
    openbox \
    python3-colcon-common-extensions \
    python3-pip \
    python3-rosdep \
    ros-dev-tools \
    ros-jazzy-foxglove-bridge \
    sudo \
    supervisor \
    tigervnc-standalone-server \
    tigervnc-tools \
    websockify \
    wget \
    x11-xserver-utils \
    xauth \
    xfonts-base \
    && rm -rf /var/lib/apt/lists/*

# 2. Install Node.js 22 LTS (Dashboard)
RUN curl -fsSL https://deb.nodesource.com/setup_22.x | bash - \
    && apt-get install -y nodejs \
    && rm -rf /var/lib/apt/lists/*

ENV PIP_BREAK_SYSTEM_PACKAGES=1

# 3. Configure ccache for high-speed rebuilding
ENV PATH="/usr/lib/ccache:$PATH"
ENV CCACHE_DIR="/workspace/.ccache"

# 4. User Configuration: Setup 'rover' and remove Ubuntu 24.04 UID 1000 conflict
ARG USERNAME=rover
ARG USER_UID=1000
ARG USER_GID=$USER_UID

RUN if getent passwd $USER_UID >/dev/null 2>&1; then \
        userdel -f -r $(getent passwd $USER_UID | cut -d: -f1) || true; \
    fi \
    && if getent group $USER_GID >/dev/null 2>&1; then \
        groupdel $(getent group $USER_GID | cut -d: -f1) || true; \
    fi \
    && groupadd --gid $USER_GID $USERNAME \
    && useradd --uid $USER_UID --gid $USER_GID -m -s /bin/bash $USERNAME \
    && echo "$USERNAME ALL=(ALL) NOPASSWD:ALL" > /etc/sudoers.d/$USERNAME \
    && chmod 0440 /etc/sudoers.d/$USERNAME

# 5. Native Xvnc Display Pipeline (Mac/Browser fallback)
RUN ln -sf /usr/share/novnc/vnc.html /usr/share/novnc/index.html \
    && echo "[supervisord]" > /etc/supervisor/conf.d/supervisord.conf \
    && echo "nodaemon=false" >> /etc/supervisor/conf.d/supervisord.conf \
    && echo "user=root" >> /etc/supervisor/conf.d/supervisord.conf \
    && echo "" >> /etc/supervisor/conf.d/supervisord.conf \
    && echo "[program:xvnc]" >> /etc/supervisor/conf.d/supervisord.conf \
    && echo "command=/usr/bin/Xvnc :1 -geometry 1920x1080 -depth 24 -rfbport 5901 -SecurityTypes None -pn" >> /etc/supervisor/conf.d/supervisord.conf \
    && echo "user=$USERNAME" >> /etc/supervisor/conf.d/supervisord.conf \
    && echo "autorestart=true" >> /etc/supervisor/conf.d/supervisord.conf \
    && echo "priority=100" >> /etc/supervisor/conf.d/supervisord.conf \
    && echo "" >> /etc/supervisor/conf.d/supervisord.conf \
    && echo "[program:openbox]" >> /etc/supervisor/conf.d/supervisord.conf \
    && echo "command=/bin/bash -c 'sleep 1 && exec openbox-session'" >> /etc/supervisor/conf.d/supervisord.conf \
    && echo "environment=DISPLAY=\":1\",USER=\"$USERNAME\",HOME=\"/home/$USERNAME\"" >> /etc/supervisor/conf.d/supervisord.conf \
    && echo "user=$USERNAME" >> /etc/supervisor/conf.d/supervisord.conf \
    && echo "autorestart=true" >> /etc/supervisor/conf.d/supervisord.conf \
    && echo "priority=150" >> /etc/supervisor/conf.d/supervisord.conf \
    && echo "" >> /etc/supervisor/conf.d/supervisord.conf \
    && echo "[program:novnc]" >> /etc/supervisor/conf.d/supervisord.conf \
    && echo "command=/usr/bin/websockify --web /usr/share/novnc 0.0.0.0:6080 127.0.0.1:5901" >> /etc/supervisor/conf.d/supervisord.conf \
    && echo "user=$USERNAME" >> /etc/supervisor/conf.d/supervisord.conf \
    && echo "autorestart=true" >> /etc/supervisor/conf.d/supervisord.conf \
    && echo "priority=200" >> /etc/supervisor/conf.d/supervisord.conf

# 6. Desktop Initialization Script (Cleans stale locks & fixes volume ownership on container boot)
RUN echo '#!/bin/bash' > /usr/local/bin/init-desktop.sh \
    && echo 'rm -f /tmp/.X1-lock /tmp/.X11-unix/X1' >> /usr/local/bin/init-desktop.sh \
    && echo 'mkdir -p /tmp/.X11-unix' >> /usr/local/bin/init-desktop.sh \
    && echo 'chmod 1777 /tmp/.X11-unix' >> /usr/local/bin/init-desktop.sh \
    && echo 'mkdir -p /workspace/build /workspace/install /workspace/log /workspace/.ccache' >> /usr/local/bin/init-desktop.sh \
    && echo 'chown -R rover:rover /workspace/build /workspace/install /workspace/log /workspace/.ccache' >> /usr/local/bin/init-desktop.sh \
    && echo 'if ! pgrep -x "supervisord" > /dev/null; then' >> /usr/local/bin/init-desktop.sh \
    && echo '    /usr/bin/supervisord -c /etc/supervisor/conf.d/supervisord.conf' >> /usr/local/bin/init-desktop.sh \
    && echo 'else' >> /usr/local/bin/init-desktop.sh \
    && echo '    /usr/bin/supervisorctl -c /etc/supervisor/conf.d/supervisord.conf restart all' >> /usr/local/bin/init-desktop.sh \
    && echo 'fi' >> /usr/local/bin/init-desktop.sh \
    && chmod +x /usr/local/bin/init-desktop.sh

# 7. Environment Auto-Sourcing
RUN echo "source /opt/ros/jazzy/setup.bash" >> /home/$USERNAME/.bashrc \
    && echo "if [ -f /workspace/install/setup.bash ]; then source /workspace/install/setup.bash; fi" >> /home/$USERNAME/.bashrc

ENV LIBGL_ALWAYS_SOFTWARE=0
ENV MESA_GL_VERSION_OVERRIDE=3.3

WORKDIR /workspace
USER $USERNAME

# Expose Foxglove (8765), noVNC (6080), and Web Dashboard (3000, 5173)
EXPOSE 8765 6080 3000 5173
