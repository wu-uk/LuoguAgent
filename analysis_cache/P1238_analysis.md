# P1238 详细题解

本题要求在给定的 m×n 迷宫中，找出从指定起点到终点的所有不重复路径。迷宫中的格子用 1 表示可通行，0 表示障碍。移动方向限定为上、左、右、下，且遵循题目给定的优先顺序：左、上、右、下。如果没有可行路径，则输出 -1。

### 核心思路
这是一个典型的路径搜索问题，适合使用深度优先搜索（DFS）来解决。DFS 会从起点出发，沿着一个方向尽可能深地探索，直到走到终点或无法继续前进，然后回溯到上一个节点，尝试其他方向。通过递归实现 DFS 并记录路径，可以系统地枚举所有可能的路径。

### 关键步骤
1. **输入处理**：读取迷宫的行数 m 和列数 n，然后读取 m 行 n 列的迷宫地图。接着读取起点坐标和终点坐标。注意题目中的坐标可能是从 1 开始的，需要适配数组的索引。

2. **方向定义**：定义四个方向的移动向量，优先顺序为左（(-1,0)）、上、右、下。在搜索时，按照这个顺序依次尝试移动，确保输出路径的优先级正确。

3. **DFS 和回溯**：
   - 维护一个路径数组 `path`，记录当前路径的坐标点。
   - 维护一个访问矩阵 `visited`，标记已经访问过的格子，避免路径中重复访问同一个点。
   - 从起点开始，尝试四个方向移动。如果移动后的格子是可通行的（值为 1）且未被访问过，则将其加入路径，标记为已访问，然后递归搜索下一步。
   - 如果到达终点，则输出当前路径。递归返回后，需要回溯：将当前格子从路径中移除，并取消访问标记，以便其他路径可以探索该格子。

4. **路径输出**：当到达终点时，按照格式 `(x,y)->...` 打印路径。注意起点和终点的坐标格式正确。

5. **无路径处理**：如果搜索结束后没有找到任何路径，则输出 -1。

### 优化技巧
- **防止越界**：在检查下一个格子时，确保其坐标在迷宫范围内（1 到 m，1 到 n）。
- **减少输出冗余**：题目要求无重复路径，因此通过 `visited` 矩阵确保路径中不重复经过同一个点。同时，回溯时正确恢复状态至关重要。

### 示例说明
以题目示例迷宫为例：
- 起点 (1,1)，终点 (5,6)。
- 按照左、上、右、下的顺序搜索，最终输出所有可行路径。DFS 会从起点出发，尝试左（不可行）、上（越界）、右（可行）等方向，逐步深入并记录路径。

### 注意事项
- 题目中的坐标是从 1 开始的，因此数组索引需要减一或直接使用 1 开始的数组。
- 路径输出时注意括号和箭头的格式，每个点之间用 `->` 连接。
- 迷宫地图需要原样保存，不能直接修改，因此使用 `visited` 矩阵来记录访问状态。

通过上述步骤，即可完整解决该问题。

# 参考代码 (cpp)

```cpp
#include <iostream>
#include <vector>
using namespace std;

// 全局变量
int m, n;
vector<vector<int>> maze;
vector<vector<bool>> visited;
vector<pair<int, int>> path;
bool found = false;

// 方向：左、上、右、下（注意题目要求优先顺序）
int dx[4] = {0, -1, 0, 1};
int dy[4] = {-1, 0, 1, 0};

// 检查坐标是否在迷宫范围内且可通行
bool isValid(int x, int y) {
    return x >= 1 && x <= m && y >= 1 && y <= n && maze[x][y] == 1 && !visited[x][y];
}

// 打印当前路径
void printPath(int startX, int startY, int endX, int endY) {
    for (int i = 0; i < path.size() - 1; ++i) {
        cout << "(" << path[i].first << "," << path[i].second << ")->";
    }
    cout << "(" << endX << "," << endY << ")" << endl;
}

// 深度优先搜索
void dfs(int x, int y, int endX, int endY) {
    if (x == endX && y == endY) {
        found = true;
        printPath(x, y, endX, endY);
        return;
    }

    for (int dir = 0; dir < 4; ++dir) {
        int nx = x + dx[dir];
        int ny = y + dy[dir];
        if (isValid(nx, ny)) {
            visited[nx][ny] = true;
            path.emplace_back(nx, ny);
            dfs(nx, ny, endX, endY);
            // 回溯
            visited[nx][ny] = false;
            path.pop_back();
        }
    }
}

int main() {
    // 读取迷宫大小
    cin >> m >> n;
    maze.resize(m + 1, vector<int>(n + 1, 0));
    visited.resize(m + 1, vector<bool>(n + 1, false));

    // 读取迷宫地图
    for (int i = 1; i <= m; ++i) {
        for (int j = 1; j <= n; ++j) {
            cin >> maze[i][j];
        }
    }

    // 读取起点和终点
    int startX, startY, endX, endY;
    cin >> startX >> startY;
    cin >> endX >> endY;

    // 初始化起点
    visited[startX][startY] = true;
    path.emplace_back(startX, startY);

    // 检查起点和终点是否可通行
    if (maze[startX][startY] != 1 || maze[endX][endY] != 1) {
        cout << "-1" << endl;
        return 0;
    }

    // 执行 DFS
    dfs(startX, startY, endX, endY);

    // 如果没有找到路径
    if (!found) {
        cout << "-1" << endl;
    }

    return 0;
}
```

# 核心知识点

* 深度优先搜索
* DFS
* 回溯
* 迷宫问题
* 路径搜索
