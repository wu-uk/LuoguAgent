# P1117 详细题解

### 问题分析

题目要求计算一个字符串 S 的所有子串中，能够被拆分成 AABB 形式的总数。这里的 A 和 B 是非空字符串。例如，对于字符串 `aabaabaa`，`aab` 和 `a` 可以构成 AABB 拆分（`aab` `aab` `a` `a`）。

### 核心思路

1. **问题转化**： AABB 拆分可以看作是由两个连续的 AA 形式子串拼接而成。设 `f[i]` 表示以位置 `i` 结尾的 AA 形式子串的数量，`g[i]` 表示以位置 `i` 开头的 AA 形式子串的数量。那么，答案可以表示为所有可能的分割点 `i` 的 `f[i] * g[i+1]` 之和。

2. **计算 `f` 和 `g`**：
   - 枚举 A 的长度 `len`。
   - 将字符串按 `len` 分块，每块的起始位置为 `len` 的倍数。相邻的两个块（位置 `i` 和 `i+len`）之间可能存在 AA 形式的子串。
   - 对于相邻块 `i` 和 `i+len`，计算它们的最长公共前缀 `LCP(i, i+len)` 和最长公共后缀 `LCS(i-1, i+len-1)`。
   - 如果 `LCP + LCS >= len`，则说明存在 AA 形式的子串。具体来说，AA 子串的起始位置是一个连续的区间，可以通过差分数组高效地更新 `f` 和 `g`。

3. **高效计算 LCP 和 LCS**：
   - 使用后缀数组（Suffix Array）预处理字符串及其反串，以便在 O(1) 时间内查询任意两个后缀的 LCP 和 LCS。
   - 通过哈希方法也可以实现 O(1) 查询，但后缀数组更为经典。

4. **调和级数优化**：
   - 枚举 `len` 时，`len` 的取值范围是 1 到 `n/2`。对于每个 `len`，块的数量约为 `n/len`，因此总复杂度为 O(n log n)，符合调和级数的性质。

### 算法步骤

1. **预处理后缀数组**：
   - 对字符串 S 和其反串 S_rev 分别构建后缀数组，并预处理 LCP 和 LCS 的查询表（ST 表）。

2. **初始化差分数组**：
   - `pre` 和 `nxt` 分别表示 `f` 和 `g` 的差分数组。

3. **枚举 `len`**：
   - 对于每个 `len`，遍历所有块对 `(i, i+len)`。
   - 计算 `LCP(i, i+len)` 和 `LCS(i-1, i+len-1)`。
   - 如果 `LCP + LCS >= len`，则更新差分数组 `pre` 和 `nxt`，表示 AA 子串的起始和结束位置。

4. **计算 `f` 和 `g`**：
   - 对差分数组 `pre` 和 `nxt` 做前缀和，得到 `f` 和 `g`。

5. **统计答案**：
   - 遍历所有可能的分割点 `i`，累加 `f[i] * g[i+1]`。

### 复杂度分析

- 后缀数组构建：O(n log n)。
- 枚举 `len` 和块对：O(n log n)。
- 差分数组更新和前缀和：O(n)。
- 总复杂度：O(n log n)，适用于 n <= 30000 的数据范围。

### 代码实现

以下是后缀数组实现的 C++ 代码：

