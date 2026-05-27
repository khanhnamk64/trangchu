// =============================================================
//  repair_operators.cpp
//  Triển khai đầy đủ thuật toán Nearest Insertion cho VRP.
//
//  Tham khảo lý thuyết:
//    Rosenkrantz, Stearns, Lewis (1977) – "An Analysis of Several
//    Heuristics for the Traveling Salesman Problem"
//
//  Độ phức tạp:
//    - selectNearest:           O(|tour| × |unvisited|)
//    - findCheapestInsertPos:   O(|tour|)
//    - buildOneRoute (1 route): O(n²) trong trường hợp xấu nhất
//    - solveNearestInsertion:   O(n³) tổng thể
//
//  Tối ưu hóa đã áp dụng:
//    1. Ma trận khoảng cách tiền tính → O(1) tra cứu
//    2. Dùng std::vector<bool> để đánh dấu visited → O(1)
//    3. Early-exit khi delta <= 0 trong một số trường hợp
// =============================================================
#include "../include/repair_operators.h"
#include <iostream>
#include <iomanip>
#include <numeric>    // std::iota
#include <algorithm>  // std::find, std::remove

// ─────────────────────────────────────────────────────────────
//  calcRouteCost
// ─────────────────────────────────────────────────────────────
double calcRouteCost(const Route& route, const DistanceMatrix& dist) {
    if (route.path.empty()) return 0.0;

    double cost = dist.fromDepot(route.path.front());      // depot → p[0]
    for (int i = 0; i + 1 < static_cast<int>(route.path.size()); ++i)
        cost += dist(route.path[i], route.path[i + 1]);    // p[i] → p[i+1]
    cost += dist.fromDepot(route.path.back());             // p[n] → depot
    return cost;
}

double refreshRouteCost(Route& route, const DistanceMatrix& dist) {
    route.cost = calcRouteCost(route, dist);
    return route.cost;
}

// ─────────────────────────────────────────────────────────────
//  selectNearest   (Nearest Selection – Bước 1)
// ─────────────────────────────────────────────────────────────
// Tìm k* = argmin { dist(i, k) : i ∈ tour ∪ {depot}, k ∈ unvisited }
int selectNearest(
    const Route&            route,
    const std::vector<int>& unvisited,
    const DistanceMatrix&   dist)
{
    if (unvisited.empty()) return -1;

    double bestDist = std::numeric_limits<double>::max();
    int    bestIdx  = 0;   // index trong unvisited[]

    for (int uk = 0; uk < static_cast<int>(unvisited.size()); ++uk) {
        int k = unvisited[uk];

        // So sánh với depot (node 0) luôn có mặt
        double d = dist.fromDepot(k);
        if (d < bestDist) { bestDist = d; bestIdx = uk; }

        // So sánh với mọi node đã có trong route
        for (int i : route.path) {
            d = dist(i, k);
            if (d < bestDist) { bestDist = d; bestIdx = uk; }
        }
    }
    return bestIdx;   // trả về INDEX trong unvisited[], không phải node id
}

// ─────────────────────────────────────────────────────────────
//  calcInsertionDelta   (Cheapest Insertion – Bước 2, từng vị trí)
// ─────────────────────────────────────────────────────────────
// Δf(i, k, j) = d(i,k) + d(k,j) - d(i,j)
// i = node trước insertPos, j = node sau insertPos
// insertPos ∈ [0, path.size()]
double calcInsertionDelta(
    int                   nodeK,
    int                   insertPos,
    const Route&          route,
    const DistanceMatrix& dist)
{
    const auto& p = route.path;
    int n = static_cast<int>(p.size());

    // Xác định node trước (i) và sau (j) vị trí chèn
    // depot = node id 0
    int nodeI = (insertPos == 0) ? 0 : p[insertPos - 1];
    int nodeJ = (insertPos == n) ? 0 : p[insertPos];

    return dist(nodeI, nodeK) + dist(nodeK, nodeJ) - dist(nodeI, nodeJ);
}

// ─────────────────────────────────────────────────────────────
//  findCheapestInsertPos   (Cheapest Insertion – tốt nhất)
// ─────────────────────────────────────────────────────────────
std::pair<int, double> findCheapestInsertPos(
    int                   nodeK,
    const Route&          route,
    const DistanceMatrix& dist)
{
    int    bestPos   = 0;
    double bestDelta = std::numeric_limits<double>::max();

    int n = static_cast<int>(route.path.size());
    for (int pos = 0; pos <= n; ++pos) {
        double delta = calcInsertionDelta(nodeK, pos, route, dist);
        if (delta < bestDelta) {
            bestDelta = delta;
            bestPos   = pos;
        }
    }
    return { bestPos, bestDelta };
}

