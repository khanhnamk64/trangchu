#!/usr/bin/env python3
"""
setup_project.py
════════════════
Script tự động dựng toàn bộ dự án VRP – Nearest Insertion.

Cách dùng:
    python setup_project.py             # tạo vào thư mục hiện tại
    python setup_project.py ./my_vrp   # tạo vào thư mục chỉ định
"""
import sys
import os
from pathlib import Path

# ─────────────────────────────────────────────────────────────
#  Nội dung từng file
# ─────────────────────────────────────────────────────────────
FILES = {}

# ══════════════════════════════════════════════════════════════
#  include/data_structures.h
# ══════════════════════════════════════════════════════════════
FILES["include/data_structures.h"] = r"""
#pragma once
#include <vector>
#include <string>
#include <cmath>
#include <cassert>
#include <limits>
#include <stdexcept>
#include <algorithm>

struct Node {
    int    id     = 0;
    double x      = 0.0;
    double y      = 0.0;
    int    demand = 0;
    std::string label;
    bool isDepot() const { return id == 0; }
};

struct Route {
    std::vector<int> path;
    int    load = 0;
    double cost = 0.0;
    bool empty() const { return path.empty(); }
    bool canAccept(int extraDemand, int capacity) const {
        return (load + extraDemand) <= capacity;
    }
    int removeAt(int pos) {
        assert(pos >= 0 && pos < static_cast<int>(path.size()));
        int id = path[pos];
        path.erase(path.begin() + pos);
        return id;
    }
    void insertAt(int pos, int nodeId) {
        assert(pos >= 0 && pos <= static_cast<int>(path.size()));
        path.insert(path.begin() + pos, nodeId);
    }
};

struct Solution {
    std::vector<Route> routes;
    double totalCost    = 0.0;
    int    vehiclesUsed = 0;
    void compact() {
        routes.erase(
            std::remove_if(routes.begin(), routes.end(),
                [](const Route& r){ return r.empty(); }),
            routes.end());
        vehiclesUsed = static_cast<int>(routes.size());
    }
    void recalcTotalCost() {
        totalCost = 0.0;
        for (const auto& r : routes) totalCost += r.cost;
        vehiclesUsed = static_cast<int>(routes.size());
    }
    bool valid() const { return !routes.empty() && totalCost >= 0.0; }
};

class DistanceMatrix {
public:
    DistanceMatrix() = default;
    void build(const std::vector<Node>& nodes) {
        n_ = static_cast<int>(nodes.size());
        if (n_ == 0) throw std::invalid_argument("Node list is empty");
        mat_.assign(n_, std::vector<double>(n_, 0.0));
        for (int i = 0; i < n_; ++i)
            for (int j = i + 1; j < n_; ++j) {
                double dx = nodes[i].x - nodes[j].x;
                double dy = nodes[i].y - nodes[j].y;
                double d  = std::sqrt(dx*dx + dy*dy);
                mat_[i][j] = d; mat_[j][i] = d;
            }
    }
    double operator()(int i, int j) const {
        assert(i>=0&&i<n_&&j>=0&&j<n_); return mat_[i][j];
    }
    double fromDepot(int j) const { return mat_[0][j]; }
    int size() const { return n_; }
private:
    int n_ = 0;
    std::vector<std::vector<double>> mat_;
};

struct Instance {
    std::string       name;
    std::vector<Node> nodes;
    int               numVehicles = 0;
    int               capacity    = 0;
    DistanceMatrix    dist;
    int numCustomers() const { return static_cast<int>(nodes.size()) - 1; }
    const Node& depot() const { return nodes[0]; }
    void buildDistMatrix() { dist.build(nodes); }
    void validate() const {
        if (nodes.empty()) throw std::runtime_error("[Instance] Khong co node nao.");
        if (capacity <= 0) throw std::runtime_error("[Instance] Capacity phai > 0.");
        for (const auto& n : nodes) {
            if (!n.isDepot() && n.demand <= 0)
                throw std::runtime_error("[Instance] Node " + std::to_string(n.id) + " co demand khong hop le.");
            if (!n.isDepot() && n.demand > capacity)
                throw std::runtime_error("[Instance] Node " + std::to_string(n.id) +
                    " co demand (" + std::to_string(n.demand) +
                    ") vuot capacity (" + std::to_string(capacity) + ").");
        }
    }
};
""".lstrip()

