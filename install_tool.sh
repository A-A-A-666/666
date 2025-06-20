#!/bin/bash

# This script attempts to install a given tool using various package managers and methods.
# It requires root or sudo privileges for system-level installations.

TOOL_NAME="$1"
INSTALL_SUCCESS=1 # 1 for failure, 0 for success

echo "--- Installation Script Output for $TOOL_NAME ---"
echo "Checking if $TOOL_NAME is already installed..."

# 1. Check if already installed
if command -v "$TOOL_NAME" &> /dev/null; then
    echo "$TOOL_NAME is already in PATH."
    INSTALL_SUCCESS=0
else
    echo "$TOOL_NAME not found. Attempting installation."

    # Function to check if a command exists
    command_exists () {
        command -v "$1" &> /dev/null
    }

    # Function to attempt package manager installation
    install_with_package_manager () {
        local pkg_manager_cmd="$1"
        local install_cmd="$2"
        local pkg_name="$3" # Allow different package name if needed, defaults to tool_name
        [ -z "$pkg_name" ] && pkg_name="$TOOL_NAME"

        if command_exists sudo && command_exists "$pkg_manager_cmd"; then
            echo "Attempting sudo $pkg_manager_cmd $install_cmd $pkg_name..."
            sudo "$pkg_manager_cmd" "$install_cmd" "$pkg_name"
            # Check installation command result AND if the tool is now in PATH
            if [ $? -eq 0 ] && command_exists "$TOOL_NAME"; then
                echo "$TOOL_NAME installed successfully via $pkg_manager_cmd."
                return 0 # Success
            else
                echo "Installation command via $pkg_manager_cmd finished, but $TOOL_NAME not found in PATH or command failed."
                return 1 # Failure
            fi
        else
            #echo "Package manager $pkg_manager_cmd or sudo not found."
            return 1 # Package manager or sudo not found
        fi
    }

    # Function to install via pip (for sherlock)
    install_pip () {
        if [ "$TOOL_NAME" == "sherlock" ]; then
            echo "Attempting pip install $TOOL_NAME..."
            if command_exists pip; then
                pip install --break-system-packages "$TOOL_NAME" # Use --break-system-packages for venv-less installs
                return $?
            elif command_exists pip3; then
                 pip3 install --break-system-packages "$TOOL_NAME" # Use --break-system-packages
                 return $?
            else
                 echo "pip or pip3 command not found."
                 return 1
            fi
        fi
        return 1 # Not sherlock
    }

    # Function to install via gem (for wpscan)
    install_gem () {
         if [ "$TOOL_NAME" == "wpscan" ]; then
            echo "Attempting gem install $TOOL_NAME..."
            if command_exists gem; then
                gem install "$TOOL_NAME"
                return $?
            else
                echo "gem command not found."
                return 1
            fi
        fi
        return 1 # Not wpscan
    }

    # --- Attempt installations in order ---
    # Update package lists first for apt, yum/dnf
    if command_exists sudo; then
      if command_exists apt; then sudo apt update; fi
      if command_exists yum; then sudo yum check-update; fi # Check, no install needed yet
      if command_exists dnf; then sudo dnf check-update; fi # Check, no install needed yet
    fi


    if install_with_package_manager "apt" "install -y"; then
        INSTALL_SUCCESS=0
    elif install_with_package_manager "yum" "install -y"; then
        INSTALL_SUCCESS=0
    elif install_with_package_manager "dnf" "install -y"; then
         INSTALL_SUCCESS=0
    elif install_with_package_manager "pacman" "-Sy --noconfirm"; then
        INSTALL_SUCCESS=0
    elif install_pip; then # Specific tools via pip
        # Verify if tool is now in PATH after pip install
        if command_exists "$TOOL_NAME"; then
            INSTALL_SUCCESS=0
        else
            echo "pip install completed, but $TOOL_NAME command not found in PATH."
            INSTALL_SUCCESS=1
        fi
    elif install_gem; then # Specific tools via gem
         # Verify if tool is now in PATH after gem install (might require re-login or specific gem path config)
        if command_exists "$TOOL_NAME"; then
            INSTALL_SUCCESS=0
        else
            echo "gem install completed, but $TOOL_NAME command not found in PATH. You may need to configure your GEM_PATH."
            INSTALL_SUCCESS=1
        fi
    else
        echo "Failed to install $TOOL_NAME using known package managers (apt, yum/dnf, pacman) or specific installers (pip, gem)."
        INSTALL_SUCCESS=1
    fi

fi # End of 'if command_exists' block

echo "--- End Installation Script Output ---"

# Final exit status based on overall success
exit $INSTALL_SUCCESS
