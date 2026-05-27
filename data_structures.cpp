// =============================================================
//  data_structures.cpp
//  Triển khai các method bổ sung của DistanceMatrix & Instance.
//  (Hầu hết logic đã inline trong header để hiệu năng tốt hơn)
// =============================================================
#include "../include/data_structures.h"
#include <iostream>
#include <iomanip>

// Không có gì cần triển khai thêm ngoài header vì:
//  - DistanceMatrix::build()  → đã inline
//  - DistanceMatrix::operator() → đã inline
//  - Instance::buildDistMatrix() → gọi dist.build() inline
//  - Tất cả struct method nhỏ → inline trong header

// Hàm debug tiện lợi (chỉ dùng khi phát triển)
void debugPrintInstance(const Instance& inst) {
    std::cout << "===== INSTANCE: " << inst.name << " =====\n";
    std::cout << "  Vehicles : " << inst.numVehicles  << "\n";
    std::cout << "  Capacity : " << inst.capacity     << "\n";
    std::cout << "  Customers: " << inst.numCustomers() << "\n\n";

    std::cout << std::fixed << std::setprecision(2);
    std::cout << "  Nodes:\n";
    for (const auto& n : inst.nodes) {
        std::cout << "    [" << std::setw(3) << n.id << "] "
                  << "(" << std::setw(7) << n.x << ", "
                  <<        std::setw(7) << n.y << ")  "
                  << "demand=" << std::setw(4) << n.demand;
        if (n.isDepot()) std::cout << "  <-- DEPOT";
        std::cout << "\n";
    }
    std::cout << std::string(40, '-') << "\n\n";
}