# ══════════════════════════════════════════════════════════════
#  include/repair_operators.h
# ══════════════════════════════════════════════════════════════
FILES["include/repair_operators.h"] = r"""
#pragma once
#include "data_structures.h"
#include <utility>
#include <vector>

double calcRouteCost(const Route& route, const DistanceMatrix& dist);
double refreshRouteCost(Route& route, const DistanceMatrix& dist);

int selectNearest(
    const Route&            route,
    const std::vector<int>& unvisited,
    const DistanceMatrix&   dist);

double calcInsertionDelta(
    int nodeK, int insertPos,
    const Route& route,
    const DistanceMatrix& dist);

std::pair<int,double> findCheapestInsertPos(
    int nodeK,
    const Route& route,
    const DistanceMatrix& dist);

Route buildOneRoute(
    std::vector<int>& unvisited,
    const Instance& inst,
    int seedNodeId = -1);

Solution solveNearestInsertion(const Instance& inst);
bool validateSolution(const Solution& sol, const Instance& inst);
""".lstrip()

# ══════════════════════════════════════════════════════════════
#  include/alns_control.h
# ══════════════════════════════════════════════════════════════
FILES["include/alns_control.h"] = r"""
#pragma once
#include "data_structures.h"
#include <string>
#include <ostream>
#include <chrono>

Instance loadInstanceFromJSON(const std::string& filepath);

void writeResultToJSON(
    const std::string& filepath,
    const Solution& sol,
    const Instance& inst,
    double elapsedMs);

void printSolutionReport(
    const Solution& sol,
    const Instance& inst,
    double elapsedMs,
    std::ostream& out = *(std::ostream*)nullptr);

void printBanner();

class Timer {
public:
    Timer() : start_(std::chrono::high_resolution_clock::now()) {}
    void reset() { start_ = std::chrono::high_resolution_clock::now(); }
    double elapsedMs() const {
        auto now = std::chrono::high_resolution_clock::now();
        return std::chrono::duration<double,std::milli>(now - start_).count();
    }
private:
    std::chrono::time_point<std::chrono::high_resolution_clock> start_;
};

struct RunConfig {
    std::string inputFile  = "CVRP.json";
    std::string outputFile = "result.json";
    bool        verbose    = true;
};

RunConfig parseArgs(int argc, char* argv[]);
""".lstrip()

# ══════════════════════════════════════════════════════════════
#  src/data_structures.cpp
# ══════════════════════════════════════════════════════════════
FILES["src/data_structures.cpp"] = r"""
#include "../include/data_structures.h"
#include <iostream>
#include <iomanip>

void debugPrintInstance(const Instance& inst) {
    std::cout << "===== INSTANCE: " << inst.name << " =====\n";
    std::cout << "  Vehicles : " << inst.numVehicles   << "\n";
    std::cout << "  Capacity : " << inst.capacity      << "\n";
    std::cout << "  Customers: " << inst.numCustomers() << "\n\n";
    std::cout << std::fixed << std::setprecision(2);
    for (const auto& n : inst.nodes) {
        std::cout << "    [" << std::setw(3) << n.id << "] "
                  << "(" << std::setw(7) << n.x << ", "
                  << std::setw(7) << n.y << ")  demand="
                  << std::setw(4) << n.demand;
        if (n.isDepot()) std::cout << "  <-- DEPOT";
        std::cout << "\n";
    }
}
""".lstrip()

