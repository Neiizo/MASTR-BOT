# server.py
from flask import Flask, request, jsonify
from flask_cors import CORS
import subprocess

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes


@app.route("/run-python-script", methods=["POST"])
def run_python_script():
    try:
        data = request.json
        python_args = data.get("args", [])
        print("Running python script with args:", python_args)
        result = subprocess.run(
            python_args,
            capture_output=True,
            text=True,
        )
        return jsonify(
            {
                "stdout": result.stdout,
                "stderr": result.stderr,
                "returncode": result.returncode,
            }
        )
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