// ─────────────────────────────────────────────────────────────
//  buildOneRoute   (xây dựng một route hoàn chỉnh)
// ─────────────────────────────────────────────────────────────
Route buildOneRoute(
    std::vector<int>& unvisited,
    const Instance&   inst,
    int               seedNodeId)
{
    Route route;
    const auto& dist = inst.dist;

    // ── Chọn seed node ─────────────────────────────────────────
    if (seedNodeId == -1) {
        // Tự chọn: node gần depot nhất trong unvisited
        double bestD = std::numeric_limits<double>::max();
        for (int uid : unvisited) {
            double d = dist.fromDepot(uid);
            if (d < bestD) { bestD = d; seedNodeId = uid; }
        }
    }

    // Chèn seed vào route
    {
        auto it = std::find(unvisited.begin(), unvisited.end(), seedNodeId);
        if (it == unvisited.end())
            throw std::runtime_error("[buildOneRoute] Seed node khong tim thay trong unvisited.");

        const Node& seedNode = inst.nodes[seedNodeId];
        if (seedNode.demand > inst.capacity)
            throw std::runtime_error("[buildOneRoute] Seed demand vuot capacity.");

        route.path.push_back(seedNodeId);
        route.load = seedNode.demand;
        unvisited.erase(it);
    }

    // ── Nearest Insertion lặp ──────────────────────────────────
    bool extended = true;
    while (extended && !unvisited.empty()) {
        extended = false;

        // Bước 1: Nearest Selection
        // Lọc trước: chỉ xét những node còn vừa capacity
        std::vector<int> candidates;
        candidates.reserve(unvisited.size());
        for (int uid : unvisited) {
            if (route.canAccept(inst.nodes[uid].demand, inst.capacity))
                candidates.push_back(uid);
        }
        if (candidates.empty()) break;  // không còn ai vừa xe này

        // Tìm nearest trong candidates
        double nearestDist = std::numeric_limits<double>::max();
        int    nearestId   = -1;
        for (int uid : candidates) {
            // khoảng cách tới depot
            double d = dist.fromDepot(uid);
            if (d < nearestDist) { nearestDist = d; nearestId = uid; }
            // khoảng cách tới từng node trong route
            for (int ri : route.path) {
                d = dist(ri, uid);
                if (d < nearestDist) { nearestDist = d; nearestId = uid; }
            }
        }
        if (nearestId == -1) break;

        // Bước 2: Cheapest Insertion Position
        auto [bestPos, _delta] = findCheapestInsertPos(nearestId, route, dist);

        // Thực hiện chèn
        route.path.insert(route.path.begin() + bestPos, nearestId);
        route.load += inst.nodes[nearestId].demand;

        // Xóa khỏi unvisited
        unvisited.erase(
            std::find(unvisited.begin(), unvisited.end(), nearestId)
        );

        extended = true;
    }

    refreshRouteCost(route, dist);
    return route;
}

// ─────────────────────────────────────────────────────────────
//  solveNearestInsertion   (entry-point)
// ─────────────────────────────────────────────────────────────
Solution solveNearestInsertion(const Instance& inst) {
    inst.validate();

    Solution sol;

    // Tập chưa thăm: tất cả customer (bỏ depot = node 0)
    std::vector<int> unvisited;
    unvisited.reserve(inst.numCustomers());
    for (int i = 1; i < static_cast<int>(inst.nodes.size()); ++i)
        unvisited.push_back(i);

    int vehicleId = 1;
    while (!unvisited.empty()) {
        // Mỗi vòng lặp = một xe mới
        Route route = buildOneRoute(unvisited, inst, /*seed=*/-1);

        if (route.empty()) {
            // Edge case: không có khách nào vừa capacity → không thoát vô hạn
            std::cerr << "[WARN] Route " << vehicleId
                      << " rong sau buildOneRoute. Con " << unvisited.size()
                      << " khach chua thu xep.\n";
            break;
        }

        sol.routes.push_back(std::move(route));
        ++vehicleId;
    }

    sol.compact();
    sol.recalcTotalCost();
    return sol;
}

// ─────────────────────────────────────────────────────────────
//  validateSolution   (kiểm tra tính đúng đắn)
// ─────────────────────────────────────────────────────────────
bool validateSolution(const Solution& sol, const Instance& inst) {
    bool ok = true;

    // 1. Mỗi khách hàng phải xuất hiện đúng 1 lần
    std::vector<int> count(inst.nodes.size(), 0);
    for (const auto& r : sol.routes)
        for (int c : r.path) {
            if (c <= 0 || c >= static_cast<int>(inst.nodes.size())) {
                std::cerr << "[VALIDATE] Node id " << c << " out of range.\n";
                ok = false;
            } else {
                ++count[c];
            }
        }
    for (int i = 1; i < static_cast<int>(inst.nodes.size()); ++i) {
        if (count[i] != 1) {
            std::cerr << "[VALIDATE] Customer " << i
                      << " xuat hien " << count[i] << " lan.\n";
            ok = false;
        }
    }

    // 2. Không route nào vượt capacity
    for (int r = 0; r < static_cast<int>(sol.routes.size()); ++r) {
        const auto& route = sol.routes[r];
        int load = 0;
        for (int c : route.path) load += inst.nodes[c].demand;
        if (load > inst.capacity) {
            std::cerr << "[VALIDATE] Route " << (r+1)
                      << " vuot capacity: " << load << " > " << inst.capacity << ".\n";
            ok = false;
        }
        if (load != route.load) {
            std::cerr << "[VALIDATE] Route " << (r+1)
                      << " load khong khop: stored=" << route.load
                      << " computed=" << load << ".\n";
            ok = false;
        }
    }

    // 3. totalCost khớp
    double computedTotal = 0.0;
    for (const auto& r : sol.routes) {
        double rc = calcRouteCost(r, inst.dist);
        computedTotal += rc;
        if (std::abs(rc - r.cost) > 1e-6) {
            std::cerr << "[VALIDATE] Route cost khong khop: stored="
                      << r.cost << " computed=" << rc << ".\n";
            ok = false;
        }
    }
    if (std::abs(computedTotal - sol.totalCost) > 1e-6) {
        std::cerr << "[VALIDATE] totalCost khong khop: stored="
                  << sol.totalCost << " computed=" << computedTotal << ".\n";
        ok = false;
    }

    if (ok) std::cout << "[VALIDATE] Solution hop le. ✓\n";
    return ok;
}
