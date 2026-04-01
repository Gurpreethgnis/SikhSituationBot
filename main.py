import os
import sys

# Ensure server module is discoverable for imports in server/app.py
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), "server"))

from server.app import app

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)
else:
    # Gunicorn uses this when loading main:app
    pass
