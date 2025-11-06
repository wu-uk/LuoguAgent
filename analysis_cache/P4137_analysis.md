# P4137 详细题解

本题要求在给定数组上进行 m 次区间询问，每次查询区间 [l, r] 内未出现过的最小自然数（即 mex，minimum excluded）。数据规模 n, m ≤ 2×10⁵，需要高效的离线算法。

### 核心思想
由于 mex 查询具有特殊的性质，且插入操作难以高效维护，通常采用删除更方便的算法。这里我们使用一种优化的莫队算法——回滚莫队（Rollback Mo's Algorithm）。其核心在于通过特殊的询问排序，使得每个块的询问处理过程中，指针移动主要是删除，而插入操作可以通过回滚来处理，从而实现高效维护 mex。

### 算法步骤
1. **分块**：将数组分成若干块，块大小取 √n。每个询问按照左端点所在的块号排序，同一块内按右端点降序排序。这样，右指针会从右向左移动（删除），而左指针在处理同一块时会回滚到块的左端点（通过暴力恢复实现）。

2. **初始化全局状态**：首先统计整个数组的 mex，记为 `global_mex`。同时，用一个计数数组 `cnt[]` 维护当前区间内每个数的出现次数，并用 `current_mex` 记录当前 mex。`current_mex` 的更新规则是：当删除一个数 `x` 后，如果 `cnt[x]` 变为 0，则 `current_mex = min(current_mex, x)`。

3. **处理询问**：
   - 对于左端点在同一块的询问，右指针从 n 开始向左移动，直到到达询问的右端点 `r`。移动过程中，每次删除右端点的数，并更新 `current_mex`。
   - 然后，左指针从块的左端点开始向右移动，直到到达询问的左端点 `l`。同样，每次删除左端点的数，并更新 `current_mex`，此时得到的 `current_mex` 即为询问的答案。
   - 处理完当前块的所有询问后，左指针会回滚到块的左端点（通过暴力恢复计数数组 `cnt`），同时右指针移动到块的左端点的下一个位置（为下一个块做准备）。

4. **特殊情况**：对于左右端点在同一块的询问，直接暴力计算 mex（时间复杂度 O(块大小)）。

### 时间复杂度分析
- 分块和排序：O(n log n)。
- 每个块内，右指针最多移动 n 次，左指针回滚和移动也是 O(n) 每块。共 O(n√n) 次操作。
- 每次插入/删除是 O(1)，总复杂度 O((n+m)√n)，可通过块大小优化到 O(n√n)。

### 关键点
- 删除操作易于维护 mex（只需检查删除的数是否使计数为 0）。
- 排序方式确保右指针单调递减，左指针回滚高效。
- 值大于 n 的数对 mex 无影响，可忽略。

# 参考代码 (cpp)

```cpp
#include <bits/stdc++.h>
using namespace std;

const int MAXN = 200005;
const int BLOCK_SIZE = 448; // 近似 sqrt(2e5)

int n, m;
int a[MAXN];
int block_id[MAXN]; // 每个位置所在的块号
int cnt[MAXN];      // 计数数组
int current_mex;    // 当前 mex
int global_mex;     // 全局 mex

struct Query {
    int l, r, id;
    bool operator<(const Query &other) const {
        if (block_id[l] != block_id[other.l])
            return block_id[l] < block_id[other.l];
        return r > other.r; // 同块内按 r 降序
    }
} queries[MAXN];

int answers[MAXN];

// 恢复计数数组到初始状态（暴力恢复）
void reset_cnt(int L, int R) {
    for (int i = L; i <= R; ++i) {
        if (a[i] <= n + 1) {
            cnt[a[i]]++;
        }
    }
}

// 删除位置 pos 的数
void remove_pos(int pos) {
    if (a[pos] > n + 1) return; // 忽略大于 n+1 的数
    cnt[a[pos]]--;
    if (cnt[a[pos]] == 0) {
        current_mex = min(current_mex, a[pos]);
    }
}

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    cin >> n >> m;
    for (int i = 1; i <= n; ++i) {
        cin >> a[i];
        block_id[i] = (i - 1) / BLOCK_SIZE + 1;
        if (a[i] <= n + 1) {
            cnt[a[i]]++;
        }
    }

    // 计算全局 mex
    while (cnt[global_mex]) ++global_mex;

    for (int i = 1; i <= m; ++i) {
        cin >> queries[i].l >> queries[i].r;
        queries[i].id = i;
    }

    sort(queries + 1, queries + m + 1);

    int total_blocks = block_id[n];
    int current_block = 1;
    int left_ptr = 1, right_ptr = n;
    current_mex = global_mex;

    for (int i = 1; i <= m; ) {
        // 处理同一块的询问
        if (block_id[queries[i].l] != current_block) {
            // 移动到下一个块
            while (left_ptr <= total_blocks * BLOCK_SIZE) {
                remove_pos(left_ptr++);
            }
            current_mex = global_mex;
            right_ptr = n;
            current_block++;
            continue;
        }

        // 处理当前块的询问
        while (i <= m && block_id[queries[i].l] == current_block) {
            Query &q = queries[i];
            // 如果询问在同一块，直接暴力计算
            if (block_id[q.l] == block_id[q.r]) {
                int mex = 0;
                static int temp_cnt[MAXN];
                for (int j = q.l; j <= q.r; ++j) {
                    if (a[j] <= n + 1) {
                        temp_cnt[a[j]]++;
                    }
                }
                while (temp_cnt[mex]) ++mex;
                answers[q.id] = mex;
                for (int j = q.l; j <= q.r; ++j) {
                    if (a[j] <= n + 1) {
                        temp_cnt[a[j]]--;
                    }
                }
                ++i;
                continue;
            }

            // 移动右指针到 q.r（删除）
            while (right_ptr > q.r) {
                remove_pos(right_ptr--);
            }

            // 移动左指针到 q.l（删除）
            int temp_mex = current_mex;
            for (int j = left_ptr; j < q.l; ++j) {
                remove_pos(j);
            }

            answers[q.id] = current_mex;

            // 回滚左指针（恢复）
            for (int j = left_ptr; j < q.l; ++j) {
                if (a[j] <= n + 1) {
                    cnt[a[j]]++;
                }
            }
            current_mex = temp_mex;

            ++i;
        }

        // 移动左指针到当前块的右边界（为下一个块做准备）
        int block_right = current_block * BLOCK_SIZE;
        while (left_ptr <= block_right && left_ptr <= n) {
            remove_pos(left_ptr++);
        }
    }

    for (int i = 1; i <= m; ++i) {
        cout << answers[i] << '\n';
    }

    return 0;
}
```

# 核心知识点

* 回滚莫队
* 离线算法
* 分块
* mex
* 区间查询
