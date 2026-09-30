#!/bin/bash
# Thermal monitor watchdog for NVIDIA GPU

echo "Starting GPU Thermal Monitor..."
echo "Press Ctrl+C to stop."
echo "----------------------------------------"

# Use watch to refresh nvidia-smi every 1 second
watch -n 1 'nvidia-smi --query-gpu=temperature.gpu,power.draw,utilization.gpu,memory.used --format=csv,noheader | awk "{print \"Temp: \"\$1\"°C | Power: \"\$2\" W | Util: \"\$3\"% | VRAM: \"\$4\" MiB\"}"'
