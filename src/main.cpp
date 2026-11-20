// =====================================================================
// main.cpp
// CMP3005 Term Project - Plagiarism detector (entry point)
//
// The program takes no user input. Run it inside the folder that holds
// main_doc.txt and documents/ :
//
//   plagiarism                  efficient version (default)
//   plagiarism brute            brute-force version
//   plagiarism compare          both versions, checks equal results, speedup
//   plagiarism benchmark [r]    timings for >= 5 numbers of documents,
//                               best of r runs (default 3), -> benchmark.csv
//
// Optional: --dir <folder> reads the input from another folder.
// =====================================================================
#include "plagiarism.h"

#include <chrono>
#include <cstdio>
#include <cstdlib>
#include <string>

namespace {

using Clock = std::chrono::steady_clock;

double millisecondsSince(Clock::time_point start) {
    return std::chrono::duration<double, std::milli>(Clock::now() - start).count();
}

void printUsage() {
    std::printf(
        "usage: plagiarism [efficient | brute | compare | benchmark [repetitions]] [--dir <folder>]\n"
        "Reads <folder>/main_doc.txt and <folder>/documents/*.txt (default folder: current folder).\n");
}

void printHeader(const Corpus& corpus, const char* version) {
    long long docSentences = 0;
    for (const Document& d : corpus.docs) docSentences += (long long)d.sentences.size();
    std::printf("Plagiarism detector (%s version)\n", version);
    std::printf("main_doc.txt: %d sentences | documents/: %d files, %lld sentences\n\n",
                (int)corpus.main.sentences.size(), (int)corpus.docs.size(), docSentences);
}

}  // namespace

int main(int argc, char** argv) {
    std::string mode = "efficient";
    std::string folder = ".";
    int repetitions = 3;

    for (int i = 1; i < argc; ++i) {
        const std::string arg = argv[i];
        if (arg == "--dir" && i + 1 < argc) {
            folder = argv[++i];
        } else if (arg == "efficient" || arg == "brute" || arg == "compare" || arg == "benchmark") {
            mode = arg;
        } else if (mode == "benchmark" && std::atoi(arg.c_str()) > 0) {
            repetitions = std::atoi(arg.c_str());
        } else {
            printUsage();
            return 1;
        }
    }

    // 1. Read and preprocess all files (same for both versions).
    const auto loadStart = Clock::now();
    Corpus corpus;
    std::string error;
    if (!loadCorpus(folder, corpus, error)) {
        std::fprintf(stderr, "Error: %s\n", error.c_str());
        printUsage();
        return 1;
    }
    const double loadMs = millisecondsSince(loadStart);

    if (mode == "benchmark") {
        runBenchmark(corpus, repetitions, "benchmark.csv");
        return 0;
    }

    // 2. Find the matches.
    MatchTable table;
    double bruteMs = -1, efficientMs = -1;
    if (mode == "brute" || mode == "compare") {
        const auto start = Clock::now();
        table = runBruteForce(corpus);
        bruteMs = millisecondsSince(start);
    }
    if (mode == "efficient" || mode == "compare") {
        const auto start = Clock::now();
        MatchTable fast = runEfficient(corpus);
        efficientMs = millisecondsSince(start);
        if (mode == "compare" && !(fast == table)) {
            std::fprintf(stderr, "Error: brute-force and efficient results differ!\n");
            return 2;
        }
        table = std::move(fast);
    }

    // 3. Print the ranked documents and the running times.
    printHeader(corpus, mode == "brute" ? "brute-force" : "efficient");
    printResults(corpus, table);

    std::printf("\nReading and preprocessing the files: %.2f ms\n", loadMs);
    if (bruteMs >= 0) std::printf("Matching, brute-force version:       %.2f ms\n", bruteMs);
    if (efficientMs >= 0) std::printf("Matching, efficient version:         %.2f ms\n", efficientMs);
    if (mode == "compare")
        std::printf("Both versions give identical results; speedup %.1fx\n",
                    efficientMs > 0 ? bruteMs / efficientMs : 0.0);
    return 0;
}
