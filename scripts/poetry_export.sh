#!/bin/bash -l

# Exit on any error
set -e

# Default output path
OUTPUT_FILE="requirements.txt"

# Parse arguments
while getopts "o:" opt; do
    case $opt in
        o) OUTPUT_FILE="$OPTARG";;
        *) echo "Usage: $0 [-o output_file]" >&2; exit 1;;
    esac
done

# Ensure Python environment is properly set up
command -v python3 >/dev/null 2>&1 || { echo "Python3 is required but not installed. Aborting." >&2; exit 1; }

# Export requirements using the Python script
echo "Exporting requirements to $OUTPUT_FILE..."
python3 export_requirements.py --output_file "$OUTPUT_FILE" || { echo "Failed to export requirements. Aborting." >&2; exit 1; }

echo "Successfully exported requirements to $OUTPUT_FILE"
