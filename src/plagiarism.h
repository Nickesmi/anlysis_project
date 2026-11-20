// =====================================================================
// CMP3005 Term Project - Plagiarism detector
// plagiarism.h : shared data types and the functions of every module.
//
// Modules
//   text_processing.cpp  reading files, sentence splitting, tokenizing,
//                        own hash table (FNV-1a, open addressing) for word ids
//   similarity.cpp       matching rule, word-level edit distance (OSA),
//                        banded edit distance, edit descriptions
//   brute_force.cpp      brute-force version (every pair of sentences)
//   efficient.cpp        efficient version (inverted index of main_doc +
//                        pigeonhole filter + banded edit distance)
//   output.cpp           ranking and printing of the results
//   benchmark.cpp        running-time measurements for the report
//   main.cpp             command line, program entry point
// =====================================================================
#ifndef PLAGIARISM_H
#define PLAGIARISM_H

#include <cstdint>
#include <string>
#include <vector>

// ----------------------------- data model -----------------------------

// One sentence of a document.
struct Sentence {
    std::string text;               // original text, whitespace collapsed (printed)
    std::vector<int> ids;           // its words, lower-cased, mapped to integer ids
};

// One input file split into sentences.
struct Document {
    std::string name;               // file name, e.g. "document7.txt"
    std::vector<Sentence> sentences;
};

// Everything the program reads.
struct Corpus {
    Document main;                  // main_doc.txt
    std::vector<Document> docs;     // documents/*.txt in natural order
    int vocabularySize = 0;         // number of distinct (lower-cased) words
};

// Best match of one main-document sentence inside one document.
struct Match {
    int mainIdx = -1;     // sentence index in main_doc.txt
    int docSentIdx = -1;  // sentence index in the document (-1 = no match)
    int distance = -1;    // word-level edit distance of the pair
};

// best[d][i] = best match of main sentence i in document d.
// Both versions of the algorithm fill this table; their tables must be equal.
struct MatchTable {
    std::vector<std::vector<Match>> best;

    void init(int numDocs, int numMainSentences);
    // Keeps the pair with the smallest distance (ties: smallest docSentIdx)
    // so brute force and efficient version always choose the same pair.
    void offer(int doc, int mainIdx, int docSentIdx, int distance);
    bool operator==(const MatchTable& other) const;
};

// --------------------------- text_processing ---------------------------

// Reads main_doc.txt and documents/*.txt below `folder`.
// Returns false (with a message in `error`) if something is missing.
bool loadCorpus(const std::string& folder, Corpus& corpus, std::string& error);

// Splits raw text into sentences, and a sentence into its words as written
// (punctuation removed). Sentence::ids holds exactly these words, lower-cased.
std::vector<std::string> splitSentences(const std::string& text);
std::vector<std::string> splitWords(const std::string& sentence);

// ------------------------------ similarity ------------------------------

// Matching rule: number of word edits allowed between two sentences
// with la and lb words (see similarity.cpp for the definition).
int allowedEdits(int la, int lb);
// Largest allowedEdits(la, lb) over every lb that could still match.
int maxAllowedEdits(int la);

// Full word-level optimal-string-alignment distance, O(|a|*|b|).
int osaDistance(const std::vector<int>& a, const std::vector<int>& b);
// Same distance, but only cells with |i-j| <= k are computed, O(|a|*k).
// Returns k+1 as soon as the distance is known to be larger than k.
int boundedOsaDistance(const std::vector<int>& a, const std::vector<int>& b, int k);

// Human readable list of the edits that turn docSentence into mainSentence,
// e.g. replaced "should" with "must"; inserted "also".
std::string describeEdits(const Sentence& docSentence, const Sentence& mainSentence);

// ------------------------------ algorithms ------------------------------

MatchTable runBruteForce(const Corpus& corpus);
MatchTable runEfficient(const Corpus& corpus);

// -------------------------------- output --------------------------------

void printResults(const Corpus& corpus, const MatchTable& table);

// ------------------------------ benchmark ------------------------------

// Times both versions on growing numbers of documents and writes a CSV.
void runBenchmark(const Corpus& corpus, int repetitions, const std::string& csvPath);

#endif
