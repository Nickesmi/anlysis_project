#!/usr/bin/env python3
"""
Builds one presentation guide per team member (helper tool, not part of the graded program).

  python3 tools/build_guides.py        -> presentation/<number>_<name>.html and .pdf

Each guide has: the member's slot and script, a walkthrough of the code they own (with line
numbers), numbers to remember, likely questions with answers, and a shared section about the
whole project and the hidden-test run (every member must be able to explain all of the code).
"""
import os
import shutil
import subprocess

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "presentation")

CSS = """
@page { size: A4; margin: 15mm 15mm 15mm 15mm; }
body { font-family: "Helvetica Neue", Arial, sans-serif; font-size: 10pt; line-height: 1.42; color: #111; }
h1 { font-size: 17pt; margin: 0 0 2px; } h2 { font-size: 12.5pt; margin: 16px 0 5px; color: #1d3c78; border-bottom: 1px solid #ccd; }
h3 { font-size: 10.5pt; margin: 10px 0 3px; }
.sub { color: #555; margin-bottom: 10px; }
table { border-collapse: collapse; margin: 6px 0; width: 100%; } td, th { border: 1px solid #bbb; padding: 3px 7px; vertical-align: top; }
th { background: #eef1f6; text-align: left; } td.me { background: #fff6d6; font-weight: bold; }
.script { background: #f7f8fb; border-left: 4px solid #1d3c78; padding: 6px 10px; margin: 6px 0; }
pre { font-family: Menlo, Consolas, monospace; font-size: 8.6pt; background: #f5f6f8; border: 1px solid #dde; padding: 5px 7px; white-space: pre-wrap; }
code { font-family: Menlo, Consolas, monospace; font-size: 9pt; }
.q { font-weight: bold; margin-top: 7px; } .a { margin: 1px 0 4px 14px; }
.shared { page-break-before: always; }
ul { margin: 3px 0 6px; padding-left: 20px; } li { margin: 1px 0; }
"""

# ---------------------------------------------------------------- talk plan
SLOTS = [
    ("0:00 to 2:00", "Pouya Shaterzadeh", "The problem, the input, sentence splitting, tokenizer and our hash table"),
    ("2:00 to 4:00", "Kian Samieenasab", "Matching rule, OSA edit distance, brute-force version"),
    ("4:00 to 6:30", "Nikan Esmaeil Tehrani", "Efficient version and complexity analysis"),
    ("6:30 to 8:00", "Mustafa Faisal Izhar", "Empirical analysis, accuracy results"),
    ("8:00 to 10:00", "Mustafa Faisal Izhar (drives), everyone", "Run on the hidden test set, then questions"),
]