# ══════════════════════════════════════════════════════════════
#  src/repair_operators.cpp
# ══════════════════════════════════════════════════════════════
FILES["src/repair_operators.cpp"] = r"""
#include "../include/repair_operators.h"
#include <iostream>
#include <iomanip>
#include <algorithm>

double calcRouteCost(const Route& route, const DistanceMatrix& dist) {
    if (route.path.empty()) return 0.0;
    double cost = dist.fromDepot(route.path.front());
    for (int i = 0; i + 1 < static_cast<int>(route.path.size()); ++i)
        cost += dist(route.path[i], route.path[i+1]);
    cost += dist.fromDepot(route.path.back());
    return cost;
}

double refreshRouteCost(Route& route, const DistanceMatrix& dist) {
    route.cost = calcRouteCost(route, dist);
    return route.cost;
}

int selectNearest(const Route& route, const std::vector<int>& unvisited,
                  const DistanceMatrix& dist) {
    if (unvisited.empty()) return -1;
    double bestDist = std::numeric_limits<double>::max();
    int    bestIdx  = 0;
    for (int uk = 0; uk < static_cast<int>(unvisited.size()); ++uk) {
        int k = unvisited[uk];
        double d = dist.fromDepot(k);
        if (d < bestDist) { bestDist = d; bestIdx = uk; }
        for (int i : route.path) {
            d = dist(i, k);
            if (d < bestDist) { bestDist = d; bestIdx = uk; }
        }
    }
    return bestIdx;
}

double calcInsertionDelta(int nodeK, int insertPos,
                          const Route& route, const DistanceMatrix& dist) {
    const auto& p = route.path;
    int n    = static_cast<int>(p.size());
    int nodeI = (insertPos == 0) ? 0 : p[insertPos - 1];
    int nodeJ = (insertPos == n) ? 0 : p[insertPos];
    return dist(nodeI, nodeK) + dist(nodeK, nodeJ) - dist(nodeI, nodeJ);
}

std::pair<int,double> findCheapestInsertPos(int nodeK, const Route& route,
                                             const DistanceMatrix& dist) {
    int    bestPos   = 0;
    double bestDelta = std::numeric_limits<double>::max();
    int n = static_cast<int>(route.path.size());
    for (int pos = 0; pos <= n; ++pos) {
        double delta = calcInsertionDelta(nodeK, pos, route, dist);
        if (delta < bestDelta) { bestDelta = delta; bestPos = pos; }
    }
    return { bestPos, bestDelta };
}

Route buildOneRoute(std::vector<int>& unvisited, const Instance& inst,
                    int seedNodeId) {
    Route route;
    const auto& dist = inst.dist;
    if (seedNodeId == -1) {
        double bestD = std::numeric_limits<double>::max();
        for (int uid : unvisited) {
            double d = dist.fromDepot(uid);
            if (d < bestD) { bestD = d; seedNodeId = uid; }
        }
    }
    {
        auto it = std::find(unvisited.begin(), unvisited.end(), seedNodeId);
        if (it == unvisited.end())
            throw std::runtime_error("[buildOneRoute] Seed node khong tim thay.");
        route.path.push_back(seedNodeId);
        route.load = inst.nodes[seedNodeId].demand;
        unvisited.erase(it);
    }
    bool extended = true;
    while (extended && !unvisited.empty()) {
        extended = false;
        std::vector<int> candidates;
        for (int uid : unvisited)
            if (route.canAccept(inst.nodes[uid].demand, inst.capacity))
                candidates.push_back(uid);
        if (candidates.empty()) break;

        double nearestDist = std::numeric_limits<double>::max();
        int    nearestId   = -1;
        for (int uid : candidates) {
            double d = dist.fromDepot(uid);
            if (d < nearestDist) { nearestDist = d; nearestId = uid; }
            for (int ri : route.path) {
                d = dist(ri, uid);
                if (d < nearestDist) { nearestDist = d; nearestId = uid; }
            }
        }
        if (nearestId == -1) break;

        auto [bestPos, _delta] = findCheapestInsertPos(nearestId, route, dist);
        route.path.insert(route.path.begin() + bestPos, nearestId);
        route.load += inst.nodes[nearestId].demand;
        unvisited.erase(std::find(unvisited.begin(), unvisited.end(), nearestId));
        extended = true;
    }
    refreshRouteCost(route, dist);
    return route;
}

Solution solveNearestInsertion(const Instance& inst) {
    inst.validate();
    Solution sol;
    std::vector<int> unvisited;
    unvisited.reserve(inst.numCustomers());
    for (int i = 1; i < static_cast<int>(inst.nodes.size()); ++i)
        unvisited.push_back(i);

    while (!unvisited.empty()) {
        Route route = buildOneRoute(unvisited, inst, -1);
        if (route.empty()) {
            std::cerr << "[WARN] Route rong, con " << unvisited.size() << " khach.\n";
            break;
        }
        sol.routes.push_back(std::move(route));
    }
    sol.compact();
    sol.recalcTotalCost();
    return sol;
}

bool validateSolution(const Solution& sol, const Instance& inst) {
    bool ok = true;
    std::vector<int> count(inst.nodes.size(), 0);
    for (const auto& r : sol.routes)
        for (int c : r.path) {
            if (c <= 0 || c >= static_cast<int>(inst.nodes.size())) {
                std::cerr << "[VALIDATE] Node id " << c << " out of range.\n"; ok = false;
            } else ++count[c];
        }
    for (int i = 1; i < static_cast<int>(inst.nodes.size()); ++i)
        if (count[i] != 1) {
            std::cerr << "[VALIDATE] Customer " << i << " xuat hien " << count[i] << " lan.\n";
            ok = false;
        }
    for (int r = 0; r < static_cast<int>(sol.routes.size()); ++r) {
        int load = 0;
        for (int c : sol.routes[r].path) load += inst.nodes[c].demand;
        if (load > inst.capacity) {
            std::cerr << "[VALIDATE] Route " << (r+1) << " vuot capacity.\n"; ok = false;
        }
    }
    if (ok) std::cout << "[VALIDATE] Solution hop le. OK\n";
    return ok;
}
""".lstrip()

