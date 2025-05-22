#!/bin/bash

# run_tests.sh
# Script to discover and run all unit tests for the PyQt Bitcoin Wallet application.

# Get the directory where the script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"

# Ensure the script is effectively running from the project root (`bitcoin_wallet_app`)
cd "$SCRIPT_DIR" || { echo "Failed to navigate to script directory: $SCRIPT_DIR. Exiting."; exit 1; }

echo "Running unit tests from: $PWD"

# Add the current directory (project root) to PYTHONPATH to help Python find the 'app' module
# Also add user site-packages in case dependencies were installed there
USER_SITE_PACKAGES=$(python3 -m site --user-site)
export PYTHONPATH="$PWD:$PYTHONPATH:$USER_SITE_PACKAGES"
echo "PYTHONPATH set to: $PYTHONPATH"


# Check if the 'tests' directory exists
if [ ! -d "tests" ]; then
    echo "Error: 'tests' directory not found in $PWD."
    exit 1
fi

# Discover and run tests in the 'tests' directory
# The -v flag provides verbose output.
python3 -m unittest discover -v tests

# Check the exit code of the unittest command
if [ $? -eq 0 ]; then
    echo "All tests passed successfully."
else
    echo "Some tests failed. Please review the output above."
    # Consider exiting with a non-zero status to indicate failure to CI systems
    # exit 1 
fi
