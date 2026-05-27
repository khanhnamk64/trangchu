// =============================================================
//  main.cpp
//  Điểm vào chương trình. Điều phối toàn bộ pipeline:
//    1. Parse args
//    2. Nạp dữ liệu (CVRP.json)
//    3. Chạy Nearest Insertion
//    4. Validate kết quả
//    5. Ghi result.json
//    6. In báo cáo
// =============================================================
#include "../include/data_structures.h"
#include "../include/repair_operators.h"
#include "../include/alns_control.h"

#include <iostream>
#include <stdexcept>

int main(int argc, char* argv[]) {
    printBanner();
    RunConfig cfg = parseArgs(argc, argv);

    try {
        // ── 1. Nạp dữ liệu ─────────────────────────────────────
        std::cout << "  [1/4] Doc du lieu: " << cfg.inputFile << " ...\n";
        Instance inst = loadInstanceFromJSON(cfg.inputFile);

        if (cfg.verbose) {
            std::cout << "       Instance : " << inst.name         << "\n";
            std::cout << "       Customers: " << inst.numCustomers()<< "\n";
            std::cout << "       Vehicles : " << inst.numVehicles  << "\n";
            std::cout << "       Capacity : " << inst.capacity     << "\n\n";
        }

        // ── 2. Chạy thuật toán ──────────────────────────────────
        std::cout << "  [2/4] Chay Nearest Insertion ...\n";
        Timer timer;
        Solution sol = solveNearestInsertion(inst);
        double elapsed = timer.elapsedMs();

        // ── 3. Validate ─────────────────────────────────────────
        std::cout << "  [3/4] Kiem tra tinh hop le ...\n  ";
        bool ok = validateSolution(sol, inst);
        if (!ok) {
            std::cerr << "  [WARN] Solution co vi pham – kiem tra lai input!\n";
        }

        // ── 4. Ghi kết quả ──────────────────────────────────────
        std::cout << "  [4/4] Ghi ket qua ...\n";
        writeResultToJSON(cfg.outputFile, sol, inst, elapsed);

        // ── 5. Báo cáo ──────────────────────────────────────────
        if (cfg.verbose) {
            std::cout << "\n";
            printSolutionReport(sol, inst, elapsed);
        }

    } catch (const std::exception& e) {
        std::cerr << "\n  [LOI] " << e.what() << "\n";
        return EXIT_FAILURE;
    }

    std::cout << "\n  Hoan thanh! Mo trinh duyet va chay Flask de xem:\n";
    std::cout << "    python app.py\n\n";
    return EXIT_SUCCESS;
}
