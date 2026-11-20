// =====================================================================
// brute_force.cpp
// Brute-force version: every sentence of main_doc.txt is compared with
// every sentence of every document using the full edit-distance table.
//
//   for each sentence a of main_doc.txt                 (n sentences)
//       for each document D                             (m documents)
//           for each sentence b of D                    (s sentences per doc)
//               dist = osaDistance(a, b)                (O(w^2) for w words)
//               if dist <= allowedEdits(|a|, |b|): record (D, a, b, dist)
//
// Time: O(n * m * s * w^2)
// =====================================================================
#include "plagiarism.h"

MatchTable runBruteForce(const Corpus& corpus) {
    const std::vector<Sentence>& mainSentences = corpus.main.sentences;
    MatchTable table;
    table.init((int)corpus.docs.size(), (int)mainSentences.size());

    for (int i = 0; i < (int)mainSentences.size(); ++i) {
        const std::vector<int>& a = mainSentences[i].ids;
        for (int d = 0; d < (int)corpus.docs.size(); ++d) {
            const std::vector<Sentence>& docSentences = corpus.docs[d].sentences;
            for (int s = 0; s < (int)docSentences.size(); ++s) {
                const std::vector<int>& b = docSentences[s].ids;
                const int dist = osaDistance(a, b);
                if (dist <= allowedEdits((int)a.size(), (int)b.size()))
                    table.offer(d, i, s, dist);
            }
        }
    }
    return table;
}
