#!/bin/bash

# upload your project (e.g., main.py auto-runs on boot)
mpremote connect auto fs cp embed/main.py :

# soft reset to run it
mpremote connect auto reset