# ---------------------------------------------------------------- members
MEMBERS = [
    {
        "name": "Pouya Shaterzadeh", "number": "2361056", "order": 1,
        "role": "Input and preprocessing: reading the files, sentence splitting, words, FNV-1a hash table.",
        "slides": [
            "Slide 1. Title, team members, what the program does (one sentence) and the similarity rate formula.",
            "Slide 2. Pipeline picture: files, sentences, word ids, matching, ranked output.",
            "Slide 3. Sentence splitting rule and the six-sentences-per-paragraph evidence (320 paragraphs).",
            "Slide 4. Word to id hash table: FNV-1a, open addressing, doubling at half full.",
        ],
        "script": """
<p>Hi, we are Nikan, Pouya, Kian and Mustafa. Our program gets a main document and a folder of documents, and for every
document it tells you what percentage of the main document's sentences were copied from it, exactly or with small edits.
The similarity rate is matched sentences of main_doc divided by all sentences of main_doc. The output is one block per
document, most similar first, with up to five sentence pairs.</p>
<p>I will talk about the first step, turning the text into something we can compare fast. First we split the text into
sentences. This sounds easy, but it decides the sentence count, so it changes every percentage. We noticed that every
paragraph in the sample documents has exactly six sentences, so they were built from the generator's own sentences. We
tried different rules, and only one gives six sentences in all 320 paragraphs: split at a full stop, question mark or
exclamation mark followed by a capital letter, but not after Mr., St. or a single capital letter like in U.S., and not when a
closing quote comes right after the full stop. A simple split on every ". " was wrong in eleven paragraphs.</p>
<p>Then we split each sentence into words, lower-case them, and give each word an integer id. For that we wrote our own hash
table: the FNV-1a hash, open addressing with linear probing, and the table doubles when it is half full, so a lookup is O(1) on
average. After this, a sentence is just a vector of ints, and comparing two words is one integer comparison. This step is
O(C) for C characters, and it is the same for both versions. Kian will now explain when two sentences count as a match.</p>
""",
        "code": [
            ("src/text_processing.cpp:20-27", "Our own character tests (isSpace, isUpper, isWordChar, isTerminator, toLower). We do not use any library search functions."),
            ("src/text_processing.cpp:36", "<code>class WordTable</code>: the hash table that maps a lower-cased word to an id."),
            ("src/text_processing.cpp:43", "<code>intern(p, n)</code>: computes FNV-1a over the lower-cased bytes (offset basis 1469598103934665603, prime 1099511628211), then linear probing. A slot holds a word id; we compare the stored 64-bit hash, the length and the characters. A new word goes in the first empty slot."),
            ("src/text_processing.cpp:75", "<code>grow()</code>: when more than half of the slots are used, the table doubles and every id is put back using its stored hash. Amortized O(1) per insert."),
            ("src/text_processing.cpp:97", "<code>isAbbreviation</code>: Mr, Mrs, Dr, St, ... and any single capital letter."),
            ("src/text_processing.cpp:108", "<code>collapseSpaces</code>: copies a sentence with runs of whitespace turned into one space (this is the text we print)."),
            ("src/text_processing.cpp:130", "<code>splitSentences</code>: one pass over the text. A run of . ! ? must be followed by whitespace, then a capital, digit, quote or bracket; the word before a '.' is checked for an abbreviation; an empty line also ends a sentence."),
            ("src/text_processing.cpp:187", "<code>scanWords</code>: a word is letters and digits; an inner ' or - stays inside (Majesty's, well-nigh). Bytes 128 and up count as letters (UTF-8)."),
            ("src/text_processing.cpp:209", "<code>readFile</code>: reads a whole file with one fread, skips a UTF-8 BOM."),
            ("src/text_processing.cpp:226", "<code>buildDocument</code>: sentences, then word ids; sentences without words are dropped."),
            ("src/text_processing.cpp:240", "<code>naturalLess</code>: document2.txt before document10.txt (digit runs compared as numbers)."),
            ("src/text_processing.cpp:262", "<code>loadCorpus</code>: reads main_doc.txt and every .txt in documents/, gives an error message if something is missing."),
        ],
        "numbers": [
            "320 paragraphs in the sample documents, all with exactly 6 generator sentences under our rule; a naive split gets 11 of them wrong.",
            "Sample set: main_doc 30 sentences, 20 documents, 2000 document sentences (100 per document).",
            "Reading and preprocessing: about 5 to 12 ms for the sample set, about 48 ms for 200 documents (was about 94 ms before we wrote our own hash table and stopped storing every word as a string).",
            "Hash table starts with 65 536 slots, load factor at most 1/2.",
        ],
        "qa": [
            ("Why didn't you use regex or string find?", "The assignment does not allow built-in text search for the core task. We scan the text character by character, which is also O(C), so we do not lose anything."),
            ("How did you decide the sentence splitting rule?", "From the data. Every paragraph of the sample documents has exactly six sentences, so the generator built the documents from its own sentence list. We tried several rules and only ours gives 6 in all 320 paragraphs. If our split differs from the generator's, a copied sentence can be cut in two and the sentence count changes, so the percentages would be off."),
            ("What happens with \"U.S. Army\"?", "At the first '.' the next character is 'S', not whitespace, so it is not a boundary. At the second '.' the word before it is the single capital 'S', which we treat as an abbreviation, so it does not split either."),
            ("Why FNV-1a?", "It is short, fast and spreads short strings well: for each byte, XOR it into the hash and multiply by the FNV prime. We hash the lower-cased bytes directly, so we never create a lower-case copy of the word."),
            ("How do you handle collisions?", "Open addressing with linear probing. On a collision we move to the next slot. To confirm a hit we compare the full 64-bit hash first, then the length and the characters, so two different words never get the same id."),
            ("What is the complexity of a lookup?", "Expected O(L) for a word of length L, because the table is never more than half full and probe sequences stay short. Doubling costs O(V) but happens rarely, so it is amortized O(1) per insert. The theoretical worst case, every word in one cluster, is O(V) per lookup."),
            ("Why turn words into integers at all?", "After this step, every comparison in the edit distance is one integer comparison instead of a string comparison, and the index can use the id directly as an array position."),
            ("Why do you lower-case words and ignore punctuation?", "A copied sentence with a changed capital letter or comma is still a copy. The edit rule only counts word edits."),
            ("What is (h ^ (h >> 29)) in intern?", "The slot is chosen with a bit mask, which keeps only the low bits. Mixing in some high bits first spreads the words more evenly over the table."),
        ],
    },
    {
        "name": "Kian Samieenasab", "number": "2475798", "order": 2,
        "role": "Matching rule, OSA edit distance, brute-force version, edit descriptions, accuracy tests.",
        "slides": [
            "Slide 5. Matching rule: OSA distance on words, the four edits, the 30% threshold with examples (3, 10, 30 words).",
            "Slide 6. The DP recurrence with the swap case, and an example table for a small sentence.",
            "Slide 7. Brute-force pseudocode and O(n·S·w²).",
        ],
        "script": """
<p>Now that every sentence is a list of word ids, we need a rule for when two sentences match. The task says a copy can have
small edits: a word added, removed, replaced, or two neighbouring words swapped. So we use the optimal string alignment
distance on words, OSA for short. It is the smallest number of those four edits that turns one sentence into the other.
We chose it over normal Levenshtein because Levenshtein counts a swap as two edits, and over word-set measures like Jaccard
because those do not see a swap at all.</p>
<p>Two sentences match if the distance is at most 30% of the longer sentence, rounded down. So a sentence of three words or
less has to be identical, a 10-word sentence can have 3 edits, and a 23-word sentence can have 6. We started with 25%, but in
our generated tests 30% found three more heavily edited short sentences and still gave zero false matches. In the sample
documents no two different sentences are even within 40% of each other.</p>
<p>The distance is a dynamic programming table. Cell i, j is the distance between the first i words of one sentence and the
first j words of the other. It takes the minimum of delete, insert, keep or replace, and the swap case, which looks two rows
and two columns back. We only keep three rows in memory. The brute force does this for every main sentence, every document
and every sentence in it, so it is O(n times S times w squared). On 200 documents that is 600 000 full tables. Nikan will
show how we avoid almost all of them.</p>
""",
        "code": [
            ("src/similarity.cpp:27", "<code>EDIT_PERCENT = 30</code>."),
            ("src/similarity.cpp:29", "<code>allowedEdits(la, lb)</code> = max(la, lb) * 30 / 100 with integer division, which is the floor."),
            ("src/similarity.cpp:37", "<code>maxAllowedEdits(la)</code>: the largest k any partner sentence could get. The partner can be longer by at most k words, and a longer partner gets a bigger k, so we walk lb upwards until the length gap is bigger than k. Example: 20 words gives 8."),
            ("src/similarity.cpp:56", "<code>osaDistance</code>: the full DP with three rolling rows (prev2, prev, cur). The swap case uses prev2[j-2] + 1 when a[i-1] == b[j-2] and a[i-2] == b[j-1]."),
            ("src/similarity.cpp:82", "<code>boundedOsaDistance</code>: the banded version used by the efficient algorithm (Nikan explains it). It must give the same answer as osaDistance whenever the distance is at most k; the self-test checks that on 200 000 random pairs."),
            ("src/similarity.cpp:125", "<code>describeEdits</code>: builds the full table, then walks back from the bottom-right corner: same word, swap, replace, delete, insert. It prints the edits in sentence order, e.g. replaced \"should\" with \"must\"."),
            ("src/similarity.cpp:181", "<code>MatchTable::offer</code>: keeps the best pair for each (document, main sentence): smaller distance wins, ties go to the smaller document sentence index. This is why brute force and efficient pick exactly the same pair."),
            ("src/brute_force.cpp:16", "<code>runBruteForce</code>: three nested loops, a full OSA for every pair, no shortcuts. This is the version we compare against."),
            ("tools/make_test_set.py", "The accuracy generator: copies 40 sentences into a new main_doc with 0 to 3 random edits, adds 20 sentences that appear nowhere, and writes an answer key."),
        ],
        "numbers": [
            "Allowed edits: 1 to 3 words give 0, 4 to 6 words give 1, 10 words give 3, 23 words give 6, 30 words give 9.",
            "Sample: 20 of 20 copied sentences found, 13 exact, 7 edited; edits were at most 2 per sentence.",
            "Generated tests: 800/800 found for sentences of at least 10 words, 798/800 for at least 6 words, 0 false matches.",
            "Brute force on 200 documents and a 30-sentence main_doc: 600 000 full DPs, 741 ms.",
        ],
        "qa": [
            ("Why OSA and not Levenshtein?", "The task lists a swap of two neighbouring words as one small edit. Levenshtein would need a delete and an insert (or two replacements) for it, so a sentence with two swaps would look like four edits. OSA counts each swap as one."),
            ("Why compare words and not characters?", "The edits in the task are word edits. Word sequences are also about 6 times shorter than character sequences, so the table is about 36 times smaller."),
            ("Why 30%?", "We tested 25% and 30% on generated sets. 30% found three more sentences with 3 edits in short sentences and still had zero false matches. We also checked all pairs of different sentences in the sample documents: none are within 40% of each other, so 30% leaves a safe margin."),
            ("Why must very short sentences be identical?", "floor(0.3 times 3) is 0. For a 3-word sentence one edit is a third of the sentence, and short sentences like \"It is so.\" would match many unrelated sentences."),
            ("What is the time and memory of one OSA?", "Time O(|a| times |b|), memory O(|b|) because we keep three rows: the current one, the previous one, and the one before it for swaps."),
            ("Is OSA a metric?", "Not exactly, it can break the triangle inequality, unlike full Damerau-Levenshtein. We never need the triangle inequality, we only compare one pair at a time with a threshold, so it does not matter."),
            ("What if a main sentence matches two sentences in the same document?", "It still counts once for that document, because the rate counts main_doc sentences. We keep the closest pair; if two are equally close we keep the earlier one."),
            ("Show the brute-force complexity.", "n main sentences times S document sentences pairs, each a w by w table: O(n times S times w squared). With 200 documents that is 30 times 20 000 = 600 000 tables."),
            ("Give an example of a sentence you miss.", "\"In invaded canals solicitude intense pervaded the nation.\" against \"In that crisis intense solicitude pervaded the nation.\": 3 edits in 8 words is 37.5%, more than 30%. Almost half the sentence changed, so we would not call it a small edit."),
        ],
    },
    {
        "name": "Nikan Esmaeil Tehrani", "number": "2477758", "order": 3,
        "role": "Efficient version (index, pigeonhole filter, cheap filters, banded DP) and the complexity analysis.",
        "slides": [
            "Slide 8. Idea: index main_doc, stream the documents; the pigeonhole argument in one picture.",
            "Slide 9. Filters in order: pigeonhole, length, bag of words, banded DP (with the counts 20 000, 6 670, 47 440, 200).",
            "Slide 10. Complexity table: brute O(n·S·w²) vs efficient; worst case and practical case.",
        ],
        "script": """
<p>The brute force computes 600 000 tables on 200 documents, but only 200 of those pairs are real copies. Our efficient
version tries to rule out the other pairs without computing the table, and it never rules out a real match, so its output is
exactly the same as the brute force. The compare mode checks that every time.</p>
<p>First we build an inverted index of main_doc only: for every word, the list of main sentences that contain it. main_doc is
the small side, so the index is tiny, and then we read every document sentence just once. Our first version indexed all the
documents and it was slower.</p>
<p>The key idea is a pigeonhole argument. If a document sentence b matches a main sentence a with at most k edits, every edit
removes at most one word of b from a. So if I take any k plus 1 different words of b, at least one of them must be in a. That
gives two shortcuts. If k plus 1 words of b do not appear anywhere in main_doc, b cannot match anything and we skip it. Otherwise
we only look at main sentences in the lists of the k plus 1 rarest words of b, because rare words have short lists.</p>
<p>Each candidate then goes through two cheap filters: the length filter, because each edit changes the length by at most one,
and a bag-of-words bound, the distance is at least the longer length minus the number of common words, which we count by merging
two sorted lists. Only what survives gets the banded DP, which only fills the cells with |i minus j| at most k and stops when a
whole row is above k.</p>
<p>On 200 documents: 6 670 of 20 000 sentences are skipped right away, 47 440 candidates are checked cheaply, and only 200 DPs are
computed, exactly the 200 real matches. In the worst case, if every sentence looked like every other sentence, we would still be
O(n times S times w squared) like the brute force, because then every pair really has to be checked. On real text the cost is
about linear in the input. Mustafa will show the measured times.</p>
""",
        "code": [
            ("src/efficient.cpp:37", "<code>class MainDocIndex</code>. The constructor builds <code>postings_[word]</code> (each main sentence at most once per word, using the <code>wordSeen_</code> stamp), <code>byLength_</code> and the sorted ids of each main sentence."),
            ("src/efficient.cpp:60", "<code>search(doc, s, b, stamp, table)</code>: handles one document sentence b. k = maxAllowedEdits(|b|)."),
            ("src/efficient.cpp:69-71", "Distinct words of b using a stamp (no clearing of arrays needed). Words in main_doc go to <code>present_</code>; a missing word increases <code>missing</code>, and as soon as missing > k we return: pigeonhole says b matches nothing."),
            ("src/efficient.cpp:80", "<code>partial_sort</code>: picks the k+1-missing rarest present words (shortest posting lists) and visits the main sentences in their lists."),
            ("src/efficient.cpp:85", "Fallback: if b has at most k different words the argument does not work, so every main sentence of a close length is a candidate."),
            ("src/efficient.cpp:93", "<code>verify</code>: each main sentence once per b (<code>checkedBy_</code> stamp); line 99 length filter, line 100 bag-of-words filter, line 101 banded DP, then <code>table.offer</code>."),
            ("src/efficient.cpp:108", "<code>commonWords</code>: merges two sorted id lists and counts equal pairs, O(|x| + |y|)."),
            ("src/efficient.cpp:130", "<code>runEfficient</code>: builds the index, then loops over every document and sentence once."),
            ("src/similarity.cpp:82", "<code>boundedOsaDistance</code>: only cells with |i-j| <= k; cells just outside the band are set to k+1 (TOO_FAR); returns k+1 early if a whole row is above k."),
        ],
        "numbers": [
            "200 documents, main_doc 30 sentences: 20 000 document sentences, 6 670 skipped by pigeonhole, 47 440 candidates, 29 580 removed by length, 17 660 by bag of words, 200 banded DPs, 200 matches.",
            "Brute force: 600 000 full DPs. Candidates per document sentence c is about 2.4, much smaller than n = 30.",
            "Matching time on 200 documents: 741 ms vs 13.9 ms (53x) with n = 30; 7 849 ms vs 81.8 ms (96x) with n = 230.",
            "k for the probes: maxAllowedEdits(20) = 8 (about 0.43 of the length).",
        ],
        "qa": [
            ("Prove that you never lose a match.", "Let b match a with d <= k edits. A word of b is missing from a only if all its copies were deleted or replaced, and each of those edits handles one copy; a swap or insert removes nothing. So at most k different words of b are missing from a. Any k+1 different words of b therefore include at least one word that is in a, so a is in one of the posting lists we visit. The length filter and the bag-of-words bound are lower bounds on the distance, and the banded DP is exact when the distance is <= k, so none of them can reject a real match."),
            ("Why the rarest words?", "Any k+1 words would be correct. The rarest words have the shortest posting lists, so we get the fewest candidates. Words that are not in main_doc at all have empty lists and count first."),
            ("Why is k for b bigger than 30% of |b|?", "The partner a can be longer than b. If a has |b|+k words it gets k = 0.3(|b|+k), which solves to about 0.43|b|. We need the largest k any partner could get, otherwise we could skip a real match. For |b| = 20 this is 8."),
            ("Why index main_doc and not the documents?", "main_doc is small, so its index is tiny and fits in cache, and each document sentence is read only once. We tried indexing all documents first; that index has all S sentences and was slower to build."),
            ("Why is the banded DP correct?", "Every step off the diagonal costs at least one edit, so an alignment with distance <= k never goes more than k cells away from the diagonal. Also, the minimum of a row never gets smaller in the next rows, so once a whole row is above k the final answer is above k too. The self-test compares it with the full DP on 200 000 random pairs."),
            ("Why the bag-of-words bound?", "To create a word that is not shared you need an insert or a replace, and each edit makes at most one shared word stop being shared, so the distance is at least max(|a|,|b|) minus the common words. Counting common words is an O(w) merge, much cheaper than an O(w·k) table. In our run it removed every non-match before the DP."),
            ("What are the stamp arrays?", "Instead of clearing a visited array for every sentence, we write the current sentence number into it. A cell counts as visited only if it holds the current number. This makes the distinct-word check O(1) and avoids O(V) clearing."),
            ("What is the worst-case complexity of the efficient version?", "O(C + n·w log w + S·(w log w + n·w) + D·w²), where D is the number of pairs that reach the DP. If every sentence is almost the same as every other, D = n·S and it is O(n·S·w²) like the brute force; no exact method can avoid that because every pair really must be checked. In practice D is just the real matches."),
            ("Why not Rabin-Karp, shingles or LSH?", "Hashing whole sentences only finds exact copies. Word bigram shingles need 3k+1 probes because one edit breaks up to 3 bigrams, and lists for common bigrams like \"of the\" are long. MinHash/LSH is probabilistic and can miss copies. Suffix arrays find exact substrings only."),
        ],
    },
    {
        "name": "Mustafa Faisal Izhar", "number": "2360187", "order": 4,
        "role": "Output and ranking, benchmark mode, empirical analysis, self-test, report; drives the hidden-test run.",
        "slides": [
            "Slide 11. Benchmark tables and the two plots (both lines linear, efficient 47 to 100 times faster).",
            "Slide 12. Results: sample set exactly like expected_output.txt; generated tests 800/800, 798/800, 0 false matches; the two misses.",
            "Slide 13. Live run on the hidden test set (terminal).",
        ],
        "script": """
<p>We measured both versions with our benchmark mode. It runs both on the first eighth, quarter and so on of the documents,
takes the best of five runs, and checks that the results are identical. The sample set has only 20 documents, so we also built a
200-document set from the sample documents with their sentences shuffled, once with the 30-sentence main_doc and once with a
230-sentence main_doc.</p>
<p>Both lines are straight, which matches the analysis: the number of document sentences grows linearly with the number of
documents. On 200 documents the brute force needs 741 milliseconds and ours 14, so 53 times faster. With the longer main_doc it
is 7.8 seconds against 82 milliseconds, 96 times faster, because the brute force grows with n times S while our version only
pays a cheap merge per candidate. For the whole program, including reading the files, it is 0.14 seconds against almost 8.</p>
<p>For accuracy, on the sample set we find all 20 copied sentences with the same ranking and the same percentages as the
expected output, and no false matches. With our test generator, 800 out of 800 copied sentences with up to 3 random edits were
found, and 798 out of 800 when we also allowed 6-word sentences. The two misses are short sentences where almost half the words
changed, more than our 30% rule allows.</p>
<p>The output is one block per document, sorted by the number of matched sentences, with ties in file order, and inside a
block the five most similar pairs. Now I will run it on the hidden test set.</p>
""",
        "code": [
            ("src/output.cpp:21", "<code>percent(part, whole)</code>: one decimal with integer rounding, (part*1000 + whole/2) / whole tenths, so 8/30 prints 26.7 with no floating point surprises."),
            ("src/output.cpp:29", "<code>moreSimilar</code>: compares d1/L1 with d2/L2 by cross-multiplying (d1*L2 < d2*L1), ties by main sentence order."),
            ("src/output.cpp:35", "<code>printResults</code>: collects the matched pairs per document; line 49 <code>stable_sort</code> ranks documents by matched count and keeps file order on ties; line 64 sorts the pairs; prints at most 5 and then \"... and N more pairs\"; edited pairs get describeEdits; last line counts main sentences copied from at least one document."),
            ("src/benchmark.cpp:26", "<code>timeIt</code>: runs an algorithm several times with steady_clock and keeps the fastest; a run over 3 s is not repeated."),
            ("src/benchmark.cpp:41", "<code>runBenchmark</code>: sizes 1/8 ... 8/8 of the documents, copies the first m documents (not timed), times both versions, checks <code>brute == fast</code>, prints the table and writes benchmark.csv."),
            ("src/main.cpp:47", "<code>main</code>: modes efficient (default), brute, compare, benchmark; --dir; loads the corpus, runs, prints, prints the times. compare exits with code 2 if the two results differ."),
            ("tests/selftest.cpp", "13 checks: splitting, words, each edit type, the 30% rule, banded vs full DP on 200 000 random pairs, edit descriptions. Run with make test."),
            ("tools/build_report.py", "Builds the submission PDF: pastes the code as text, makes the tables and the SVG plot from report/data/*.csv."),
        ],
        "numbers": [
            "Sample (20 docs, n = 30): brute 72.5 ms, efficient 1.35 ms (54x).",
            "200 docs, n = 30: brute 741.4 ms, efficient 13.9 ms (53x). 200 docs, n = 230: 7 848.7 ms vs 81.8 ms (96x).",
            "Whole program, 200 docs and n = 230: 0.14 s vs 7.96 s. Reading files: about 48 ms for 200 docs.",
            "Machine: Apple M2 Pro, 16 GB, clang 17, -O2, best of 5 runs.",
            "Sample result: document18 26.7% (8/30), document14 16.7% (5/30), document20 13.3% (4/30), document3 6.7% (2/30), document4 3.3% (1/30).",
        ],
        "qa": [
            ("What exactly did you time?", "Only the matching step, and for the efficient version that includes building its index. Reading the files is the same code for both, so we report it separately (about 48 ms for 200 documents). Each number is the best of 5 runs with std::chrono::steady_clock."),
            ("Why is the brute force line straight?", "Its cost is n times S times w squared. n and w do not change in the experiment and S grows linearly with the number of documents."),
            ("Why is the speedup bigger with the longer main_doc?", "The brute force does n times S full tables, so it grows 7.7 times when n goes from 30 to 230. In the efficient version more of the main_doc words are known, so more candidates appear, but each candidate costs only an O(w) merge, not an O(w²) table."),
            ("The 200 documents are copies. Is that fair?", "The sample only has 20 documents, so we repeated them with shuffled sentence order to get realistic sizes. Both versions get exactly the same input, so the comparison is fair. Duplicates only make the efficient version do a bit more work, because copied sentences match in more documents."),
            ("How do you rank documents with the same similarity?", "We use a stable sort on the matched count, so equal documents keep their file order, document2 before document10."),
            ("How do you choose the 5 pairs you print?", "By relative distance, distance divided by the longer sentence length, smallest first. Exact copies come first. We compare fractions by cross-multiplying, so no floating point is needed."),
            ("How do you know the two versions agree?", "compare and benchmark check the full result tables for equality: every document, every main sentence, the chosen pair and its distance. compare exits with an error if they differ. It never happened in any test."),
            ("What do you do if the hidden test set gives a different result?", "We report what we get. The percentages depend on the sentence count, so if a sentence is split differently from the generator the numbers move a little; we explain that in the report."),
        ],
    },
]

