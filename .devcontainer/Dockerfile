FROM ros:jazzy-ros-base

ENV DEBIAN_FRONTEND=noninteractive

# Base tools, X11/VNC fallback, build accelerators, and utilities
RUN apt-get update && apt-get install -y --no-install-recommends \
    software-properties-common \
    && add-apt-repository universe \
    && apt-get update && apt-get install -y --no-install-recommends \
    ros-jazzy-desktop-full \
    fonts-dejavu \
    fonts-liberation \
    libxcb-cursor0 \
    libxcb-xinerama0 \
    qt6-qpa-plugins \
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
    x11-utils \
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

# User Configuration: Setup 'rover' and handle Ubuntu 24.04 UID 1000 conflict
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

# Create writable X11 directory and link host X0 from staging mount
RUN mkdir -p /tmp/.X11-unix /tmp/.X11-unix-host \
    && ln -sf /tmp/.X11-unix-host/X0 /tmp/.X11-unix/X0 \
    && chmod 1777 /tmp/.X11-unix

# Native Xvnc Display Pipeline (Mac/Browser fallback on DISPLAY=:1)
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

# Intelligent Display & GPU Detection Script
RUN echo '#!/bin/bash' > /etc/profile.d/00-display-detect.sh \
    && echo '# Timeout after 1 second if :0 is unresponsive (prevents Mac hangs)' >> /etc/profile.d/00-display-detect.sh \
    && echo 'if timeout 1s xdpyinfo -display :0 >/dev/null 2>&1; then' >> /etc/profile.d/00-display-detect.sh \
    && echo '    export DISPLAY=:0' >> /etc/profile.d/00-display-detect.sh \
    && echo 'else' >> /etc/profile.d/00-display-detect.sh \
    && echo '    # Fallback to internal noVNC/Openbox session (macOS / Headless)' >> /etc/profile.d/00-display-detect.sh \
    && echo '    export DISPLAY=:1' >> /etc/profile.d/00-display-detect.sh \
    && echo 'fi' >> /etc/profile.d/00-display-detect.sh \
    && echo 'export QT_QPA_PLATFORM=xcb' >> /etc/profile.d/00-display-detect.sh \
    && echo 'export LIBGL_DRI3_DISABLE=1' >> /etc/profile.d/00-display-detect.sh \
    && echo 'if [ ! -e /dev/dri ] && [ ! -d /usr/lib/wsl ]; then' >> /etc/profile.d/00-display-detect.sh \
    && echo '    export LIBGL_ALWAYS_SOFTWARE=1' >> /etc/profile.d/00-display-detect.sh \
    && echo 'fi' >> /etc/profile.d/00-display-detect.sh \
    && echo 'export XDG_RUNTIME_DIR=/tmp/runtime-${USER:-rover}' >> /etc/profile.d/00-display-detect.sh \
    && echo 'mkdir -p $XDG_RUNTIME_DIR && chmod 0700 $XDG_RUNTIME_DIR' >> /etc/profile.d/00-display-detect.sh \
    && chmod +x /etc/profile.d/00-display-detect.sh

# Desktop Initialization Script (Cleans stale locks & starts supervisor)
RUN echo '#!/bin/bash' > /usr/local/bin/init-desktop.sh \
    && echo 'mkdir -p /tmp/.X11-unix /workspace/build /workspace/install /workspace/log /workspace/.ccache' >> /usr/local/bin/init-desktop.sh \
    && echo 'chmod 1777 /tmp/.X11-unix' >> /usr/local/bin/init-desktop.sh \
    && echo '# Restore symlink to host WSLg X0 if available' >> /usr/local/bin/init-desktop.sh \
    && echo 'if [ -S /tmp/.X11-unix-host/X0 ] && [ ! -e /tmp/.X11-unix/X0 ]; then' >> /usr/local/bin/init-desktop.sh \
    && echo '    ln -sf /tmp/.X11-unix-host/X0 /tmp/.X11-unix/X0' >> /usr/local/bin/init-desktop.sh \
    && echo 'fi' >> /usr/local/bin/init-desktop.sh \
    && echo 'rm -f /tmp/.X1-lock /tmp/.X11-unix/X1' >> /usr/local/bin/init-desktop.sh \
    && echo 'chown -R rover:rover /workspace/build /workspace/install /workspace/log /workspace/.ccache' >> /usr/local/bin/init-desktop.sh \
    && echo 'if ! pgrep -x "supervisord" > /dev/null; then' >> /usr/local/bin/init-desktop.sh \
    && echo '    /usr/bin/supervisord -c /etc/supervisor/conf.d/supervisord.conf' >> /usr/local/bin/init-desktop.sh \
    && echo 'else' >> /usr/local/bin/init-desktop.sh \
    && echo '    /usr/bin/supervisorctl -c /etc/supervisor/conf.d/supervisord.conf restart all' >> /usr/local/bin/init-desktop.sh \
    && echo 'fi' >> /usr/local/bin/init-desktop.sh \
    && chmod +x /usr/local/bin/init-desktop.sh

# 8. Environment Auto-Sourcing
RUN echo "source /etc/profile.d/00-display-detect.sh" >> /home/$USERNAME/.bashrc \
    && echo "source /opt/ros/jazzy/setup.bash" >> /home/$USERNAME/.bashrc \
    && echo "if [ -f /workspace/install/setup.bash ]; then source /workspace/install/setup.bash; fi" >> /home/$USERNAME/.bashrc

WORKDIR /workspace
USER $USERNAME

# Expose Foxglove (8765), noVNC (6080), and Web Dashboard (3000, 5173)
EXPOSE 8765 6080 3000 5173
