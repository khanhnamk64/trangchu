"""
app.py – Flask backend cho VRP Visualizer (fixed)
Chạy: python app.py
Sau đó mở: http://localhost:5000
"""
import json
import os
import subprocess
import sys
from pathlib import Path
from flask import Flask, jsonify, send_from_directory, request

app = Flask(__name__, static_folder="web")

BASE_DIR    = Path(__file__).parent.resolve()
RESULT_FILE = BASE_DIR / "result.json"
CVRP_FILE   = BASE_DIR / "CVRP.json"
EXE_NAME    = "alns_vrp.exe" if sys.platform == "win32" else "alns_vrp"
EXE_PATH    = BASE_DIR / EXE_NAME

SRC_FILES = [
    "src/main.cpp",
    "src/data_structures.cpp",
    "src/repair_operators.cpp",
    "src/alns_control.cpp",
]
INCLUDE_DIR = "include"

@app.route("/")
def index():
    return send_from_directory("web", "index.html")

@app.route("/api/result")
def get_result():
    if not RESULT_FILE.exists():
        return jsonify({"error": "Chua co result.json. Nhan nut Run Solver."}), 404
    with open(RESULT_FILE, encoding="utf-8") as f:
        return jsonify(json.load(f))

@app.route("/api/instance")
def get_instance():
    if not CVRP_FILE.exists():
        return jsonify({"error": "CVRP.json khong tim thay."}), 404
    with open(CVRP_FILE, encoding="utf-8") as f:
        return jsonify(json.load(f))

@app.route("/api/run", methods=["POST"])
def run_solver():
    # Bước 1: Compile
    compile_result = _compile()
    if compile_result["returncode"] != 0:
        return jsonify({
            "success": False,
            "step": "compile",
            "error": compile_result["stderr"] or "Compile that bai",
            "cmd": compile_result["cmd"]
        }), 500

    # Bước 2: Chạy exe
    if not EXE_PATH.exists():
        return jsonify({
            "success": False,
            "step": "run",
            "error": f"Khong tim thay {EXE_NAME} sau khi compile"
        }), 500

    try:
        run_result = subprocess.run(
            [EXE_NAME, "-i", CVRP_FILE.name, "-o", RESULT_FILE.name],
            capture_output=True,
            text=True,
            timeout=120,
            cwd=str(BASE_DIR)
        )
        if False: #
            return jsonify({
                "success": False,
                "step": "run",
                "stdout": run_result.stdout,
                "stderr": run_result.stderr
            }), 500

        return jsonify({
            "success": True,
            "stdout": run_result.stdout,
            "stderr": run_result.stderr
        })

    except subprocess.TimeoutExpired:
        return jsonify({"success": False, "error": "Timeout >120s"}), 500
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/api/compile", methods=["POST"])
def compile_only():
    result = _compile()
    return jsonify(result), 200 if result["returncode"] == 0 else 500

def _compile():
    cmd = [
        "g++", "-std=c++17", "-O2",
        *SRC_FILES,
        "-I", INCLUDE_DIR,
        "-o", EXE_NAME
    ]
    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True,
            timeout=60, cwd=str(BASE_DIR)
        )
        return {
            "returncode": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "cmd": " ".join(cmd)
        }
    except FileNotFoundError:
        return {
            "returncode": -1, "stdout": "",
            "stderr": "g++ khong tim thay. Hay cai: scoop install mingw",
            "cmd": " ".join(cmd)
        }
    except subprocess.TimeoutExpired:
        return {"returncode": -1, "stdout": "", "stderr": "Compile timeout", "cmd": " ".join(cmd)}

if __name__ == "__main__":
    print("=" * 50)
    print(f"  BASE_DIR : {BASE_DIR}")
    print(f"  EXE_PATH : {EXE_PATH}")
    print(f"  CVRP     : {CVRP_FILE}")
    print("=" * 50)
    print("  VRP Visualizer  ->  http://localhost:5001")
    print("=" * 50)
    app.run(debug=True, port=5001)
