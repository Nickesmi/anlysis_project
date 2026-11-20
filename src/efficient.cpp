// =====================================================================
// efficient.cpp
// Efficient version: inverted index of main_doc.txt + pigeonhole filter
// + banded edit distance. Every document sentence is read only once.
//
// 1. INDEX the small side, main_doc.txt  (O(n * w))
//      postings[word] = main sentences that contain the word (each once)
//      byLength[L]    = main sentences with exactly L words
//
// 2. SCAN every sentence b of every document once, k = maxAllowedEdits(|b|).
//    Pigeonhole argument: if b matches a main sentence a, at most k edits
//    were made and every edit removes at most one word of b from a (a swap
//    removes none). So among ANY k+1 distinct words of b, at least one
//    also occurs in a.
//      - If k+1 distinct words of b occur nowhere in main_doc.txt, b
//        cannot match anything and is skipped. This is the case for
//        almost every sentence, usually after reading only a few words.
//      - Otherwise the probe set is: the words of b missing from main_doc
//        (empty posting lists) plus the rarest present words, k+1 in all.
//        Candidates = main sentences in the posting lists of the probe set.
//      - If b has at most k distinct words (very short sentences) the
//        argument does not apply; then every main sentence whose length is
//        within k of |b| is a candidate (from byLength).
//    No true match is ever lost, so the result equals the brute force.
//
// 3. VERIFY each candidate with three checks, cheapest first:
//      length filter       ||a| - |b|| <= k                      O(1)
//      bag-of-words filter max(|a|,|b|) - common words <= k      O(w)
//      banded edit distance boundedOsaDistance(a, b, k) <= k     O(w * k)
// =====================================================================
#include "plagiarism.h"

#include <algorithm>

namespace {

class MainDocIndex {
public:
    MainDocIndex(const Document& mainDoc, int vocabularySize)
        : main_(mainDoc), postings_(vocabularySize), wordSeen_(vocabularySize, -1) {
        const std::vector<Sentence>& sentences = main_.sentences;
        for (int i = 0; i < (int)sentences.size(); ++i) {
            for (int w : sentences[i].ids) {
                if (wordSeen_[w] == i) continue;          // each sentence once per word
                wordSeen_[w] = i;
                postings_[w].push_back(i);
            }
            const int len = (int)sentences[i].ids.size();
            if (len >= (int)byLength_.size()) byLength_.resize(len + 1);
            byLength_[len].push_back(i);
            sortedIds_.push_back(sentences[i].ids);
            std::sort(sortedIds_.back().begin(), sortedIds_.back().end());
        }
        std::fill(wordSeen_.begin(), wordSeen_.end(), -1);
        checkedBy_.assign(sentences.size(), -1);
    }

    // Finds the main sentences that match sentence `s` of document `doc`.
    // `stamp` must be different for every call (used to de-duplicate).
    void search(int doc, int s, const std::vector<int>& b, int stamp, MatchTable& table) {
        const int k = maxAllowedEdits((int)b.size());

        // Distinct words of b, split into "missing from main_doc" and "present".
        // As soon as k+1 distinct words are missing, b cannot match anything
        // (pigeonhole), so we stop reading it.
        int missing = 0;
        present_.clear();
        for (int w : b) {
            if (wordSeen_[w] == stamp) continue;
            wordSeen_[w] = stamp;
            if (!postings_[w].empty()) present_.push_back(w);
            else if (++missing > k) return;
        }
        const int distinct = missing + (int)present_.size();
        sortedB_.assign(b.begin(), b.end());             // for the bag-of-words filter
        std::sort(sortedB_.begin(), sortedB_.end());

        if (distinct >= k + 1) {
            const int probes = k + 1 - missing;           // rarest present words to probe
            std::partial_sort(present_.begin(), present_.begin() + probes, present_.end(),
                              [this](int x, int y) { return postings_[x].size() < postings_[y].size(); });
            for (int t = 0; t < probes; ++t)
                for (int a : postings_[present_[t]]) verify(a, doc, s, b, stamp, table);
        } else {
            // Too few distinct words for the pigeonhole argument: length buckets.
            const int lb = (int)b.size();
            for (int len = std::max(0, lb - k); len <= lb + k && len < (int)byLength_.size(); ++len)
                for (int a : byLength_[len]) verify(a, doc, s, b, stamp, table);
        }
    }

private:
    void verify(int a, int doc, int s, const std::vector<int>& b, int stamp, MatchTable& table) {
        if (checkedBy_[a] == stamp) return;               // already checked for this b
        checkedBy_[a] = stamp;
        const std::vector<int>& av = main_.sentences[a].ids;
        const int la = (int)av.size(), lb = (int)b.size();
        const int k = allowedEdits(la, lb);
        if (la - lb > k || lb - la > k) return;                       // length filter
        if (std::max(la, lb) - commonWords(sortedIds_[a], sortedB_) > k) return;  // bag filter
        const int dist = boundedOsaDistance(av, b, k);
        if (dist <= k) table.offer(doc, a, s, dist);
    }

    // Size of the multiset intersection of two sorted word lists, O(|x|+|y|).
    // Every edit adds at most one non-shared word, so
    // distance >= max(|a|, |b|) - commonWords(a, b): a cheap lower bound.
    static int commonWords(const std::vector<int>& x, const std::vector<int>& y) {
        int i = 0, j = 0, common = 0;
        while (i < (int)x.size() && j < (int)y.size()) {
            if (x[i] < y[j]) ++i;
            else if (y[j] < x[i]) ++j;
            else { ++common; ++i; ++j; }
        }
        return common;
    }

    const Document& main_;
    std::vector<std::vector<int>> postings_;   // word id -> main sentences containing it
    std::vector<std::vector<int>> byLength_;   // word count -> main sentences
    std::vector<int> wordSeen_;                // word id -> last stamp (distinct words of b)
    std::vector<int> checkedBy_;               // main sentence -> last stamp that verified it
    std::vector<std::vector<int>> sortedIds_;  // main sentence -> its word ids, sorted
    std::vector<int> present_;                 // scratch: distinct words of b found in main_doc
    std::vector<int> sortedB_;                 // scratch: word ids of b, sorted
};

}  // namespace

MatchTable runEfficient(const Corpus& corpus) {
    MatchTable table;
    table.init((int)corpus.docs.size(), (int)corpus.main.sentences.size());

    MainDocIndex index(corpus.main, corpus.vocabularySize);
    int stamp = 0;
    for (int d = 0; d < (int)corpus.docs.size(); ++d) {
        const std::vector<Sentence>& sentences = corpus.docs[d].sentences;
        for (int s = 0; s < (int)sentences.size(); ++s) index.search(d, s, sentences[s].ids, stamp++, table);
    }
    return table;
}