# ---------------------------------------------------------------- shared part
SHARED = """
<section class="shared">
<h2>Shared part: the whole project on one page (everyone must know this)</h2>
<h3>Pipeline</h3>
<ol>
<li><b>Read</b> main_doc.txt and documents/*.txt from the current folder (or --dir). Natural file order.</li>
<li><b>Split</b> into sentences (generator rule: no split after Mr./St./single capitals, not after a closing quote; empty line ends a sentence).</li>
<li><b>Words to ids</b>: lower-case, letters and digits, inner ' and - kept; our FNV-1a hash table with linear probing gives each word an int id.</li>
<li><b>Match</b>: OSA distance on words (insert, delete, replace, swap neighbours), match if distance &lt;= floor(0.3 x longer length).
   Brute force: every pair, full DP. Efficient: main_doc index, pigeonhole skip, k+1 rarest words, length filter, bag-of-words filter, banded DP.</li>
<li><b>Output</b>: rate = matched main sentences / all main sentences; documents sorted by rate, ties in file order; up to 5 most similar pairs, edits listed.</li>
</ol>
<h3>Complexity in one line each</h3>
<ul>
<li>n main sentences, m documents, s sentences per document, S = m·s, w words per sentence, C characters.</li>
<li>Preprocessing: O(C) expected (both versions).</li>
<li>Brute force: O(n·S·w²).</li>
<li>Efficient: O(C + n·w log w + S·(w log w + n·w) + D·w²); worst case O(n·S·w²) if every pair survives; in practice D = real matches, so about linear.</li>
<li>Memory: O(C + V + n·w + m·n).</li>
</ul>
<h3>Numbers everyone should remember</h3>
<ul>
<li>Sample: 20/20 found (13 exact, 7 edited), same ranking and rates as expected_output.txt, 0 false matches.</li>
<li>200 documents: 741 ms vs 14 ms (53x) with n = 30; 7.8 s vs 82 ms (96x) with n = 230; whole program 7.96 s vs 0.14 s.</li>
<li>Filters on 200 documents: 20 000 sentences, 6 670 skipped at once, 47 440 candidates, 200 DPs = 200 matches (brute: 600 000 DPs).</li>
<li>Generated tests: 800/800 (at least 10 words), 798/800 (at least 6 words), 0 false matches.</li>
</ul>
<h3>Talk plan (10 minutes)</h3>
{slots}
<h3>Questions anyone can get</h3>
<div class="q">Which files does it read and how do you run it?</div>
<div class="a">main_doc.txt and documents/*.txt in the folder it is started from. Compile with <code>g++ -std=c++17 -O2 -o plagiarism src/*.cpp</code>, run with <code>./plagiarism</code> (efficient), <code>brute</code>, <code>compare</code>, <code>benchmark</code>.</div>
<div class="q">Did you use any built-in search?</div>
<div class="a">No find, indexOf or regex in the core. Splitting, tokenizing, hashing and matching are our own code. We use standard containers (vector, sort), which the assignment allows.</div>
<div class="q">Are the brute force and the efficient version really the same?</div>
<div class="a">Same matching rule, and the efficient filters can only reject pairs that cannot match, so the result tables are identical. compare and benchmark check it every run.</div>
<div class="q">What would you improve?</div>
<div class="a">Reading the files is now the slowest part (about 48 ms for 200 documents); it could be done with memory-mapped files or in parallel. We could also make the threshold depend on the sentence length more carefully for very short sentences.</div>
<div class="q">Did you use AI?</div>
<div class="a">Yes, Claude, as written in our AI Use Declaration. We tested everything ourselves and each of us can explain all of the code.</div>

<h2>Hidden test set: checklist (Mustafa drives, everyone should know it)</h2>
<pre>Before class (once):
  cd ~/Desktop/betuljende/plagiarism_detector
  make                       # or: g++ -std=c++17 -O2 -o plagiarism src/*.cpp
  make test                  # should print ALL TESTS PASSED
  cd ../1_STUDENTS_sample_set && ../plagiarism_detector/plagiarism compare | tail -4

In class, when you get the hidden folder (it contains main_doc.txt and documents/):
  cd "&lt;hidden folder&gt;"
  ~/Desktop/betuljende/plagiarism_detector/plagiarism | head -60      # efficient result, top of the ranking
  ~/Desktop/betuljende/plagiarism_detector/plagiarism | tail -4       # times
  ~/Desktop/betuljende/plagiarism_detector/plagiarism compare | tail -5   # both versions, same result, speedup

If it says "Error: cannot read ./main_doc.txt": you are in the wrong folder. Either cd into the folder
that contains main_doc.txt, or add  --dir "&lt;hidden folder&gt;"  to the command.</pre>
<ul>
<li>Do not change any code in class; the assignment says it must run without changes.</li>
<li>Keep the laptop charged, the terminal font large, and the sample-set run already in the scroll-back as a backup.</li>
</ul>
</section>
"""


