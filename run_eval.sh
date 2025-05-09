#!/bin/bash

echo "📂 Evaluation Setup"

read -p "Enter path to the directory: " directory
while [[ ! -d "$directory" ]]; do
  echo "❌ Directory not found: $directory"
  read -p "Please enter a valid path to a directory: " directory
done

echo "✅ Running evaluation..."
uv run python3 evaluate_estimations.py "$directory"