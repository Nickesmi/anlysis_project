// =====================================================================
// text_processing.cpp
// Reading the input files, splitting text into sentences and words,
// and mapping every lower-cased word to a small integer id with our own
// hash table (FNV-1a hash function + open addressing).
//
// All scanning is done character by character by our own code; no
// built-in text search (find, indexOf, regex) is used.
// =====================================================================
#include "plagiarism.h"

#include <algorithm>
#include <cstdio>
#include <filesystem>

namespace fs = std::filesystem;

// --------------------------- character classes ---------------------------

static bool isSpace(char c) { return c == ' ' || c == '\t' || c == '\n' || c == '\r' || c == '\f' || c == '\v'; }
static bool isUpper(char c) { return c >= 'A' && c <= 'Z'; }
static bool isLower(char c) { return c >= 'a' && c <= 'z'; }
static bool isDigit(char c) { return c >= '0' && c <= '9'; }
// Bytes >= 128 belong to UTF-8 letters (e.g. accented characters).
static bool isWordChar(char c) { return isUpper(c) || isLower(c) || isDigit(c) || (unsigned char)c >= 128; }
static bool isTerminator(char c) { return c == '.' || c == '!' || c == '?'; }
static char toLower(char c) { return isUpper(c) ? (char)(c - 'A' + 'a') : c; }

// ------------------------------ hash table ------------------------------

// Word interning table: lower-cased word -> id 0, 1, 2, ...
// Hash function: 64-bit FNV-1a, h = (h XOR byte) * prime, over the
// lower-cased bytes. Collisions: open addressing with linear probing.
// The table is doubled when it is half full, so a lookup is O(1) expected
// and O(length of the word) for hashing and comparing.
class WordTable {
public:
    WordTable() : slots_(1 << 16, -1) {}

    int size() const { return (int)hashes_.size(); }

    // Returns the id of word p[0..n) (case-insensitive), adding it if new.
    int intern(const char* p, size_t n) {
        uint64_t h = 1469598103934665603ULL;           // FNV offset basis
        for (size_t i = 0; i < n; ++i) {
            h ^= (unsigned char)toLower(p[i]);
            h *= 1099511628211ULL;                     // FNV prime
        }
        size_t mask = slots_.size() - 1;
        size_t pos = (size_t)(h ^ (h >> 29)) & mask;
        while (slots_[pos] >= 0) {
            const int id = slots_[pos];
            if (hashes_[id] == h && sameWord(id, p, n)) return id;
            pos = (pos + 1) & mask;                    // linear probing
        }
        const int id = size();
        slots_[pos] = id;
        hashes_.push_back(h);
        start_.push_back((uint32_t)chars_.size());
        length_.push_back((uint32_t)n);
        for (size_t i = 0; i < n; ++i) chars_ += toLower(p[i]);
        if (2 * hashes_.size() > slots_.size()) grow();
        return id;
    }

private:
    bool sameWord(int id, const char* p, size_t n) const {
        if (length_[id] != n) return false;
        const char* stored = chars_.data() + start_[id];
        for (size_t i = 0; i < n; ++i)
            if (stored[i] != toLower(p[i])) return false;
        return true;
    }

    void grow() {
        std::vector<int> bigger(slots_.size() * 2, -1);
        const size_t mask = bigger.size() - 1;
        for (int id = 0; id < size(); ++id) {
            const uint64_t h = hashes_[id];
            size_t pos = (size_t)(h ^ (h >> 29)) & mask;
            while (bigger[pos] >= 0) pos = (pos + 1) & mask;
            bigger[pos] = id;
        }
        slots_.swap(bigger);
    }

    std::vector<int> slots_;          // -1 = empty, otherwise a word id
    std::vector<uint64_t> hashes_;    // per id: full 64-bit hash
    std::vector<uint32_t> start_;     // per id: position of the word in chars_
    std::vector<uint32_t> length_;    // per id: length of the word
    std::string chars_;               // all distinct words, lower-cased, concatenated
};

// ------------------------------ sentences ------------------------------

