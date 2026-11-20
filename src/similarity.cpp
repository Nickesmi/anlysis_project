// =====================================================================
// similarity.cpp
// The matching rule and the word-level edit distance.
//
// MATCHING RULE
//   Both sentences are compared as sequences of lower-cased words
//   (punctuation ignored). The distance between them is the optimal
//   string alignment (OSA) distance on words: the smallest number of
//       - word insertions,
//       - word deletions,
//       - word replacements,
//       - swaps of two neighbouring words
//   that turn one sentence into the other.
//   Two sentences match  <=>  distance <= allowedEdits(la, lb),
//   where allowedEdits = 30% of the word count of the longer sentence
//   (rounded down). So a 4-word sentence may differ by 1 edit, a
//   20-word sentence by 6 edits; sentences of 1-3 words must be equal.
//   (30% was chosen with tools/make_test_set.py: it finds sentences with
//   up to 3 random edits, while no two different sentences of the sample
//   documents are even within 40% of each other, so no false matches.)
// =====================================================================
#include "plagiarism.h"

#include <algorithm>

// Allowed share of edits, in percent of the longer sentence's word count.
static const int EDIT_PERCENT = 30;

int allowedEdits(int la, int lb) {
    const int longer = std::max(la, lb);
    return longer * EDIT_PERCENT / 100;          // integer arithmetic = floor
}

// A document sentence with lb words can only match if |la - lb| <= k,
// because every edit changes the length by at most one word. Longer lb
// gives a larger k, so we walk lb upwards until the length gap exceeds k.
int maxAllowedEdits(int la) {
    int best = allowedEdits(la, la);
    for (int lb = la + 1;; ++lb) {
        const int k = allowedEdits(la, lb);
        if (lb - la > k) break;
        best = std::max(best, k);
    }
    return best;
}

// ---------------------------------------------------------------------
// Full OSA distance (used by the brute-force version).
// d[i][j] = distance between the first i words of a and first j words of b
//   d[i][j] = min( d[i-1][j] + 1,                        delete a[i-1]
//                  d[i][j-1] + 1,                        insert b[j-1]
//                  d[i-1][j-1] + (a[i-1] != b[j-1]),     keep / replace
//                  d[i-2][j-2] + 1  if a[i-1]==b[j-2] and a[i-2]==b[j-1] )  swap
// Only three rows are kept: O(|a|*|b|) time, O(|b|) memory.
// ---------------------------------------------------------------------
int osaDistance(const std::vector<int>& a, const std::vector<int>& b) {
    const int n = (int)a.size(), m = (int)b.size();
    std::vector<int> prev2(m + 1), prev(m + 1), cur(m + 1);
    for (int j = 0; j <= m; ++j) prev[j] = j;
    for (int i = 1; i <= n; ++i) {
        cur[0] = i;
        for (int j = 1; j <= m; ++j) {
            int v = std::min(prev[j] + 1, cur[j - 1] + 1);
            v = std::min(v, prev[j - 1] + (a[i - 1] != b[j - 1] ? 1 : 0));
            if (i > 1 && j > 1 && a[i - 1] == b[j - 2] && a[i - 2] == b[j - 1])
                v = std::min(v, prev2[j - 2] + 1);
            cur[j] = v;
        }
        std::swap(prev2, prev);
        std::swap(prev, cur);
    }
    return prev[m];
}

// ---------------------------------------------------------------------
// Banded OSA distance (used by the efficient version).
// If the distance is <= k, the optimal alignment never leaves the band
// |i - j| <= k, so only 2k+1 cells per row are computed: O(|a| * k).
// Values are capped at k+1 ("too far"), and we stop early as soon as a
// whole row is > k, because values never decrease further down.
// ---------------------------------------------------------------------
int boundedOsaDistance(const std::vector<int>& a, const std::vector<int>& b, int k) {
    const int n = (int)a.size(), m = (int)b.size();
    const int TOO_FAR = k + 1;
    if (n - m > k || m - n > k) return TOO_FAR;            // length filter

    // Reused buffers: the program is single-threaded.
    static std::vector<int> buf0, buf1, buf2;
    if ((int)buf0.size() < m + 2) { buf0.resize(m + 2); buf1.resize(m + 2); buf2.resize(m + 2); }
    int* prev2 = buf0.data();
    int* prev = buf1.data();
    int* cur = buf2.data();

    // Row 0: d[0][j] = j inside the band.
    for (int j = 0; j <= std::min(m, k); ++j) prev[j] = j;
    if (k + 1 <= m) prev[k + 1] = TOO_FAR;

    for (int i = 1; i <= n; ++i) {
        const int lo = std::max(1, i - k), hi = std::min(m, i + k);
        cur[0] = (i <= k) ? i : TOO_FAR;                     // column 0
        if (lo > 1) cur[lo - 1] = TOO_FAR;                   // left edge of band
        int rowMin = cur[0];
        for (int j = lo; j <= hi; ++j) {
            int v = std::min(prev[j] + 1, cur[j - 1] + 1);
            v = std::min(v, prev[j - 1] + (a[i - 1] != b[j - 1] ? 1 : 0));
            if (i > 1 && j > 1 && a[i - 1] == b[j - 2] && a[i - 2] == b[j - 1])
                v = std::min(v, prev2[j - 2] + 1);
            if (v > TOO_FAR) v = TOO_FAR;
            cur[j] = v;
            if (v < rowMin) rowMin = v;
        }
        if (hi + 1 <= m) cur[hi + 1] = TOO_FAR;              // right edge of band
        if (rowMin > k) return TOO_FAR;                      // early termination
        int* t = prev2; prev2 = prev; prev = cur; cur = t;   // rotate rows
    }
    return std::min(prev[m], TOO_FAR);
}

