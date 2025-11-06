# P1117 详细题解

### 1. 问题分析

题目要求我们计算一个字符串 S 的所有子串中，能够拆分成 AABB 形式的总方案数。一个 AABB 形式的拆分意味着该子串可以被分为四个连续的非空部分，其中前两部分 A 相同，后两部分 B 相同。

### 2. 核心思想

直接枚举所有子串并判断其是否为 AABB 的朴素方法是 O(n^3) 的，对于 n ≤ 30000 的数据范围来说效率太低。

一个关键的观察是，一个 AABB 形式的字符串可以看作是由一个 AA 类型的子串紧跟着一个 BB 类型的子串构成。

因此，我们可以将问题分解为两个子问题：
1.  计算以每个位置 `i` 结尾的，形如 AA 的子串数量，记为 `f[i]`。
2.  计算以每个位置 `i` 开头的，形如 AA 的子串数量，记为 `g[i]`。（注意：这里的 BB 和 AA 的结构相同，只是位置不同）

对于一个 AABB 子串，如果它在中间位置 `i` 和 `i+1` 之间断开，那么它前面的部分（`S[1...i]`）必须以一个 AA 结尾，而它后面的部分（`S[i+1...n]`）必须以一个 AA 开头。因此，以位置 `i` 和 `i+1` 为分界线的 AABB 子串的数量就是 `f[i] * g[i+1]`。

最终答案就是所有可能的分界点的贡献之和：`Ans = Σ f[i] * g[i+1]`，其中 `i` 从 `1` 遍历到 `n-1`。

### 3. 如何计算 `f[i]` 和 `g[i]` 数组

现在问题的核心是高效地计算出 `f` 和 `g` 数组。`f` 和 `g` 的计算方法是完全对称的，我们以求 `f[i]` 为例（`g` 可以通过对字符串求逆序后用同样方法计算）。

#### 3.1 寻找 AA 子串

一个形如 AA 的子串由两个长度相同的子串拼接而成。我们可以枚举这个重复子串的长度 `len`。

当我们固定 `len` 后，我们可以在原串上每隔 `len` 的位置设置一个“观察点”，例如 `i, i+len, i+2*len, ...`。一个长度为 `2*len` 的 AA 子串必然会跨越两个相邻的观察点 `i` 和 `i+len`。

#### 3.2 利用 LCP 和 LCS

考虑两个相邻的观察点 `i` 和 `j=i+len`。
我们想找到以 `j` 结尾的、跨越 `i` 和 `j` 的 AA 子串的第一个 A 的结尾位置 `k` 的范围。

一个位置 `k` (属于第一个 A) 是可行的，当且仅当 `S[k-len+1...k]` 和 `S[k+1...k+len]` 完全相同。

为了高效地找到所有可行的 `k`，我们引入两个概念：
- `LCP(i, j)`: 以 `i` 开头的后缀和以 `j` 开头的后缀的最长公共前缀长度。
- `LCS(i, j)`: 以 `i` 结尾的前缀和以 `j` 结尾的前缀的最长公共后缀长度。

为了方便计算 LCS，我们可以对原串 `S` 求反串 `S_rev`，然后 `LCS(i, j)` 就等于 `LCP(n-i+1, n-j+1)` 在 `S_rev` 上的值。这样，LCP 和 LCS 都可以通过后缀数组和 RMQ 在 O(1) 时间内查询到。

回到观察点 `i` 和 `j=i+len`。

- `L1 = LCP(i, j)`：表示从 `i` 和 `j` 开始，最多有多少个连续相同的字符。这意味着 `S[i...i+L1-1] == S[j...j+L1-1]`。为了保证 AA 结构，`L1` 不能超过 `len`。`L1` 的最大值是 `min(LCP(i, j), len)`。
- `L2 = LCS(i-1, j-1)`：表示在 `i` 和 `j` 之前，最多有多少个连续相同的字符。这意味着 `S[i-L2...i-1] == S[j-L2...j-1]`。同样，`L2` 也不能超过 `len`。`L2` 的最大值是 `min(LCS(i-1, j-1), len)`。

一个长度为 `2*len` 的 AA 子串 `S[k-len+1...k+len]` (跨越 `i` 和 `j`) 存在的充分必要条件是 `L1 + L2 >= len`。

