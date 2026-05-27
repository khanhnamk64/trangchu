#pragma once
// =============================================================
//  data_structures.h
//  Định nghĩa toàn bộ kiểu dữ liệu cốt lõi cho bài toán VRP.
//  Thiết kế theo nguyên tắc: dữ liệu thuần tuý, không logic.
// =============================================================
#include <vector>
#include <string>
#include <cmath>
#include <cassert>
#include <limits>
#include <stdexcept>
#include <algorithm>

// -------------------------------------------------------------
//  Node – đại diện cho một khách hàng hoặc depot
// -------------------------------------------------------------
struct Node {
    int    id     = 0;
    double x      = 0.0;
    double y      = 0.0;
    int    demand = 0;      // 0 nếu là depot
    std::string label;      // tên tùy chọn (hiển thị)

    bool isDepot() const { return id == 0; }
};

// -------------------------------------------------------------
//  Route – một hành trình xe (KHÔNG lưu depot, thêm khi in)
// -------------------------------------------------------------
struct Route {
    std::vector<int> path;    // id khách theo thứ tự thăm
    int    load     = 0;      // tổng demand hiện tại
    double cost     = 0.0;    // tổng quãng đường (depot→...→depot)

    bool empty() const { return path.empty(); }

    bool canAccept(int extraDemand, int capacity) const {
        return (load + extraDemand) <= capacity;
    }

    // Xóa khách hàng tại vị trí pos, trả về id của nó
    int removeAt(int pos) {
        assert(pos >= 0 && pos < static_cast<int>(path.size()));
        int id = path[pos];
        path.erase(path.begin() + pos);
        return id;
    }

    // Chèn khách hàng id vào vị trí pos
    void insertAt(int pos, int nodeId) {
        assert(pos >= 0 && pos <= static_cast<int>(path.size()));
        path.insert(path.begin() + pos, nodeId);
    }
};

// -------------------------------------------------------------
//  Solution – tập hợp các Route
// -------------------------------------------------------------
struct Solution {
    std::vector<Route> routes;
    double totalCost    = 0.0;
    int    vehiclesUsed = 0;

    // Xóa route rỗng và cập nhật vehiclesUsed
    void compact() {
        routes.erase(
            std::remove_if(routes.begin(), routes.end(),
                [](const Route& r){ return r.empty(); }),
            routes.end()
        );
        vehiclesUsed = static_cast<int>(routes.size());
    }

    // Tính lại totalCost từ tất cả routes
    void recalcTotalCost() {
        totalCost = 0.0;
        for (const auto& r : routes) totalCost += r.cost;
        vehiclesUsed = static_cast<int>(routes.size());
    }

    bool valid() const {
        return !routes.empty() && totalCost >= 0.0;
    }
};

// -------------------------------------------------------------
//  DistanceMatrix – ma trận khoảng cách tiền tính O(n²)
//  Tra cứu O(1), tránh sqrt() lặp lại khi chạy thuật toán
// -------------------------------------------------------------
class DistanceMatrix {
public:
    DistanceMatrix() = default;

    // Xây dựng từ danh sách nodes (Euclidean 2D)
    void build(const std::vector<Node>& nodes) {
        n_ = static_cast<int>(nodes.size());
        if (n_ == 0) throw std::invalid_argument("Node list is empty");

        mat_.assign(n_, std::vector<double>(n_, 0.0));
        for (int i = 0; i < n_; ++i) {
            for (int j = i + 1; j < n_; ++j) {
                double dx = nodes[i].x - nodes[j].x;
                double dy = nodes[i].y - nodes[j].y;
                double d  = std::sqrt(dx * dx + dy * dy);
                mat_[i][j] = d;
                mat_[j][i] = d;
            }
        }
    }

    // Tra cứu khoảng cách (O(1))
    double operator()(int i, int j) const {
        assert(i >= 0 && i < n_ && j >= 0 && j < n_);
        return mat_[i][j];
    }

    // Khoảng cách từ depot (node 0) đến node j
    double fromDepot(int j) const { return mat_[0][j]; }

    int size() const { return n_; }

private:
    int n_ = 0;
    std::vector<std::vector<double>> mat_;
};

// -------------------------------------------------------------
//  Instance – toàn bộ dữ liệu bài toán VRP
// -------------------------------------------------------------
struct Instance {
    std::string        name;
    std::vector<Node>  nodes;          // nodes[0] = depot
    int                numVehicles = 0;
    int                capacity    = 0;
    DistanceMatrix     dist;

    int numCustomers() const {
        return static_cast<int>(nodes.size()) - 1;  // trừ depot
    }

    const Node& depot() const { return nodes[0]; }

    // Xây dựng ma trận khoảng cách sau khi nạp nodes
    void buildDistMatrix() {
        dist.build(nodes);
    }

    // Kiểm tra tính hợp lệ cơ bản
    void validate() const {
        if (nodes.empty())
            throw std::runtime_error("[Instance] Khong co node nao.");
        if (capacity <= 0)
            throw std::runtime_error("[Instance] Capacity phai > 0.");
        for (const auto& n : nodes) {
            if (!n.isDepot() && n.demand <= 0)
                throw std::runtime_error(
                    "[Instance] Node " + std::to_string(n.id) +
                    " co demand khong hop le.");
            if (!n.isDepot() && n.demand > capacity)
                throw std::runtime_error(
                    "[Instance] Node " + std::to_string(n.id) +
                    " co demand (" + std::to_string(n.demand) +
                    ") vuot qua capacity (" + std::to_string(capacity) + ").");
        }
    }
};