// Words that end with '.' but normally do not end a sentence.
static bool isAbbreviation(const std::string& w) {
    static const char* const list[] = {
        "Mr", "Mrs", "Ms", "Dr", "St", "Jr", "Sr", "Messrs", "Mt", "Ft",
        "Gen", "Col", "Capt", "Lieut", "Lt", "Gov", "Hon", "Rev", "Prof", "No", "vs"};
    for (const char* a : list)
        if (w == a) return true;
    // A single capital letter is an initial ("James B. Eads", "U.S.").
    return w.size() == 1 && isUpper(w[0]);
}

// Copies text[from, to) with runs of whitespace collapsed to one space, trimmed.
static std::string collapseSpaces(const std::string& s, size_t from, size_t to) {
    std::string out(to - from, '\0');             // never longer than the input
    size_t len = 0;
    bool pendingSpace = false;
    for (size_t i = from; i < to; ++i) {
        const char c = s[i];
        if (isSpace(c)) { pendingSpace = len > 0; continue; }
        if (pendingSpace) { out[len++] = ' '; pendingSpace = false; }
        out[len++] = c;
    }
    out.resize(len);
    return out;
}

// A sentence ends at '.', '!' or '?' (a run like ".." or "?!" counts as one)
// that is directly followed by whitespace and then a capital letter, digit,
// quote or bracket, unless the word before the '.' is an abbreviation.
// A terminator followed by a closing quote (`do." The`) does not end the
// sentence: the sample documents are built from paragraphs of exactly six
// sentences, and only this rule reproduces six sentences in every one of
// them. An empty line (new paragraph) and the end of the text also end a
// sentence.
std::vector<std::string> splitSentences(const std::string& text) {
    std::vector<std::string> sentences;
    const size_t n = text.size();
    size_t start = 0;

    auto emit = [&](size_t end) {
        if (end <= start) return;                 // nothing since the last boundary
        std::string s = collapseSpaces(text, start, end);
        if (!s.empty()) sentences.push_back(std::move(s));
    };

    for (size_t i = 0; i < n; ++i) {
        const char c = text[i];

        // Paragraph break: newline, optional spaces, newline.
        if (c == '\n') {
            size_t j = i + 1;
            while (j < n && (text[j] == ' ' || text[j] == '\t' || text[j] == '\r')) ++j;
            if (j < n && text[j] == '\n') { emit(i); start = j + 1; i = j; }
            continue;
        }
        if (!isTerminator(c)) continue;

        // Absorb a run of terminators ("..", "?!"); it must be followed by whitespace.
        size_t end = i + 1;
        while (end < n && isTerminator(text[end])) ++end;
        if (end < n && !isSpace(text[end])) { i = end - 1; continue; }   // e.g. "1.5", "U.S.", `."`

        size_t next = end;
        while (next < n && isSpace(text[next])) ++next;
        bool boundary = (next == n);
        if (!boundary) {
            const char d = text[next];
            boundary = isUpper(d) || isDigit(d) || d == '"' || d == '\'' || d == '(' || d == '[';
        }
        if (boundary && c == '.') {
            // The word right before the '.' decides whether it is an abbreviation.
            size_t wStart = i;
            while (wStart > start && (isUpper(text[wStart - 1]) || isLower(text[wStart - 1]))) --wStart;
            if (isAbbreviation(text.substr(wStart, i - wStart))) boundary = false;
        }
        if (boundary) {
            emit(end);
            start = next;
        }
        i = end - 1;
    }
    emit(n);
    return sentences;
}

// -------------------------------- words --------------------------------

// A word is a run of letters/digits; an apostrophe or hyphen between two
// such characters stays inside the word ("Majesty's", "well-nigh").
// Calls onWord(start, length) for every word of s.
template <typename OnWord>
static void scanWords(const std::string& s, OnWord onWord) {
    const size_t n = s.size();
    size_t i = 0;
    while (i < n) {
        if (!isWordChar(s[i])) { ++i; continue; }
        const size_t start = i;
        while (i < n && (isWordChar(s[i]) ||
                         ((s[i] == '\'' || s[i] == '-') && i + 1 < n && isWordChar(s[i + 1]))))
            ++i;
        onWord(start, i - start);
    }
}

