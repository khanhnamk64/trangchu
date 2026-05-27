#pragma once
// =============================================================
//  repair_operators.h
//  Khai báo toàn bộ logic thuật toán Nearest Insertion.
//
//  Quy ước đặt tên:
//    calc*   – tính toán, KHÔNG thay đổi trạng thái
//    do*     – thực hiện thay đổi trực tiếp lên Route/Solution
//    build*  – xây dựng từ đầu (khởi tạo)
//    solve*  – hàm entry-point cấp cao
// =============================================================
#include "data_structures.h"
#include <utility>   // std::pair
#include <vector>
#include <tuple>

// -------------------------------------------------------------
//  Hàm tiện ích: tính chi phí route (depot→path→depot)
// -------------------------------------------------------------

/**
 * Tính tổng quãng đường thực tế của một Route.
 * Công thức: d(depot,p0) + Σd(pᵢ,pᵢ₊₁) + d(pₙ,depot)
 */
double calcRouteCost(const Route& route, const DistanceMatrix& dist);

/**
 * Cập nhật route.cost bằng cách gọi calcRouteCost().
 * Trả về chi phí mới.
 */
double refreshRouteCost(Route& route, const DistanceMatrix& dist);

// -------------------------------------------------------------
//  Nearest Selection (Bước 1 của Nearest Insertion)
// -------------------------------------------------------------

/**
 * Tìm node chưa thăm (unvisited) gần nhất với BẤT KỲ node nào
 * đã có trong tour hiện tại.
 *
 * Tiêu chí: k* = argmin { dist(i,k) : i ∈ tour ∪ {depot}, k ∈ unvisited }
 *
 * @return index của node trong unvisited[] gần nhất
 *         (-1 nếu unvisited rỗng)
 */
int selectNearest(
    const Route&              route,
    const std::vector<int>&   unvisited,
    const DistanceMatrix&     dist
);

// -------------------------------------------------------------
//  Cheapest Insertion (Bước 2 của Nearest Insertion)
// -------------------------------------------------------------

/**
 * Tính chi phí tăng thêm (delta cost) khi chèn nodeK
 * vào giữa hai node liên tiếp tại vị trí insertPos.
 *
 * Route hiện tại:  depot → … → path[insertPos-1] → path[insertPos] → …
 * Sau khi chèn:    depot → … → path[insertPos-1] → nodeK → path[insertPos] → …
 *
 * Δf = d(i, k) + d(k, j) - d(i, j)
 * trong đó i = path[insertPos-1] (hoặc depot), j = path[insertPos] (hoặc depot)
 */
double calcInsertionDelta(
    int                   nodeK,
    int                   insertPos,          // vị trí trong path (0 → n)
    const Route&          route,
    const DistanceMatrix& dist
);

/**
 * Tìm vị trí chèn tốt nhất (cheapest) cho nodeK vào route.
 *
 * @return { vị_trí_chèn_tốt_nhất, delta_cost_nhỏ_nhất }
 *         vị trí 0 = chèn trước phần tử đầu tiên
 *         vị trí n = chèn sau phần tử cuối cùng
 */
std::pair<int, double> findCheapestInsertPos(
    int                   nodeK,
    const Route&          route,
    const DistanceMatrix& dist
);

// -------------------------------------------------------------
//  Route builder – xây dựng một route bằng Nearest Insertion
// -------------------------------------------------------------

/**
 * Xây dựng MỘT Route từ tập unvisited theo Nearest Insertion.
 * Thuật toán dừng khi:
 *   (a) unvisited rỗng, HOẶC
 *   (b) không còn node nào vừa capacity của route này
 *
 * unvisited sẽ bị XÓA các node đã được chèn vào route.
 *
 * @param seedNode   Node đầu tiên để khởi tạo route
 *                   (-1 → tự chọn node gần depot nhất)
 * @return Route hoàn chỉnh với cost đã được tính
 */
Route buildOneRoute(
    std::vector<int>&     unvisited,    // [in/out] sẽ bị xóa
    const Instance&       inst,
    int                   seedNode = -1
);

// -------------------------------------------------------------
//  Solver entry-point
// -------------------------------------------------------------

/**
 * Giải toàn bộ bài toán VRP bằng Nearest Insertion.
 *
 * Luồng chính:
 *   while (còn khách chưa thăm):
 *       route = buildOneRoute(unvisited, inst)
 *       solution.routes.push_back(route)
 *
 * @return Solution hoàn chỉnh (totalCost đã được cập nhật)
 */
Solution solveNearestInsertion(const Instance& inst);

// -------------------------------------------------------------
//  Validation helper (dùng để test)
// -------------------------------------------------------------

/**
 * Kiểm tra Solution có hợp lệ không:
 *  - Mỗi khách hàng xuất hiện đúng 1 lần
 *  - Không route nào vượt capacity
 *  - totalCost khớp với tổng route.cost
 *
 * @return true nếu hợp lệ, false nếu có vi phạm (kèm message qua cerr)
 */
bool validateSolution(const Solution& sol, const Instance& inst);
