FROM python:3.9-slim

ENV DISPLAY=:99 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install Chrome and VNC dependencies
# Update package lists
RUN apt-get update

# Install basic dependencies
RUN apt-get install -y --no-install-recommends \
    wget \
    gnupg2 \
    ca-certificates

# Install X11 and VNC components
RUN apt-get install -y --no-install-recommends \
    xvfb \
    x11vnc \
    novnc \
    websockify

# Install window manager and terminal
RUN apt-get install -y --no-install-recommends \
    fluxbox \
    xterm

# Install font and UI libraries
RUN apt-get install -y --no-install-recommends \
    fonts-liberation \
    libappindicator3-1 \
    libasound2 \
    libatk-bridge2.0-0 \
    libatspi2.0-0 \
    libgtk-3-0 \
    libnspr4 \
    libnss3 \
    libx11-xcb1 \
    libxcb-dri3-0 \
    libxcomposite1 \
    libxcursor1 \
    libxdamage1 \
    libxi6 \
    libxrandr2 \
    libxtst6 \
    lsb-release \
    xdg-utils


# Install Chrome

# Add Chrome repository and install Chrome and ChromeDriver
RUN wget -qO- https://dl.google.com/linux/linux_signing_key.pub | gpg --dearmor -o /usr/share/keyrings/google-chrome-keyring.gpg && \
    echo "deb [arch=amd64 signed-by=/usr/share/keyrings/google-chrome-keyring.gpg] https://dl.google.com/linux/chrome/deb/ stable main" > /etc/apt/sources.list.d/google-chrome.list && \
    apt-get update && \
    apt-get install -y --no-install-recommends \
    google-chrome-stable \
    chromium-driver && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Final cleanup
RUN apt-get clean && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /code
COPY . /code/

RUN pip install --upgrade pip && \
    pip install -r requirements.txt

RUN mkdir /code/screenshots

EXPOSE 8080 5900

CMD ["sh", "-c", \
    "Xvfb :99 -screen 0 1280x820x24 -ac +extension GLX +render -noreset & \
    fluxbox & \
    x11vnc -display :99 -forever -shared -noxdamage -passwd ${VNC_PASSWORD} & \
    websockify -D --web /usr/share/novnc 8080 localhost:5900 & python database_setup.py && python main.py"]
# CMD ["sh", "-c", \
#     "Xvfb :99 -screen 0 1280x820x24 -ac +extension GLX +render -noreset & \
#     fluxbox & \
#     x11vnc -display :99 -forever -shared -noxdamage -passwd ${VNC_PASSWORD} & \
#     websockify -D --web /usr/share/novnc 8080 localhost:5900 & python database_setup.py && while true; do sleep 30; done;"]