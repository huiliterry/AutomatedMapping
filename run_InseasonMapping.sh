#!/bin/bash
echo "[Cron Triggered] $(date)" >> /home/hli47/logs/AutoInseasonMapping.log

# Activate conda and run your program
# Load Conda (needed for non-login shells like cron)
source /home/hli47/anaconda3/etc/profile.d/conda.sh

# Activate the env
conda activate AutomatedMapping

# Run the script with full Python path
/home/hli47/anaconda3/envs/AutomatedMapping/bin/python3.13 /home/hli47/InseasonMapping/Code/AutoInseasonMapping.py >> /home/hli47/logs/AutoInseasonMapping.log 2>&1
