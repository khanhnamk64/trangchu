#pragma once
// =============================================================
//  alns_control.h
//  Điều khiển luồng chạy chính: nạp dữ liệu, ghi kết quả,
//  in báo cáo. Tách biệt hoàn toàn với logic thuật toán.
// =============================================================
#include "data_structures.h"
#include <string>
#include <ostream>
#include <chrono>

// -------------------------------------------------------------
//  I/O – Nạp dữ liệu từ JSON, ghi kết quả ra JSON
// -------------------------------------------------------------

/**
 * Nạp Instance từ file JSON (dùng nlohmann/json).
 *
 * Cấu trúc JSON được hỗ trợ:
 * {
 *   "name": "C101",
 *   "numVehicles": 3,
 *   "capacity": 50,
 *   "depot": { "x": 0, "y": 0 },
 *   "customers": [
 *     { "id": 1, "x": 2.5, "y": 3.1, "demand": 10 }, ...
 *   ]
 * }
 *
 * @throws std::runtime_error nếu file không đọc được hoặc JSON sai format
 */
Instance loadInstanceFromJSON(const std::string& filepath);

/**
 * Ghi Solution ra file result.json để Flask đọc và visualize.
 *
 * Output format:
 * {
 *   "instance":  "C101",
 *   "totalCost": 123.45,
 *   "vehicles":  3,
 *   "elapsedMs": 12.3,
 *   "nodes": [ {"id":0,"x":0,"y":0,"demand":0,"isDepot":true}, ... ],
 *   "routes": [
 *     {
 *       "id": 1,
 *       "path": [0,3,1,5,0],   ← inclus depot au début et à la fin
 *       "load": 42,
 *       "cost": 55.2,
 *       "coords": [{"x":0,"y":0}, ...]
 *     }, ...
 *   ]
 * }
 */
void writeResultToJSON(
    const std::string& filepath,
    const Solution&    sol,
    const Instance&    inst,
    double             elapsedMs
);

// -------------------------------------------------------------
//  Reporting – in kết quả ra console
// -------------------------------------------------------------

/**
 * In bảng tóm tắt solution ra stream (mặc định std::cout).
 * Dùng định dạng căn chỉnh dễ đọc.
 */
void printSolutionReport(
    const Solution&  sol,
    const Instance&  inst,
    double           elapsedMs,
    std::ostream&    out = *(std::ostream*)nullptr  // sẽ dùng std::cout nếu null
);

/**
 * In tiêu đề banner khi khởi động chương trình.
 */
void printBanner();

// -------------------------------------------------------------
//  Timer – đo thời gian chạy
// -------------------------------------------------------------
class Timer {
public:
    Timer() : start_(std::chrono::high_resolution_clock::now()) {}

    void reset() {
        start_ = std::chrono::high_resolution_clock::now();
    }

    // Trả về số milliseconds đã trôi qua
    double elapsedMs() const {
        auto now = std::chrono::high_resolution_clock::now();
        return std::chrono::duration<double, std::milli>(now - start_).count();
    }

private:
    std::chrono::time_point<std::chrono::high_resolution_clock> start_;
};

// -------------------------------------------------------------
//  RunConfig – cấu hình chạy từ command line
// -------------------------------------------------------------
struct RunConfig {
    std::string inputFile  = "CVRP.json";
    std::string outputFile = "result.json";
    bool        verbose    = true;
};

/**
 * Parse command-line arguments.
 * Hỗ trợ: -i <input.json>  -o <output.json>  --quiet
 */
RunConfig parseArgs(int argc, char* argv[]);