def slots_table(me):
    rows = ["<table><tr><th>Time</th><th>Who</th><th>Topic</th></tr>"]
    for t, who, topic in SLOTS:
        cls = ' class="me"' if me in who else ""
        rows.append("<tr><td%s>%s</td><td%s>%s</td><td%s>%s</td></tr>" % (cls, t, cls, who, cls, topic))
    rows.append("</table>")
    return "".join(rows)


def guide_html(m):
    my_slots = [s for s in SLOTS if m["name"] in s[1]]
    parts = ["<h1>Presentation guide: %s (%s)</h1>" % (m["name"], m["number"]),
             '<div class="sub">CMP3005 Term Project, Efficient Plagiarism Detector. Speaker %d of 4. Your part: %s</div>'
             % (m["order"], m["role"]),
             "<h2>1. Your slot</h2>", slots_table(m["name"]),
             "<p>You speak at: %s. Keep to about 300 words; it is fine to read from the slide notes the first time, "
             "but practise until you only need the slide.</p>" % "; ".join(s[0] for s in my_slots),
             "<h2>2. Your slides</h2><ul>%s</ul>" % "".join("<li>%s</li>" % s for s in m["slides"]),
             "<h2>3. What to say</h2>", '<div class="script">%s</div>' % m["script"],
             "<h2>4. Your code (open these lines before the presentation)</h2><table><tr><th>Where</th><th>What it does</th></tr>%s</table>"
             % "".join("<tr><td><code>%s</code></td><td>%s</td></tr>" % c for c in m["code"]),
             "<h2>5. Numbers to remember</h2><ul>%s</ul>" % "".join("<li>%s</li>" % n for n in m["numbers"]),
             "<h2>6. Questions you will probably get</h2>%s"
             % "".join('<div class="q">%s</div><div class="a">%s</div>' % qa for qa in m["qa"]),
             SHARED.replace("{slots}", slots_table(m["name"]))]
    return ('<!doctype html><html><head><meta charset="utf-8"><title>Guide %s</title><style>%s</style></head><body>%s</body></html>'
            % (m["name"], CSS, "\n".join(parts)))


def main():
    os.makedirs(OUT, exist_ok=True)
    chrome = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
    if not os.path.exists(chrome):
        chrome = shutil.which("google-chrome") or shutil.which("chromium")
    for m in MEMBERS:
        base = "%d_%s_%s" % (m["order"], m["number"], m["name"].replace(" ", "_"))
        html_path = os.path.join(OUT, base + ".html")
        with open(html_path, "w", encoding="utf-8") as f:
            f.write(guide_html(m))
        if chrome:
            subprocess.run([chrome, "--headless", "--disable-gpu", "--no-pdf-header-footer",
                            "--print-to-pdf=" + os.path.join(OUT, base + ".pdf"), "file://" + html_path],
                           check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        print("wrote", os.path.join(OUT, base + (".pdf" if chrome else ".html")))


if __name__ == "__main__":
    main()