```cpp
#include <bits/stdc++.h>
using namespace std;

const int MAXN = 3e4 + 5;
int lg[MAXN];

struct SA {
    char s[MAXN];
    int rk[MAXN], sa[MAXN], c[MAXN], x[MAXN], y[MAXN], h[MAXN], n, m, st[MAXN][20];
    void init() {
        memset(x, 0, sizeof x);
        memset(y, 0, sizeof y);
        memset(h, 0, sizeof h);
        memset(st, 0, sizeof st);
        memset(sa, 0, sizeof sa);
        memset(rk, 0, sizeof rk);
        memset(c, 0, sizeof c);
        for (int i = 1; i <= n; i++) x[i] = s[i];
        for (int i = 1; i <= m; i++) c[i] = 0;
        for (int i = 1; i <= n; i++) c[x[i]]++;
        for (int i = 1; i <= m; i++) c[i] += c[i - 1];
        for (int i = n; i >= 1; i--) sa[c[x[i]]--] = i;
        for (int k = 1; k <= n; k <<= 1) {
            int num = 0;
            for (int i = n - k + 1; i <= n; i++) y[++num] = i;
            for (int i = 1; i <= n; i++) if (sa[i] > k) y[++num] = sa[i] - k;
            for (int i = 1; i <= m; i++) c[i] = 0;
            for (int i = 1; i <= n; i++) c[x[i]]++;
            for (int i = 1; i <= m; i++) c[i] += c[i - 1];
            for (int i = n; i >= 1; i--) sa[c[x[y[i]]]--] = y[i];
            swap(x, y);
            x[sa[1]] = 1, num = 1;
            for (int i = 2; i <= n; i++) x[sa[i]] = (y[sa[i]] == y[sa[i - 1]] && y[sa[i] + k] == y[sa[i - 1] + k]) ? num : ++num;
            if (num == n) break;
            m = num;
        }
        for (int i = 1; i <= n; i++) rk[i] = x[i];
        int H = 0;
        for (int i = 1; i <= n; i++) {
            if (rk[i] == 1) continue;
            if (H) H--;
            int j = sa[rk[i] - 1];
            while (i + H <= n && j + H <= n && s[i + H] == s[j + H]) H++;
            h[rk[i]] = H;
        }
        for (int i = 1; i <= n; i++) st[i][0] = h[i];
        for (int j = 1; j <= 18; j++)
            for (int i = 1; i + (1 << j) - 1 <= n; i++)
                st[i][j] = min(st[i][j - 1], st[i + (1 << (j - 1))][j - 1]);
    }
    int LCP(int x, int y) {
        x = rk[x], y = rk[y];
        if (x > y) swap(x, y);
        x++;
        int l = lg[y - x + 1];
        return min(st[x][l], st[y - (1 << l) + 1][l]);
    }
    void ins(char *s, int len) {
        n = len, m = 122;
        for (int i = 1; i <= n; i++) this->s[i] = s[i];
    }
} A, B;

long long pre[MAXN], nxt[MAXN];
char s[MAXN];

int main() {
    lg[0] = -1;
    for (int i = 1; i < MAXN; i++) lg[i] = lg[i >> 1] + 1;
    int T;
    scanf("%d", &T);
    while (T--) {
        scanf("%s", s + 1);
        int n = strlen(s + 1);
        A.ins(s, n);
        reverse(s + 1, s + n + 1);
        B.ins(s, n);
        A.init(), B.init();
        memset(pre, 0, sizeof pre), memset(nxt, 0, sizeof nxt);
        for (int L = 1; L <= n >> 1; L++)
            for (int i = 1; i + L <= n; i += L) {
                int j = i + L;
                int xx = A.LCP(i, j), yy = B.LCP(n - i + 1, n - j + 1);
                xx = min(xx, L), yy = min(yy, L);
                if (xx + yy < L + 1) continue;
                int nowlen = xx + yy - L - 1;
                nxt[i - yy + 1]++, nxt[i - yy + nowlen + 2]--;
                pre[j + xx - nowlen - 1]++, pre[j + xx]--;
            }
        for (int i = 1; i <= n; i++) pre[i] += pre[i - 1], nxt[i] += nxt[i - 1];
        long long ans = 0;
        for (int i = 1; i < n; i++) ans += pre[i] * nxt[i + 1];
        printf("%lld\n", ans);
    }
    return 0;
}
```

### 关键词

- 后缀数组
- LCP/LCS
- 差分数组
- 调和级数

# 参考代码 (cpp)

