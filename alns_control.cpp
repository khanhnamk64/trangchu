// =============================================================
//  alns_control.cpp
//  Triển khai: nạp/ghi JSON, báo cáo console, parse args.
//  Dùng nlohmann/json (header-only) – đặt json.hpp vào include/
// =============================================================
#include "../include/alns_control.h"
#include "../include/repair_operators.h"
#include "../include/json.hpp"

#include <fstream>
#include <iostream>
#include <iomanip>
#include <sstream>
#include <stdexcept>
#include <cstring>

using json = nlohmann::json;

// ─────────────────────────────────────────────────────────────
//  loadInstanceFromJSON
// ─────────────────────────────────────────────────────────────
Instance loadInstanceFromJSON(const std::string& filepath) {
    std::ifstream f(filepath);
    if (!f.is_open())
        throw std::runtime_error("Khong mo duoc file: " + filepath);

    json j;
    try {
        f >> j;
    } catch (const json::parse_error& e) {
        throw std::runtime_error("JSON parse error trong " + filepath +
                                 ": " + e.what());
    }

    Instance inst;
    inst.name        = j.value("name", filepath);
    inst.numVehicles = j.at("numVehicles").get<int>();
    inst.capacity    = j.at("capacity").get<int>();

    // Depot (node 0)
    Node depot;
    depot.id     = 0;
    depot.x      = j.at("depot").at("x").get<double>();
    depot.y      = j.at("depot").at("y").get<double>();
    depot.demand = 0;
    depot.label  = "Depot";
    inst.nodes.push_back(depot);

    // Customers
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

// ─────────────────────────────────────────────────────────────
//  writeResultToJSON
// ─────────────────────────────────────────────────────────────
void writeResultToJSON(
    const std::string& filepath,
    const Solution&    sol,
    const Instance&    inst,
    double             elapsedMs)
{
    json j;
    j["instance"]  = inst.name;
    j["totalCost"] = sol.totalCost;
    j["vehicles"]  = sol.vehiclesUsed;
    j["elapsedMs"] = elapsedMs;
    j["capacity"]  = inst.capacity;

    // Tất cả nodes (depot + customers) – dùng cho web vẽ map
    json nodesArr = json::array();
    for (const auto& n : inst.nodes) {
        nodesArr.push_back({
            {"id",      n.id},
            {"x",       n.x},
            {"y",       n.y},
            {"demand",  n.demand},
            {"label",   n.label},
            {"isDepot", n.isDepot()}
        });
    }
    j["nodes"] = nodesArr;

    // Routes
    json routesArr = json::array();
    for (int r = 0; r < static_cast<int>(sol.routes.size()); ++r) {
        const auto& route = sol.routes[r];

        // Path đầy đủ bao gồm depot ở đầu và cuối
        json pathArr = json::array();
        json coordsArr = json::array();

        auto addCoord = [&](int id) {
            coordsArr.push_back({ {"x", inst.nodes[id].x},
                                  {"y", inst.nodes[id].y} });
        };

        pathArr.push_back(0); addCoord(0);
        for (int c : route.path) {
            pathArr.push_back(c);
            addCoord(c);
        }
        pathArr.push_back(0); addCoord(0);

        routesArr.push_back({
            {"id",       r + 1},
            {"path",     pathArr},
            {"customers", route.path},
            {"load",     route.load},
            {"cost",     route.cost},
            {"coords",   coordsArr}
        });
    }
    j["routes"] = routesArr;

    std::ofstream out(filepath);
    if (!out.is_open())
        throw std::runtime_error("Khong ghi duoc: " + filepath);
    out << j.dump(2);
    std::cout << "  → Da ghi: " << filepath << "\n";
}

// ─────────────────────────────────────────────────────────────
//  printSolutionReport
// ─────────────────────────────────────────────────────────────
void printSolutionReport(
    const Solution&  sol,
    const Instance&  inst,
    double           elapsedMs,
    std::ostream&    out_)
{
    std::ostream& out = (&out_ == nullptr) ? std::cout : out_;

    const int W = 60;
    out << std::string(W, '=') << "\n";
    out << "  VRP SOLUTION – " << inst.name << "\n";
    out << std::string(W, '=') << "\n";
    out << std::fixed << std::setprecision(4);
    out << "  Khach hang     : " << inst.numCustomers()  << "\n";
    out << "  Xe su dung     : " << sol.vehiclesUsed     << " / "
                                 << inst.numVehicles     << "\n";
    out << "  Tong quang duong: " << sol.totalCost       << "\n";
    out << "  Thoi gian       : " << elapsedMs           << " ms\n";
    out << std::string(W, '-') << "\n";

    for (int r = 0; r < static_cast<int>(sol.routes.size()); ++r) {
        const auto& route = sol.routes[r];
        out << "  Route " << std::setw(2) << (r + 1) << " "
            << "[load=" << std::setw(4) << route.load
            << "/" << inst.capacity
            << " dist=" << std::setw(8) << route.cost << "]:  ";
        out << "0";
        for (int c : route.path) out << " → " << c;
        out << " → 0\n";
    }
    out << std::string(W, '=') << "\n";
}

// ─────────────────────────────────────────────────────────────
//  printBanner
// ─────────────────────────────────────────────────────────────
void printBanner() {
    std::cout << R"(
  ╔══════════════════════════════════════════════╗
  ║   VRP – Nearest Insertion Heuristic v1.0     ║
  ║   C++17 | Multi-route | Capacity constrained ║
  ╚══════════════════════════════════════════════╝
)";
}

// ─────────────────────────────────────────────────────────────
//  parseArgs
// ─────────────────────────────────────────────────────────────
RunConfig parseArgs(int argc, char* argv[]) {
    RunConfig cfg;
    for (int i = 1; i < argc; ++i) {
        if (std::strcmp(argv[i], "-i") == 0 && i + 1 < argc)
            cfg.inputFile = argv[++i];
        else if (std::strcmp(argv[i], "-o") == 0 && i + 1 < argc)
            cfg.outputFile = argv[++i];
        else if (std::strcmp(argv[i], "--quiet") == 0)
            cfg.verbose = false;
    }
    return cfg;
}