# ══════════════════════════════════════════════════════════════
#  src/alns_control.cpp
# ══════════════════════════════════════════════════════════════
FILES["src/alns_control.cpp"] = r"""
#include "../include/alns_control.h"
#include "../include/repair_operators.h"
#include "../include/json.hpp"
#include <fstream>
#include <iostream>
#include <iomanip>
#include <stdexcept>
#include <cstring>

using json = nlohmann::json;

Instance loadInstanceFromJSON(const std::string& filepath) {
    std::ifstream f(filepath);
    if (!f.is_open()) throw std::runtime_error("Khong mo duoc file: " + filepath);
    json j; f >> j;
    Instance inst;
    inst.name        = j.value("name", filepath);
    inst.numVehicles = j.at("numVehicles").get<int>();
    inst.capacity    = j.at("capacity").get<int>();
    Node depot; depot.id=0; depot.label="Depot";
    depot.x = j.at("depot").at("x").get<double>();
    depot.y = j.at("depot").at("y").get<double>();
    inst.nodes.push_back(depot);
    for (const auto& c : j.at("customers")) {
        Node n;
        n.id     = c.at("id").get<int>();
        n.x      = c.at("x").get<double>();
        n.y      = c.at("y").get<double>();
        n.demand = c.at("demand").get<int>();
        n.label  = c.value("label", "C" + std::to_string(n.id));
        inst.nodes.push_back(n);
    }
    inst.buildDistMatrix();
    return inst;
}

void writeResultToJSON(const std::string& filepath, const Solution& sol,
                       const Instance& inst, double elapsedMs) {
    json j;
    j["instance"]  = inst.name;
    j["totalCost"] = sol.totalCost;
    j["vehicles"]  = sol.vehiclesUsed;
    j["elapsedMs"] = elapsedMs;
    j["capacity"]  = inst.capacity;

    json nodesArr = json::array();
    for (const auto& n : inst.nodes)
        nodesArr.push_back({{"id",n.id},{"x",n.x},{"y",n.y},
                            {"demand",n.demand},{"label",n.label},
                            {"isDepot",n.isDepot()}});
    j["nodes"] = nodesArr;

    json routesArr = json::array();
    for (int r = 0; r < static_cast<int>(sol.routes.size()); ++r) {
        const auto& route = sol.routes[r];
        json pathArr = json::array(), coordsArr = json::array();
        auto addCoord = [&](int id){
            coordsArr.push_back({{"x",inst.nodes[id].x},{"y",inst.nodes[id].y}});
        };
        pathArr.push_back(0); addCoord(0);
        for (int c : route.path){ pathArr.push_back(c); addCoord(c); }
        pathArr.push_back(0); addCoord(0);
        routesArr.push_back({{"id",r+1},{"path",pathArr},
                              {"customers",route.path},
                              {"load",route.load},{"cost",route.cost},
                              {"coords",coordsArr}});
    }
    j["routes"] = routesArr;
    std::ofstream out(filepath);
    if (!out.is_open()) throw std::runtime_error("Khong ghi duoc: " + filepath);
    out << j.dump(2);
    std::cout << "  -> Da ghi: " << filepath << "\n";
}

void printSolutionReport(const Solution& sol, const Instance& inst,
                         double elapsedMs, std::ostream& out_) {
    std::ostream& out = (&out_ == nullptr) ? std::cout : out_;
    const int W = 60;
    out << std::string(W,'=') << "\n";
    out << "  VRP SOLUTION - " << inst.name << "\n" << std::string(W,'=') << "\n";
    out << std::fixed << std::setprecision(4);
    out << "  Khach hang      : " << inst.numCustomers() << "\n";
    out << "  Xe su dung      : " << sol.vehiclesUsed << " / " << inst.numVehicles << "\n";
    out << "  Tong quang duong: " << sol.totalCost << "\n";
    out << "  Thoi gian       : " << elapsedMs << " ms\n";
    out << std::string(W,'-') << "\n";
    for (int r = 0; r < static_cast<int>(sol.routes.size()); ++r) {
        const auto& route = sol.routes[r];
        out << "  Route " << std::setw(2) << (r+1)
            << " [load=" << std::setw(4) << route.load
            << "/" << inst.capacity
            << " dist=" << std::setw(8) << route.cost << "]:  0";
        for (int c : route.path) out << " -> " << c;
        out << " -> 0\n";
    }
    out << std::string(W,'=') << "\n";
}

void printBanner() {
    std::cout << "\n"
              << "  +----------------------------------------------+\n"
              << "  |  VRP - Nearest Insertion Heuristic v1.0      |\n"
              << "  |  C++17 | Multi-route | Capacity constrained  |\n"
              << "  +----------------------------------------------+\n\n";
}

RunConfig parseArgs(int argc, char* argv[]) {
    RunConfig cfg;
    for (int i = 1; i < argc; ++i) {
        if (std::strcmp(argv[i], "-i") == 0 && i+1 < argc) cfg.inputFile  = argv[++i];
        else if (std::strcmp(argv[i], "-o") == 0 && i+1 < argc) cfg.outputFile = argv[++i];
        else if (std::strcmp(argv[i], "--quiet") == 0) cfg.verbose = false;
    }
    return cfg;
}
""".lstrip()