如果条件满足，那么第一个 A 的结尾位置 `k` 的范围是一个连续的区间。通过画图或推导可以发现，这个 `k` 的范围是 `[j+L1-1-(L1+L2-len), j+L1-1]`。这个区间的长度为 `L1+L2-len+1`。

这些可行的 `k` 值构成了一个连续的区间。我们可以使用差分数组来对这个区间进行区间加 1 的操作。`f[k]` 就是以 `k` 结尾的 AA 子串数量。

#### 3.3 算法流程

1.  **预处理**：
    -   为原串 `S` 构建后缀数组 `SA`，并预处理 ST 表用于 O(1) 查询 LCP。
    -   为 `S` 的反串 `S_rev` 构建后缀数组 `SA_rev`，并预处理 ST 表用于 O(1) 查询 LCS（通过 LCP 实现）。
2.  **计算 `f` 数组 (以 `i` 结尾的 AA 数)**：
    -   初始化差分数组 `diff_f` 为 0。
    -   枚举重复子串的长度 `len` 从 `1` 到 `n/2`。
    -   对于每个 `len`，遍历所有相邻的观察点对 `(i, i+len)`。
    -   计算出跨越该点对的 AA 子串的可行结尾位置区间 `[L, R]`。
    -   如果 `L <= R`，执行 `diff_f[L]++` 和 `diff_f[R+1]--`。
    -   遍历完所有 `len` 后，对 `diff_f` 求前缀和，得到 `f` 数组。
3.  **计算 `g` 数组 (以 `i` 开头的 AA 数)**：
    -   这等同于计算 `S_rev` 上的 `f` 数组（但位置映射关系需要注意，`S` 的开头 `i` 对应 `S_rev` 的结尾 `n-i+1`）。一个更简单的方法是，在步骤 2 中，当我们找到一个 AA 子串 `S[l...r]` 时，它的开头是 `l`，我们也可以对 `l` 的位置进行差分更新。观察可得，`S[k-len+1...k+len]` 的开头位置是 `k-len+1`。当 `k` 的范围是 `[L, R]` 时，开头的范围是 `[L-len+1, R-len+1]`。我们可以用另一个差分数组 `diff_g` 来更新这个区间。
4.  **计算最终答案**：
    -   求和 `Ans = Σ f[i] * g[i+1]` for `i=1 to n-1`。

### 4. 复杂度分析

-   **后缀数组构建**：O(n log n)。
-   **枚举 `len` 和遍历观察点**：外层循环 `len` 从 `1` 到 `n/2`。内层循环对于每个 `len`，遍历 `n/len` 个观察点。总迭代次数为 `n/1 + n/2 + ... + n/n = n * (1 + 1/2 + ... + 1/n)`，这是调和级数，约等于 `n * log(n)`。所以此部分为 O(n log n)。
-   **所有内部操作**：LCP/LCS查询（O(1)）、差分更新（O(1)）、前缀和（O(n)）。
-   **总时间复杂度**：O(n log n)。对于 n ≤ 30000，这是完全可以接受的。
-   **空间复杂度**：O(n)，用于存储后缀数组和各种辅助数组。

# 参考代码 (cpp)

