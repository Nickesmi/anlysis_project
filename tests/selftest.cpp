// =====================================================================
// selftest.cpp - checks of the building blocks (run with: make test)
//   1. sentence splitting and word splitting on tricky inputs
//   2. edit distance on hand-made examples (each edit type)
//   3. banded distance == full distance (capped at k+1) on random inputs
//   4. edit descriptions
// =====================================================================
#include "plagiarism.h"

#include <cstdio>
#include <random>

static int failures = 0;

static void check(bool ok, const char* what) {
    std::printf("%s  %s\n", ok ? "ok  " : "FAIL", what);
    if (!ok) ++failures;
}

static std::vector<int> ids(const std::string& s) {
    // Simple ids for tests: one id per distinct lower-case word.
    static std::vector<std::string> seen;
    std::vector<int> out;
    for (std::string w : splitWords(s)) {
        for (char& c : w) c = (char)((c >= 'A' && c <= 'Z') ? c - 'A' + 'a' : c);
        int id = -1;
        for (int i = 0; i < (int)seen.size(); ++i)
            if (seen[i] == w) id = i;
        if (id < 0) { id = (int)seen.size(); seen.push_back(w); }
        out.push_back(id);
    }
    return out;
}

int main() {
    // 1. Splitting
    auto s1 = splitSentences("The ship sailed. Mr. Blair arrived at St. Louis! Was it U.S. policy? Yes.");
    check(s1.size() == 4, "abbreviations Mr. St. U.S. do not end a sentence");
    auto s2 = splitSentences("He said \"we will do.\" The next one. And 1.5 percent.\n\nNew paragraph");
    check(s2.size() == 3 && s2[0] == "He said \"we will do.\" The next one.",
          "a closing quote after '.' does not end a sentence; 1.5 is not a boundary");
    check(s2.size() == 3 && s2[2] == "New paragraph", "an empty line ends a sentence");
    auto w = splitWords("Her Majesty's well-nigh 1,878 (careful) - attention.");
    check(w.size() == 7 && w[1] == "Majesty's" && w[2] == "well-nigh", "words keep inner ' and -");

    // 2. Distance: one example per edit type
    const auto base = ids("the report should receive the careful attention");
    check(osaDistance(base, base) == 0, "identical sentences: distance 0");
    check(osaDistance(base, ids("the report must receive the careful attention")) == 1, "replace: 1");
    check(osaDistance(base, ids("the report should receive the attention")) == 1, "delete: 1");
    check(osaDistance(base, ids("the report should also receive the careful attention")) == 1, "insert: 1");
    check(osaDistance(base, ids("the report should receive the attention careful")) == 1, "swap: 1");
    check(osaDistance(base, ids("the report must receive the attention careful")) == 2, "replace + swap: 2");
    check(allowedEdits(3, 3) == 0 && allowedEdits(4, 4) == 1 && allowedEdits(20, 18) == 6,
          "allowed edits = 30% of the longer sentence");

    // 3. Banded distance against full distance on random word lists
    std::mt19937 rng(12345);
    int mismatches = 0;
    for (int t = 0; t < 200000; ++t) {
        std::vector<int> a(rng() % 25), b(rng() % 25);
        const int alphabet = 1 + rng() % 5;
        for (int& x : a) x = rng() % alphabet;
        for (int& x : b) x = rng() % alphabet;
        const int k = rng() % 8;
        const int full = osaDistance(a, b);
        if (boundedOsaDistance(a, b, k) != (full <= k ? full : k + 1)) ++mismatches;
    }
    check(mismatches == 0, "banded distance equals full distance on 200000 random pairs");

    // 4. Edit descriptions
    Sentence doc, mainS;
    doc.text = "The report should receive the careful attention of Congress.";
    mainS.text = "The report must receive the attention careful of Congress.";
    doc.ids = ids(doc.text);
    mainS.ids = ids(mainS.text);
    check(describeEdits(doc, mainS) == "replaced \"should\" with \"must\"; swapped \"careful\" and \"attention\"",
          "edit description names the edits");

    std::printf("\n%s (%d failed)\n", failures == 0 ? "ALL TESTS PASSED" : "SOME TESTS FAILED", failures);
    return failures == 0 ? 0 : 1;
}