# ══════════════════════════════════════════════════════════════
#  src/main.cpp
# ══════════════════════════════════════════════════════════════
FILES["src/main.cpp"] = r"""
#include "../include/data_structures.h"
#include "../include/repair_operators.h"
#include "../include/alns_control.h"
#include <iostream>
#include <stdexcept>

int main(int argc, char* argv[]) {
    printBanner();
    RunConfig cfg = parseArgs(argc, argv);
    try {
        std::cout << "  [1/4] Doc du lieu: " << cfg.inputFile << " ...\n";
        Instance inst = loadInstanceFromJSON(cfg.inputFile);
        if (cfg.verbose) {
            std::cout << "       Instance : " << inst.name          << "\n";
            std::cout << "       Customers: " << inst.numCustomers() << "\n";
            std::cout << "       Vehicles : " << inst.numVehicles   << "\n";
            std::cout << "       Capacity : " << inst.capacity      << "\n\n";
        }
        std::cout << "  [2/4] Chay Nearest Insertion ...\n";
        Timer timer;
        Solution sol = solveNearestInsertion(inst);
        double elapsed = timer.elapsedMs();

        std::cout << "  [3/4] Kiem tra tinh hop le ...\n  ";
        validateSolution(sol, inst);

        std::cout << "  [4/4] Ghi ket qua ...\n";
        writeResultToJSON(cfg.outputFile, sol, inst, elapsed);

        if (cfg.verbose) {
            std::cout << "\n";
            printSolutionReport(sol, inst, elapsed);
        }
    } catch (const std::exception& e) {
        std::cerr << "\n  [LOI] " << e.what() << "\n";
        return EXIT_FAILURE;
    }
    std::cout << "\n  Hoan thanh! Mo trinh duyet va chay:\n    python app.py\n\n";
    return EXIT_SUCCESS;
}
""".lstrip()