// ---------------------------------------------------------------------
// Edit description for printing: full DP table, then walk back from the
// bottom-right corner and name every step that costs 1.
// Source = document sentence, target = main_doc sentence, so the words
// are reported as "what the copier did to the original sentence".
// ---------------------------------------------------------------------
std::string describeEdits(const Sentence& docSentence, const Sentence& mainSentence) {
    const std::vector<int>& x = docSentence.ids;
    const std::vector<int>& y = mainSentence.ids;
    const int n = (int)x.size(), m = (int)y.size();
    std::vector<std::vector<int>> d(n + 1, std::vector<int>(m + 1, 0));
    for (int i = 0; i <= n; ++i) d[i][0] = i;
    for (int j = 0; j <= m; ++j) d[0][j] = j;
    for (int i = 1; i <= n; ++i)
        for (int j = 1; j <= m; ++j) {
            int v = std::min(d[i - 1][j] + 1, d[i][j - 1] + 1);
            v = std::min(v, d[i - 1][j - 1] + (x[i - 1] != y[j - 1] ? 1 : 0));
            if (i > 1 && j > 1 && x[i - 1] == y[j - 2] && x[i - 2] == y[j - 1])
                v = std::min(v, d[i - 2][j - 2] + 1);
            d[i][j] = v;
        }

    // Words as written (same tokenizer as the ids, so positions line up).
    const std::vector<std::string> xw = splitWords(docSentence.text);
    const std::vector<std::string> yw = splitWords(mainSentence.text);
    auto q = [](const std::string& w) { return "\"" + w + "\""; };
    std::vector<std::string> ops;                       // collected backwards
    int i = n, j = m;
    while (i > 0 || j > 0) {
        if (i > 0 && j > 0 && x[i - 1] == y[j - 1] && d[i][j] == d[i - 1][j - 1]) {
            --i; --j;                                   // same word
        } else if (i > 1 && j > 1 && x[i - 1] == y[j - 2] && x[i - 2] == y[j - 1] &&
                   d[i][j] == d[i - 2][j - 2] + 1) {
            ops.push_back("swapped " + q(xw[i - 2]) + " and " + q(xw[i - 1]));
            i -= 2; j -= 2;
        } else if (i > 0 && j > 0 && d[i][j] == d[i - 1][j - 1] + 1) {
            ops.push_back("replaced " + q(xw[i - 1]) + " with " + q(yw[j - 1]));
            --i; --j;
        } else if (i > 0 && d[i][j] == d[i - 1][j] + 1) {
            ops.push_back("deleted " + q(xw[i - 1]));
            --i;
        } else {
            ops.push_back("inserted " + q(yw[j - 1]));
            --j;
        }
    }
    std::string out;
    for (int t = (int)ops.size() - 1; t >= 0; --t) {
        if (!out.empty()) out += "; ";
        out += ops[t];
    }
    return out;
}

// ----------------------------- MatchTable -----------------------------

void MatchTable::init(int numDocs, int numMainSentences) {
    best.assign(numDocs, std::vector<Match>(numMainSentences));
    for (int d = 0; d < numDocs; ++d)
        for (int i = 0; i < numMainSentences; ++i) best[d][i].mainIdx = i;
}

void MatchTable::offer(int doc, int mainIdx, int docSentIdx, int distance) {
    Match& m = best[doc][mainIdx];
    if (m.docSentIdx < 0 || distance < m.distance ||
        (distance == m.distance && docSentIdx < m.docSentIdx)) {
        m.docSentIdx = docSentIdx;
        m.distance = distance;
    }
}

bool MatchTable::operator==(const MatchTable& other) const {
    if (best.size() != other.best.size()) return false;
    for (size_t d = 0; d < best.size(); ++d) {
        if (best[d].size() != other.best[d].size()) return false;
        for (size_t i = 0; i < best[d].size(); ++i) {
            const Match& p = best[d][i];
            const Match& q = other.best[d][i];
            if (p.docSentIdx != q.docSentIdx || p.distance != q.distance) return false;
        }
    }
    return true;
}
