#!/bin/bash

# Generate a timestamp (e.g., 2025-07-15)
today=$(date '+%Y-%m-%d')

# Define the log file path using that date
log_file="/home/hli47/logs/Postprocess_MosaicClipExport_${today}.log"

# Write the trigger time into the new log file
echo "[Cron Triggered] $(date '+%Y-%m-%d %H:%M:%S')" >> "$log_file"

# Activate conda and run your program
# Load Conda (needed for non-login shells like cron)
source /home/hli47/anaconda3/etc/profile.d/conda.sh

# Activate the env
conda activate AutomatedMapping

# Run the script with full Python path
/home/hli47/anaconda3/envs/AutomatedMapping/bin/python3.13 /home/hli47/InseasonMapping/Code/Postprocess_MosaicClipExport.py >> "$log_file" 2>&1