# ══════════════════════════════════════════════════════════════
#  CVRP.json
# ══════════════════════════════════════════════════════════════
FILES["CVRP.json"] = r"""
{
  "name": "VRP-10",
  "numVehicles": 3,
  "capacity": 50,
  "depot": { "x": 0.0, "y": 0.0 },
  "customers": [
    { "id": 1,  "x":  2.5, "y":  3.1, "demand": 10, "label": "C01" },
    { "id": 2,  "x":  5.0, "y":  1.2, "demand": 15, "label": "C02" },
    { "id": 3,  "x":  7.3, "y":  8.4, "demand": 20, "label": "C03" },
    { "id": 4,  "x":  1.1, "y":  6.0, "demand":  8, "label": "C04" },
    { "id": 5,  "x":  9.0, "y":  2.5, "demand": 12, "label": "C05" },
    { "id": 6,  "x":  3.7, "y":  9.2, "demand": 18, "label": "C06" },
    { "id": 7,  "x":  6.1, "y":  4.8, "demand":  9, "label": "C07" },
    { "id": 8,  "x":  8.5, "y":  6.3, "demand": 25, "label": "C08" },
    { "id": 9,  "x":  4.4, "y":  2.0, "demand": 14, "label": "C09" },
    { "id": 10, "x":  0.9, "y":  8.7, "demand":  7, "label": "C10" }
  ]
}
""".lstrip()

# ══════════════════════════════════════════════════════════════
#  app.py (Flask)
# ══════════════════════════════════════════════════════════════
FILES["app.py"] = r"""
import json, os, subprocess, sys
from pathlib import Path
from flask import Flask, jsonify, send_from_directory, request

app = Flask(__name__, static_folder="web")
BASE_DIR    = Path(__file__).parent
RESULT_FILE = BASE_DIR / "result.json"
CVRP_FILE   = BASE_DIR / "CVRP.json"
EXE_NAME    = "alns_vrp.exe" if sys.platform == "win32" else "alns_vrp"
EXE_PATH    = BASE_DIR / EXE_NAME

@app.route("/")
def index():
    return send_from_directory("web", "index.html")

@app.route("/api/result")
def get_result():
    if not RESULT_FILE.exists():
        return jsonify({"error": "Chua co result.json."}), 404
    with open(RESULT_FILE, encoding="utf-8") as f:
        return jsonify(json.load(f))

@app.route("/api/run", methods=["POST"])
def run_solver():
    if not EXE_PATH.exists():
        cr = _compile()
        if cr["returncode"] != 0:
            return jsonify({"success": False, "stderr": cr["stderr"]}), 500
    data = request.get_json(silent=True) or {}
    try:
        r = subprocess.run(
            [str(EXE_PATH), "-i", str(CVRP_FILE), "-o", str(RESULT_FILE)],
            capture_output=True, text=True, timeout=120, cwd=str(BASE_DIR))
        return jsonify({"success": r.returncode==0, "stdout": r.stdout, "stderr": r.stderr})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/api/compile", methods=["POST"])
def compile_endpoint():
    r = _compile()
    return jsonify(r), 200 if r["returncode"]==0 else 500

def _compile():
    cmd = ["g++", "-std=c++17", "-O2", "-Wall",
           "src/main.cpp", "src/data_structures.cpp",
           "src/repair_operators.cpp", "src/alns_control.cpp",
           "-I", "include", "-o", EXE_NAME]
    r = subprocess.run(cmd, capture_output=True, text=True, cwd=str(BASE_DIR))
    return {"returncode": r.returncode, "stdout": r.stdout, "stderr": r.stderr}

if __name__ == "__main__":
    print("VRP Visualizer  ->  http://localhost:5000")
    app.run(debug=True, port=5000)
""".lstrip()

