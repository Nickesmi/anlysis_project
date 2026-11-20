// =====================================================================
// benchmark.cpp
// Empirical analysis: runs the brute-force and the efficient version on
// the first m documents for several values of m (at least 5 sizes),
// checks that both give identical results and prints the running times
// in milliseconds as a table; the same numbers are written to a CSV file
// that can be plotted for the report.
// Only the matching work is timed (the efficient time includes building
// the index); reading the files is the same for both and is excluded.
// =====================================================================
#include "plagiarism.h"

#include <algorithm>
#include <chrono>
#include <cstdio>
#include <fstream>

namespace {

double millisecondsSince(std::chrono::steady_clock::time_point start) {
    return std::chrono::duration<double, std::milli>(std::chrono::steady_clock::now() - start).count();
}

// Runs `algorithm` up to `repetitions` times and returns the fastest time.
// Very slow runs (> 3 s) are not repeated.
template <typename Algorithm>
double timeIt(Algorithm algorithm, const Corpus& corpus, int repetitions, MatchTable& result) {
    double best = -1;
    for (int r = 0; r < repetitions; ++r) {
        auto start = std::chrono::steady_clock::now();
        result = algorithm(corpus);
        const double ms = millisecondsSince(start);
        if (best < 0 || ms < best) best = ms;
        if (ms > 3000) break;
    }
    return best;
}

}  // namespace

void runBenchmark(const Corpus& corpus, int repetitions, const std::string& csvPath) {
    const int total = (int)corpus.docs.size();
    const int points = std::min(total, 8);

    std::vector<int> sizes;
    for (int p = 1; p <= points; ++p) {
        const int m = (int)((long long)total * p / points);
        if (m > 0 && (sizes.empty() || sizes.back() != m)) sizes.push_back(m);
    }

    std::ofstream csv(csvPath);
    csv << "documents,document_sentences,main_sentences,brute_force_ms,efficient_ms,speedup,same_result\n";

    std::printf("Benchmark: main_doc.txt has %d sentences, best of %d runs per size\n\n",
                (int)corpus.main.sentences.size(), repetitions);
    std::printf("%10s %12s %16s %14s %10s %8s\n", "documents", "doc sents", "brute force ms", "efficient ms",
                "speedup", "same");

    for (int m : sizes) {
        Corpus sub;
        sub.main = corpus.main;
        sub.vocabularySize = corpus.vocabularySize;
        sub.docs.assign(corpus.docs.begin(), corpus.docs.begin() + m);
        long long docSentences = 0;
        for (const Document& d : sub.docs) docSentences += (long long)d.sentences.size();

        MatchTable brute, fast;
        const double bruteMs = timeIt(runBruteForce, sub, repetitions, brute);
        const double fastMs = timeIt(runEfficient, sub, repetitions, fast);
        const bool same = (brute == fast);
        const double speedup = fastMs > 0 ? bruteMs / fastMs : 0;

        std::printf("%10d %12lld %16.2f %14.3f %9.1fx %8s\n", m, docSentences, bruteMs, fastMs, speedup,
                    same ? "yes" : "NO");
        csv << m << ',' << docSentences << ',' << sub.main.sentences.size() << ',' << bruteMs << ','
            << fastMs << ',' << speedup << ',' << (same ? "yes" : "no") << '\n';
    }
    std::printf("\nResults written to %s\n", csvPath.c_str());
}
