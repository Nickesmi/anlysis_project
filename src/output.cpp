// =====================================================================
// output.cpp
// Ranks the documents and prints one block per document:
//
// 1) document7.txt   similarity 42.5%   (17 of 40 sentences)
//    "<sentence in main_doc.txt>"
//    "<matching sentence in document7.txt>"   [edited: ...]
//    ... up to the 5 most similar sentence pairs
//
// Similarity rate = matched sentences of main_doc.txt / all sentences
// of main_doc.txt * 100, one decimal.
// =====================================================================
#include "plagiarism.h"

#include <algorithm>
#include <cstdio>

static const int MAX_PAIRS_SHOWN = 5;

// Percentage with one decimal, rounded half up using integers only.
static std::string percent(int part, int whole) {
    if (whole == 0) return "0.0";
    const long long tenths = ((long long)part * 1000 + whole / 2) / whole;
    return std::to_string(tenths / 10) + "." + std::to_string(tenths % 10);
}

// Pair p is more similar than q if its distance relative to the longer
// sentence is smaller: dp/Lp < dq/Lq  <=>  dp*Lq < dq*Lp.
static bool moreSimilar(const Match& p, int lp, const Match& q, int lq) {
    const long long left = (long long)p.distance * lq, right = (long long)q.distance * lp;
    if (left != right) return left < right;
    return p.mainIdx < q.mainIdx;
}

void printResults(const Corpus& corpus, const MatchTable& table) {
    const std::vector<Sentence>& mainSentences = corpus.main.sentences;
    const int n = (int)mainSentences.size();
    const int numDocs = (int)corpus.docs.size();

    // Matched main sentences per document.
    std::vector<std::vector<Match>> matched(numDocs);
    for (int d = 0; d < numDocs; ++d)
        for (const Match& m : table.best[d])
            if (m.docSentIdx >= 0) matched[d].push_back(m);

    // Rank documents: most matched sentences first, ties in file order.
    std::vector<int> order(numDocs);
    for (int d = 0; d < numDocs; ++d) order[d] = d;
    std::stable_sort(order.begin(), order.end(),
                     [&](int x, int y) { return matched[x].size() > matched[y].size(); });

    for (int rank = 0; rank < numDocs; ++rank) {
        const int d = order[rank];
        const Document& doc = corpus.docs[d];
        std::vector<Match>& pairs = matched[d];
        std::printf("%d) %s   similarity %s%%   (%d of %d sentences)\n", rank + 1, doc.name.c_str(),
                    percent((int)pairs.size(), n).c_str(), (int)pairs.size(), n);

        // The most similar pairs first.
        auto pairLength = [&](const Match& m) {
            return std::max(mainSentences[m.mainIdx].ids.size(),
                            doc.sentences[m.docSentIdx].ids.size());
        };
        std::sort(pairs.begin(), pairs.end(), [&](const Match& p, const Match& q) {
            return moreSimilar(p, (int)pairLength(p), q, (int)pairLength(q));
        });

        const int shown = std::min((int)pairs.size(), MAX_PAIRS_SHOWN);
        for (int t = 0; t < shown; ++t) {
            const Sentence& ms = mainSentences[pairs[t].mainIdx];
            const Sentence& ds = doc.sentences[pairs[t].docSentIdx];
            std::printf("   \"%s\"\n", ms.text.c_str());
            if (pairs[t].distance == 0)
                std::printf("   \"%s\"\n", ds.text.c_str());
            else
                std::printf("   \"%s\"   [edited: %s]\n", ds.text.c_str(), describeEdits(ds, ms).c_str());
        }
        if ((int)pairs.size() > shown) std::printf("   ... and %d more pairs\n", (int)pairs.size() - shown);
    }

    // Sentences of main_doc.txt copied from at least one document.
    int copied = 0;
    for (int i = 0; i < n; ++i) {
        bool found = false;
        for (int d = 0; d < numDocs && !found; ++d) found = table.best[d][i].docSentIdx >= 0;
        if (found) ++copied;
    }
    std::printf("\n%d of %d sentences of main_doc.txt (%s%%) match a sentence in at least one document.\n",
                copied, n, percent(copied, n).c_str());
}