# ══════════════════════════════════════════════════════════════
#  web/index.html  (rút gọn – bản đầy đủ ở file riêng)
# ══════════════════════════════════════════════════════════════
FILES["web/index.html"] = open(
    Path(__file__).parent / "web" / "index.html", encoding="utf-8"
).read() if (Path(__file__).parent / "web" / "index.html").exists() else """
<!DOCTYPE html><html lang="vi"><head><meta charset="UTF-8">
<title>VRP Dashboard</title>
<script src="https://cdnjs.cloudflare.com/ajax/libs/Chart.js/4.4.0/chart.umd.min.js"></script>
<style>
body{background:#0b0f1a;color:#e2e8f0;font-family:monospace;padding:20px}
h1{color:#38bdf8} button{background:#2563eb;color:#fff;border:none;padding:8px 18px;border-radius:6px;cursor:pointer;margin:4px}
canvas{background:#111827;border-radius:10px;display:block;margin:20px auto}
#info{margin:10px 0;color:#34d399}
</style></head><body>
<h1>VRP – Nearest Insertion</h1>
<button onclick="run()">▶ Run Solver</button>
<button onclick="load()">⟳ Reload</button>
<div id="info">Nhan 'Run Solver' de bat dau.</div>
<canvas id="c" width="700" height="500"></canvas>
<div id="routes"></div>
<script>
const COLORS=['#38bdf8','#34d399','#fb923c','#a78bfa','#f472b6','#facc15'];
let chart=null;
async function run(){
  document.getElementById('info').textContent='Dang chay...';
  await fetch('/api/run',{method:'POST',headers:{'Content-Type':'application/json'},body:'{}'});
  await load();
}
async function load(){
  const r=await fetch('/api/result');
  if(!r.ok){document.getElementById('info').textContent='Chua co ket qua.';return;}
  const d=await r.json();
  document.getElementById('info').textContent=
    'Tong: '+d.totalCost.toFixed(2)+' | Xe: '+d.vehicles;
  const ctx=document.getElementById('c').getContext('2d');
  if(chart)chart.destroy();
  const ds=[];
  d.routes.forEach((r,i)=>{
    ds.push({label:'Route '+r.id,data:r.coords.map(c=>({x:c.x,y:c.y})),
      borderColor:COLORS[i%COLORS.length],showLine:true,fill:false,
      pointRadius:0,borderWidth:2.5});
  });
  const cust=(d.nodes||[]).filter(n=>!n.isDepot);
  ds.push({label:'Khach',data:cust.map(n=>({x:n.x,y:n.y})),
    backgroundColor:'#94a3b8',pointRadius:7,showLine:false});
  const dep=(d.nodes||[]).find(n=>n.isDepot);
  if(dep)ds.push({label:'Depot',data:[{x:dep.x,y:dep.y}],
    backgroundColor:'#fbbf24',pointRadius:12,showLine:false});
  chart=new Chart(ctx,{type:'scatter',data:{datasets:ds},
    options:{responsive:false,plugins:{legend:{display:false}},
      scales:{x:{grid:{color:'#1f2937'}},y:{grid:{color:'#1f2937'}}}}});
  document.getElementById('routes').innerHTML=d.routes.map((r,i)=>
    '<p style="color:'+COLORS[i%COLORS.length]+'">Route '+r.id+': 0 -> '+
    r.customers.join(' -> ')+' -> 0 | dist='+r.cost.toFixed(2)+'</p>').join('');
}
load();
</script></body></html>
""".lstrip()