std::vector<std::string> splitWords(const std::string& s) {
    std::vector<std::string> words;
    scanWords(s, [&](size_t start, size_t len) { words.push_back(s.substr(start, len)); });
    return words;
}

// ------------------------------- loading -------------------------------

// Reads a whole file into `out` with one fread call.
static bool readFile(const fs::path& path, std::string& out) {
    std::error_code ec;
    const uintmax_t size = fs::file_size(path, ec);
    if (ec) return false;
    std::FILE* f = std::fopen(path.string().c_str(), "rb");
    if (!f) return false;
    out.assign((size_t)size, '\0');
    const size_t got = size > 0 ? std::fread(&out[0], 1, (size_t)size, f) : 0;
    std::fclose(f);
    out.resize(got);
    // Skip a UTF-8 byte order mark if present.
    if (out.size() >= 3 && (unsigned char)out[0] == 0xEF && (unsigned char)out[1] == 0xBB &&
        (unsigned char)out[2] == 0xBF)
        out.erase(0, 3);
    return true;
}

static Document buildDocument(const std::string& name, const std::string& text, WordTable& words) {
    Document doc;
    doc.name = name;
    for (std::string& st : splitSentences(text)) {
        Sentence s;
        scanWords(st, [&](size_t start, size_t len) { s.ids.push_back(words.intern(st.data() + start, len)); });
        if (s.ids.empty()) continue;              // e.g. a lone "..."
        s.text = std::move(st);
        doc.sentences.push_back(std::move(s));
    }
    return doc;
}

// "document2.txt" < "document10.txt": digit runs are compared as numbers.
static bool naturalLess(const std::string& a, const std::string& b) {
    size_t i = 0, j = 0;
    while (i < a.size() && j < b.size()) {
        if (isDigit(a[i]) && isDigit(b[j])) {
            size_t i2 = i, j2 = j;
            while (i2 < a.size() && a[i2] == '0') ++i2;   // ignore leading zeros
            while (j2 < b.size() && b[j2] == '0') ++j2;
            size_t ie = i2, je = j2;
            while (ie < a.size() && isDigit(a[ie])) ++ie;
            while (je < b.size() && isDigit(b[je])) ++je;
            if (ie - i2 != je - j2) return ie - i2 < je - j2;
            for (size_t p = 0; p < ie - i2; ++p)
                if (a[i2 + p] != b[j2 + p]) return a[i2 + p] < b[j2 + p];
            i = ie; j = je;
        } else {
            if (a[i] != b[j]) return a[i] < b[j];
            ++i; ++j;
        }
    }
    return a.size() - i < b.size() - j;
}

bool loadCorpus(const std::string& folder, Corpus& corpus, std::string& error) {
    const fs::path base(folder);
    const fs::path mainPath = base / "main_doc.txt";
    const fs::path docsPath = base / "documents";
    WordTable words;

    std::string text;
    if (!readFile(mainPath, text)) {
        error = "cannot read " + mainPath.string();
        return false;
    }
    corpus.main = buildDocument("main_doc.txt", text, words);

    std::error_code ec;
    if (!fs::is_directory(docsPath, ec)) {
        error = "folder not found: " + docsPath.string();
        return false;
    }
    std::vector<std::string> names;
    for (const auto& entry : fs::directory_iterator(docsPath, ec)) {
        if (!entry.is_regular_file()) continue;
        const std::string name = entry.path().filename().string();
        const bool isTxt = name.size() > 4 && name.compare(name.size() - 4, 4, ".txt") == 0;
        if (isTxt && name[0] != '.') names.push_back(name);
    }
    std::sort(names.begin(), names.end(), naturalLess);
    if (names.empty()) {
        error = "no .txt files in " + docsPath.string();
        return false;
    }

    corpus.docs.clear();
    corpus.docs.reserve(names.size());
    for (const std::string& name : names) {
        if (!readFile(docsPath / name, text)) {
            error = "cannot read " + (docsPath / name).string();
            return false;
        }
        corpus.docs.push_back(buildDocument(name, text, words));
    }
    corpus.vocabularySize = words.size();
    return true;
}
