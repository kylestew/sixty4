```bash
pip install mpremote

# list files
mpremote connect auto fs ls

# upload your project (e.g., main.py auto-runs on boot)
mpremote connect auto fs cp main.py :

# soft reset to run it
mpremote connect auto reset
```
