#!/usr/bin/env bash
set -e
export PYTHONPATH="services/ai:."
python scripts/simulate_all.py