```cpp
#include <bits/stdc++.h>
using namespace std;

const int MAXN = 3e4 + 5;
int lg[MAXN];

struct SA {
    char s[MAXN];
    int rk[MAXN], sa[MAXN], c[MAXN], x[MAXN], y[MAXN], h[MAXN], n, m, st[MAXN][20];
    void init() {
        memset(x, 0, sizeof x);
        memset(y, 0, sizeof y);
        memset(h, 0, sizeof h);
        memset(st, 0, sizeof st);
        memset(sa, 0, sizeof sa);
        memset(rk, 0, sizeof rk);
        memset(c, 0, sizeof c);
        for (int i = 1; i <= n; i++) x[i] = s[i];
        for (int i = 1; i <= m; i++) c[i] = 0;
        for (int i = 1; i <= n; i++) c[x[i]]++;
        for (int i = 1; i <= m; i++) c[i] += c[i - 1];
        for (int i = n; i >= 1; i--) sa[c[x[i]]--] = i;
        for (int k = 1; k <= n; k <<= 1) {
            int num = 0;
            for (int i = n - k + 1; i <= n; i++) y[++num] = i;
            for (int i = 1; i <= n; i++) if (sa[i] > k) y[++num] = sa[i] - k;
            for (int i = 1; i <= m; i++) c[i] = 0;
            for (int i = 1; i <= n; i++) c[x[i]]++;
            for (int i = 1; i <= m; i++) c[i] += c[i - 1];
            for (int i = n; i >= 1; i--) sa[c[x[y[i]]]--] = y[i];
            swap(x, y);
            x[sa[1]] = 1, num = 1;
            for (int i = 2; i <= n; i++) x[sa[i]] = (y[sa[i]] == y[sa[i - 1]] && y[sa[i] + k] == y[sa[i - 1] + k]) ? num : ++num;
            if (num == n) break;
            m = num;
        }
        for (int i = 1; i <= n; i++) rk[i] = x[i];
        int H = 0;
        for (int i = 1; i <= n; i++) {
            if (rk[i] == 1) continue;
            if (H) H--;
            int j = sa[rk[i] - 1];
            while (i + H <= n && j + H <= n && s[i + H] == s[j + H]) H++;
            h[rk[i]] = H;
        }
        for (int i = 1; i <= n; i++) st[i][0] = h[i];
        for (int j = 1; j <= 18; j++)
            for (int i = 1; i + (1 << j) - 1 <= n; i++)
                st[i][j] = min(st[i][j - 1], st[i + (1 << (j - 1))][j - 1]);
    }
    int LCP(int x, int y) {
        x = rk[x], y = rk[y];
        if (x > y) swap(x, y);
        x++;
        int l = lg[y - x + 1];
        return min(st[x][l], st[y - (1 << l) + 1][l]);
    }
    void ins(char *s, int len) {
        n = len, m = 122;
        for (int i = 1; i <= n; i++) this->s[i] = s[i];
    }
} A, B;

long long pre[MAXN], nxt[MAXN];
char s[MAXN];

int main() {
    lg[0] = -1;
    for (int i = 1; i < MAXN; i++) lg[i] = lg[i >> 1] + 1;
    int T;
    scanf("%d", &T);
    while (T--) {
        scanf("%s", s + 1);
        int n = strlen(s + 1);
        A.ins(s, n);
        reverse(s + 1, s + n + 1);
        B.ins(s, n);
        A.init(), B.init();
        memset(pre, 0, sizeof pre), memset(nxt, 0, sizeof nxt);
        for (int L = 1; L <= n >> 1; L++)
            for (int i = 1; i + L <= n; i += L) {
                int j = i + L;
                int xx = A.LCP(i, j), yy = B.LCP(n - i + 1, n - j + 1);
                xx = min(xx, L), yy = min(yy, L);
                if (xx + yy < L + 1) continue;
                int nowlen = xx + yy - L - 1;
                nxt[i - yy + 1]++, nxt[i - yy + nowlen + 2]--;
                pre[j + xx - nowlen - 1]++, pre[j + xx]--;
            }
        for (int i = 1; i <= n; i++) pre[i] += pre[i - 1], nxt[i] += nxt[i - 1];
        long long ans = 0;
        for (int i = 1; i < n; i++) ans += pre[i] * nxt[i + 1];
        printf("%lld\n", ans);
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
