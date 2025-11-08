# P1238 详细题解

本题要求在一个 m×n 的迷宫中找出从起点到终点的所有不重复路径。迷宫中的 1 表示可通行，0 表示障碍物。移动方向只能是上、下、左、右，且一条路径中不能重复经过同一个点。题目还规定了搜索的优先顺序：左、上、右、下（即：`(x, y-1)`, `(x-1, y)`, `(x, y+1)`, `(x+1, y)`）。如果没有找到任何路径，则输出 -1。

这是一个典型的深度优先搜索（DFS）问题，或者称为回溯法问题。我们可以通过递归函数来系统地探索所有可能的路径。

**算法思路：**

1.  **存储结构：**
    *   使用一个二维数组（例如 `maze[15][15]`）来存储输入的迷宫信息。`1` 代表通路，`0` 代表墙。
    *   使用一个与迷宫同样大小的二维布尔数组（例如 `visited[15][15]`）来标记某个点是否已经在当前路径中被访问过，以防止路径中出现环路。为了节省空间，也可以直接修改原始的 `maze` 数组，将访问过的点的值改为 `0`，回溯时再改回 `1`。
    *   使用一个一维数组或二维数组（例如 `path[225][2]`）来记录当前搜索路径上的点的坐标。`path[i][0]` 存储第 i 步的行号，`path[i][1]` 存储第 i 步的列号。
    *   设置一个全局布尔变量（例如 `has_path`）来判断是否找到了至少一条路径，初始值为 `false`。

2.  **DFS 函数设计 (`dfs(x, y, step)`):**
    *   **参数：** `x`, `y` 表示当前所在位置的坐标，`step` 表示当前是第几步（或者说路径中已有多少个点）。
    *   **边界条件（递归出口）：**
        *   如果当前点 `(x, y)` 就是终点，说明找到了一条完整路径。
        *   此时，将 `has_path` 标记为 `true`。
        *   遍历 `path` 数组，按照题目要求的格式 `(x,y)->(x,y)...->(x,y)` 输出这条完整的路径，并换行。
        *   返回，继续探索其他可能的路径。
    *   **递归过程：**
        *   从当前点 `(x, y)` 出发，按照**左、上、右、下**的优先顺序尝试移动到下一个点 `(nx, ny)`。
        *   对于每一个方向（`(nx, ny)`）：
            *   **合法性检查：** 判断 `(nx, ny)` 是否在迷宫边界内。
            *   **通行性检查：** 判断 `maze[nx][ny]` 是否为 `1`（即可通行）。
            *   **访问性检查：** 判断 `(nx, ny)` 是否未被访问过（即 `visited[nx][ny]` 为 `false`）。
            *   如果以上条件都满足，则：
                1.  **做出选择：** 将 `(nx, ny)` 加入到当前路径中，即 `path[step][0] = nx; path[step][1] = ny;`。同时，标记该点为已访问，`visited[nx][ny] = true;` (或 `maze[nx][ny] = 0;`)。
                2.  **递归深入：** 以 `(nx, ny)` 为新的起点，步数加一，继续进行 DFS：`dfs(nx, ny, step + 1)`。
                3.  **撤销选择（回溯）：** 递归返回后，需要撤销当前的选择，以便能从其他方向探索。将 `(nx, ny)` 从路径中移除（这一步在下次覆盖 `path[step]` 时自动完成），并取消其访问标记，即 `visited[nx][ny] = false;` (或 `maze[nx][ny] = 1;`)。

3.  **主函数流程：**
    *   读取迷宫的行数 `m` 和列数 `n`。
    *   读取 `m` 行 `n` 列的迷宫数据，存入 `maze` 数组。为了简化边界判断，可以读入后在迷宫四周加一圈 `0` 作为“哨兵墙” (Sentinel Wall)，这样在 DFS 中只需要检查 `maze[nx][ny] == 1` 即可，无需再判断 `(nx, ny)` 是否越界。
    *   读取起点坐标 `(sx, sy)` 和终点坐标 `(ex, ey)`。
    *   **特殊处理：** 如果起点或终点本身是墙（值为0），则肯定无路，直接输出 `-1` 并结束。
    *   初始化起点为已访问，并将起点坐标存入 `path` 数组的第 1 个位置。
    *   调用 DFS 函数：`dfs(sx, sy, 2)`。（`step` 从 2 开始，因为 path[1] 已经是起点了）。
    *   DFS 执行完毕后，检查全局布尔变量 `has_path`。如果它仍然是 `false`，说明没有找到任何路径，则输出 `-1`。

