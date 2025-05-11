#!/bin/bash
# Purpose: Run the test_image_matcher.py script with the correct Python path settings

# Get the absolute path of the repo root directory
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../../.." && pwd)"

# Set up the PYTHONPATH to include the correct directories
export PYTHONPATH="$REPO_ROOT:$REPO_ROOT/backend/src"

# Print debug information
echo "Running tests with PYTHONPATH=$PYTHONPATH"
echo "Current directory: $(pwd)"
echo "Repository root: $REPO_ROOT"

# Run the test script
python3 test_image_matcher.py

# Return the exit code of the test script
exit $? 