```cpp
#include <bits/stdc++.h>
#define ll long long

const int MAXN = 30005;
const int LOG_MAXN = 15;

struct SuffixArray {
    int n, m;
    int x[MAXN], y[MAXN], c[MAXN], sa[MAXN];
    int rk[MAXN], ht[MAXN], st[MAXN][LOG_MAXN];
    int _log2[MAXN];

    void init_log() {
        _log2[0] = -1;
        for (int i = 1; i < MAXN; ++i) {
            _log2[i] = _log2[i >> 1] + 1;
        }
    }

    void build(char* s, int _n) {
        n = _n;
        m = 'z';
        // Initial sort by first character
        for (int i = 1; i <= n; ++i) c[x[i] = s[i]]++;
        for (int i = 1; i <= m; ++i) c[i] += c[i - 1];
        for (int i = n; i >= 1; --i) sa[c[x[i]]--] = i;
        // Radix sort by second key, then first key
        for (int k = 1; k <= n; k <<= 1) {
            int num = 0;
            // Sort by second key
            for (int i = n - k + 1; i <= n; ++i) y[++num] = i;
            for (int i = 1; i <= n; ++i) if (sa[i] > k) y[++num] = sa[i] - k;
            // Radix sort by first key
            for (int i = 1; i <= m; ++i) c[i] = 0;
            for (int i = 1; i <= n; ++i) c[x[i]]++;
            for (int i = 1; i <= m; ++i) c[i] += c[i - 1];
            for (int i = n; i >= 1; --i) sa[c[x[y[i]]]--] = y[i];
            
            // Update rank
            std::swap(x, y);
            x[sa[1]] = 1; num = 1;
            for (int i = 2; i <= n; ++i) {
                x[sa[i]] = (y[sa[i]] == y[sa[i-1]] && y[sa[i]+k] == y[sa[i-1]+k]) ? num : ++num;
            }
            if (num == n) break;
            m = num;
        }
        // Calculate rank and height array
        for (int i = 1; i <= n; ++i) rk[sa[i]] = i;
        int k = 0;
        for (int i = 1; i <= n; ++i) {
            if (rk[i] == 1) continue;
            if (k) k--;
            int j = sa[rk[i] - 1];
            while (i + k <= n && j + k <= n && s[i + k] == s[j + k]) k++;
            ht[rk[i]] = k;
        }
        // Build ST table for RMQ
        for (int i = 1; i <= n; ++i) st[i][0] = ht[i];
        for (int j = 1; j <= LOG_MAXN; ++j) {
            for (int i = 1; i + (1 << (j - 1)) <= n; ++i) {
                st[i][j] = std::min(st[i][j - 1], st[i + (1 << (j - 1))][j - 1]);
            }
        }
    }

    int rmq(int l, int r) {
        int k = _log2[r - l + 1];
        return std::min(st[l][k], st[r - (1 << k) + 1]);
    }

    // Get Longest Common Prefix of suffixes starting at i and j
    int get_lcp(int i, int j) {
        if (i == j) return n - i + 1;
        int ri = rk[i], rj = rk[j];
        if (ri > rj) std::swap(ri, rj);
        return rmq(ri + 1, rj);
    }
};

SuffixArray sa, sa_rev;
char s[MAXN], s_rev[MAXN];
ll f[MAXN], g[MAXN]; // f: AA ending at i, g: AA starting at i
ll diff_f[MAXN], diff_g[MAXN]; // Difference arrays

void solve_case() {
    scanf("%s", s + 1);
    int n = strlen(s + 1);
    
    // Build SA for original string
    sa.build(s, n);
    
    // Build SA for reversed string
    std::reverse_copy(s + 1, s + n + 1, s_rev + 1);
    sa_rev.build(s_rev, n);
    
    // Clear difference arrays
    for (int i = 1; i <= n; ++i) diff_f[i] = diff_g[i] = 0;

    for (int len = 1; len <= n / 2; ++len) {
        for (int i = 1; i + 2 * len - 1 <= n; i += len) {
            int j = i + len;
            
            // lcp = LCP(i, j)
            // lcs = LCS(i-1, j-1)
            int lcp = std::min(sa.get_lcp(i, j), len);
            int lcs = std::min(sa_rev.get_lcp(n - (i-1) + 1, n - (j-1) + 1), len);

            if (lcp + lcs < len) continue;
            
            // Found some AA substrings of length 2*len crossing i and j.
            // The end of the first A is 'k'.
            // The range of k is [j + lcp - 1 - (lcp + lcs - len), j + lcp - 1]
            // which is [j - lcs - 1 + len, j + lcp - 1]
            int k_start = j - lcs - 1 + len; 
            int k_end = j + lcp - 1;
            
            if (k_start <= k_end) {
                // Update f array: AA ends at k
                diff_f[k_start]++;
                diff_f[k_end + 1]--;
                
                // Update g array: AA starts at k - len + 1
                int s_start = k_start - len + 1;
                int s_end = k_end - len + 1;
                diff_g[s_start]++;
                diff_g[s_end + 1]--;
            }
        }
    }
    
    // Prefix sum to get actual counts
    for (int i = 1; i <= n; ++i) {
        f[i] = f[i-1] + diff_f[i];
        g[i] = g[i-1] + diff_g[i];
    }
    
    ll ans = 0;
    for (int i = 1; i < n; ++i) {
        ans += f[i] * g[i+1];
    }
    
    printf("%lld\n", ans);
}

int main() {
    sa.init_log();
    sa_rev.init_log();
    int T;
    scanf("%d", &T);
    while (T--) {
        solve_case();
    }
    return 0;
}
```

# 核心知识点

* 后缀数组
* LCP
* LCS
* 差分数组
* 调和级数
* 枚举