**输出格式处理注意：**
题目要求路径格式为 `(x1,y1)->(x2,y2)->...->(xk,yk)`，其中 `(x1, y1)` 是起点。一些题解提到了坐标大于 9 时的显示问题（例如 `chr(ord('0')+digit)`），但在现代 C++ 环境中，直接使用 `cout << digit` 即可正确处理，无需特殊转换。只需注意在输出路径时，每个点之间用 `->` 连接，最后一个是终点，后面不加 `->`。

# 参考代码 (cpp)

```cpp
#include <iostream>
#include <vector>

// 定义迷宫大小，+2 是为了加哨兵墙
const int MAX_M = 15;
const int MAX_N = 15;

// 全局变量
int maze[MAX_M + 2][MAX_N + 2]; // 迷宫地图，0为墙，1为路
int path[MAX_M * MAX_N][2];    // 记录路径，path[i][0]=row, path[i][1]=col
bool has_path = false;         // 是否找到至少一条路径的标志

// 按照题目要求的优先顺序：左、上、右、下
// dx, dy 分别对应行和列的变化
const int dx[] = {0, -1, 0, 1};
const int dy[] = {-1, 0, 1, 0};

// 深度优先搜索函数
// x, y: 当前位置坐标
// step: 当前是第几步（路径中点的个数）
// end_x, end_y: 终点坐标
void dfs(int x, int y, int step, int end_x, int end_y) {
    // 1. 检查是否到达终点
    if (x == end_x && y == end_y) {
        has_path = true;
        // 输出路径
        for (int i = 1; i < step; ++i) {
            std::cout << "(" << path[i][0] << "," << path[i][1] << ")";
            if (i < step - 1) {
                std::cout << "->";
            }
        }
        std::cout << std::endl;
        return; // 到达终点后，返回以寻找其他路径
    }

    // 2. 按照左、上、右、下的顺序探索
    for (int i = 0; i < 4; ++i) {
        int nx = x + dx[i];
        int ny = y + dy[i];

        // 判断新位置是否可走
        if (maze[nx][ny] == 1) {
            // 做出选择
            maze[nx][ny] = 0; // 标记为已访问
            path[step][0] = nx;
            path[step][1] = ny;

            // 递归深入
            dfs(nx, ny, step + 1, end_x, end_y);

            // 撤销选择（回溯）
            maze[nx][ny] = 1; // 恢复为未访问状态
        }
    }
}

int main() {
    // 提高IO效率
    std::ios_base::sync_with_stdio(false);
    std::cin.tie(NULL);

    int m, n;
    std::cin >> m >> n;

    // 初始化迷宫，外围设为0（哨兵墙）
    for (int i = 0; i <= m + 1; ++i) {
        for (int j = 0; j <= n + 1; ++j) {
            maze[i][j] = 0;
        }
    }

    // 读入迷宫数据
    for (int i = 1; i <= m; ++i) {
        for (int j = 1; j <= n; ++j) {
            std::cin >> maze[i][j];
        }
    }

    int start_x, start_y, end_x, end_y;
    std::cin >> start_x >> start_y;
    std::cin >> end_x >> end_y;

    // 如果起点或终点是墙，则无路可走
    if (maze[start_x][start_y] == 0 || maze[end_x][end_y] == 0) {
        std::cout << -1 << std::endl;
        return 0;
    }

    // 初始化路径和起点
    path[1][0] = start_x;
    path[1][1] = start_y;
    maze[start_x][start_y] = 0; // 标记起点为已访问

    // 从起点开始搜索
    dfs(start_x, start_y, 2, end_x, end_y);

    // 如果全程没找到路径
    if (!has_path) {
        std::cout << -1 << std::endl;
    }

    return 0;
}
```

# 核心知识点

* 深度优先搜索
* 回溯法
* 路径搜索
* 递归
