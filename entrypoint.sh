#!/bin/sh
# Allow commands to fail without exiting immediately for better diagnostics
set +e

# --- Configuration ---
# Default VNC password if not set via environment variable
DEFAULT_VNC_PASSWORD="password"
# Use environment variable VNC_PASSWORD if set, otherwise use default
VNC_PASSWORD="${VNC_PASSWORD:-$DEFAULT_VNC_PASSWORD}"
VNC_PASSWD_FILE="/etc/x11vnc.pass" # Using /etc for config, ensure permissions if needed
# Screen resolution for Xvfb
SCREEN_RESOLUTION="1280x820x24"

# --- Handle potential stale lock files ---
# Clean up any existing lock files for display :99
if [ -f /tmp/.X99-lock ]; then
    echo "Removing stale X lock file /tmp/.X99-lock"
    rm -f /tmp/.X99-lock
fi
if [ -f /tmp/.X11-unix/X99 ]; then
    echo "Removing stale X11 socket /tmp/.X11-unix/X99"
    rm -f /tmp/.X11-unix/X99
fi

# Make sure X11 socket directory exists with correct permissions
mkdir -p /tmp/.X11-unix
chmod 1777 /tmp/.X11-unix

# --- Setup ---
echo "Initializing VNC password..."
# Create the directory if it doesn't exist (should exist, but good practice)
mkdir -p "$(dirname "$VNC_PASSWD_FILE")"
# Store the password securely for x11vnc
x11vnc -storepasswd "${VNC_PASSWORD}" "${VNC_PASSWD_FILE}"
chmod 600 "${VNC_PASSWD_FILE}" # Secure the password file

# --- Start Xvfb with detailed diagnostics ---
echo "Starting Xvfb virtual display on :99..."
# First attempt with logging to help diagnose issues
Xvfb :99 -screen 0 ${SCREEN_RESOLUTION} -ac +extension GLX +render -noreset &
XVFB_PID=$!
echo "Xvfb PID: ${XVFB_PID}"

# Give Xvfb a moment to initialize
sleep 5

# Check if Xvfb process is still running
if ! ps -p $XVFB_PID > /dev/null; then
    echo "ERROR: Xvfb process died. Attempting to start with verbose logging..."
    # Try again with verbose logging to diagnose the problem
    Xvfb :99 -screen 0 ${SCREEN_RESOLUTION} -ac +extension GLX +render -noreset -verbose 5 > /tmp/xvfb.log 2>&1 &
    XVFB_PID=$!
    sleep 5
    
    # Check again and provide diagnostic information
    if ! ps -p $XVFB_PID > /dev/null; then
        echo "ERROR: Xvfb failed to start. Diagnostic information:"
        echo "--- Last 20 lines of Xvfb log ---"
        if [ -f /tmp/xvfb.log ]; then
            tail -20 /tmp/xvfb.log
        else
            echo "No log file was created."
        fi
        echo "--- System information ---"
        echo "Operating system:"
        cat /etc/os-release
        echo "Available memory:"
        free -h
        echo "Disk space:"
        df -h
        echo "--- Attempting fallback configuration ---"
        
        # Try one more time with minimal configuration
        echo "Attempting to start Xvfb with minimal configuration..."
        Xvfb :99 -screen 0 1024x768x16 -nolisten tcp &
        XVFB_PID=$!
        sleep 5
        
        if ! ps -p $XVFB_PID > /dev/null; then
            echo "FATAL ERROR: Could not start Xvfb with any configuration."
            exit 1
        fi
    fi
fi

export DISPLAY=:99

# Verify Xvfb is running properly
echo "Verifying Xvfb is operational..."
if command -v xdpyinfo >/dev/null 2>&1; then
    if ! xdpyinfo -display :99 >/dev/null 2>&1; then
        echo "ERROR: Xvfb is running but not accepting connections."
        exit 1
    else
        echo "Xvfb verified operational."
    fi
else
    echo "xdpyinfo not available, skipping Xvfb verification."
fi

# --- Continue with remaining services if Xvfb is working ---
echo "Starting Fluxbox window manager..."
fluxbox -display :99 &
FLUXBOX_PID=$!
echo "Fluxbox PID: ${FLUXBOX_PID}"
sleep 2

echo "Starting x11vnc server (port 5900)..."
x11vnc -display :99 -forever -shared -noxdamage -rfbauth "${VNC_PASSWD_FILE}" &
X11VNC_PID=$!
echo "x11vnc PID: ${X11VNC_PID}"
sleep 2

# Check if x11vnc started properly
if ! ps -p $X11VNC_PID > /dev/null; then
    echo "WARNING: x11vnc failed to start properly. Attempting to start with different options..."
    x11vnc -display :99 -forever -shared -noxdamage -passwd "${VNC_PASSWORD}" &
    X11VNC_PID=$!
    sleep 2
    
    if ! ps -p $X11VNC_PID > /dev/null; then
        echo "ERROR: Could not start x11vnc. Continuing without VNC support."
    fi
fi

echo "Starting noVNC websockify proxy (port 8080 -> 5900)..."
websockify -D --web /usr/share/novnc 8080 localhost:5900 &
WEBSOCKIFY_PID=$!
echo "Websockify PID: ${WEBSOCKIFY_PID}"

# --- Application Setup and Execution ---
sleep 3

echo "Running database setup (python database_setup.py)..."
python database_setup.py

echo "Starting main application (python main.py)..."
# Use 'exec' to replace the shell process with the python process
exec python main.py