# ══════════════════════════════════════════════════════════════
#  .vscode/c_cpp_properties.json
# ══════════════════════════════════════════════════════════════
FILES[".vscode/c_cpp_properties.json"] = """{
  "configurations": [
    {
      "name": "Win32",
      "includePath": ["${workspaceFolder}/include","${workspaceFolder}/**"],
      "defines": ["_DEBUG","UNICODE"],
      "compilerPath": "C:/MinGW/bin/g++.exe",
      "cStandard": "c17",
      "cppStandard": "c++17",
      "intelliSenseMode": "windows-gcc-x64"
    },
    {
      "name": "Linux",
      "includePath": ["${workspaceFolder}/include","${workspaceFolder}/**"],
      "defines": [],
      "compilerPath": "/usr/bin/g++",
      "cStandard": "c17",
      "cppStandard": "c++17",
      "intelliSenseMode": "linux-gcc-x64"
    }
  ],
  "version": 4
}
"""

# ─────────────────────────────────────────────────────────────
#  Main: tạo cấu trúc thư mục và ghi files
# ─────────────────────────────────────────────────────────────
def setup(root: Path):
    print(f"\n  Tao du an tai: {root.resolve()}\n")

    # Tạo thư mục gốc và các thư mục con
    for folder in ["include", "src", "web", ".vscode"]:
        (root / folder).mkdir(parents=True, exist_ok=True)
        print(f"  [DIR]  {folder}/")

    print()

    # Ghi từng file
    for rel_path, content in FILES.items():
        full_path = root / rel_path
        full_path.parent.mkdir(parents=True, exist_ok=True)

        # web/index.html: đọc từ hàm con nếu tồn tại file gốc
        if rel_path == "web/index.html" and content.startswith("<!DOCTYPE"):
            pass  # dùng nội dung đã lấy

        with open(full_path, "w", encoding="utf-8", newline="\n") as f:
            f.write(content)
        size = full_path.stat().st_size
        print(f"  [OK]   {rel_path:<45} ({size:>6} bytes)")

    # Nhắc tải json.hpp
    print(f"""
  ┌─────────────────────────────────────────────────────────┐
  │  BUOC TIEP THEO                                         │
  ├─────────────────────────────────────────────────────────┤
  │  1. Tai json.hpp tu:                                    │
  │     https://github.com/nlohmann/json/releases           │
  │     → single_include/nlohmann/json.hpp                  │
  │     → dat vao thu muc include/                          │
  │                                                         │
  │  2. Compile (Windows – MinGW):                          │
  │     g++ -std=c++17 -O2 -Wall                 \\          │
  │       src/main.cpp src/data_structures.cpp   \\          │
  │       src/repair_operators.cpp               \\          │
  │       src/alns_control.cpp                   \\          │
  │       -I include -o alns_vrp.exe                        │
  │                                                         │
  │  3. Chay:                                               │
  │     .\\alns_vrp.exe                                      │
  │                                                         │
  │  4. Web (can flask):                                    │
  │     pip install flask                                   │
  │     python app.py  ->  http://localhost:5000            │
  └─────────────────────────────────────────────────────────┘
""")
    print(f"  Hoan thanh! {len(FILES)} files da duoc tao.\n")


if __name__ == "__main__":
    target = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(".")
    try:
        setup(target)
    except Exception as e:
        print(f"\n  [LOI] {e}\n")
        sys.exit(1)
