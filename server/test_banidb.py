import banidb
import json

try:
    res = banidb.shabad(1)
    print(json.dumps(res, indent=2))
except Exception as e:
    print(f"Error: {e}")
