# CMP3005 Term Project – Plagiarism Detector (C++17)

Finds which sentences of `main_doc.txt` were copied (exactly or with small edits)
from the files in `documents/`, ranks the documents by similarity and prints up to
5 sentence pairs per document. Contains a brute-force and an efficient version.

## Compile

```bash
g++ -std=c++17 -O2 -o plagiarism src/*.cpp
```

(or `make`; `make test` builds and runs the self-test)

## Run

The program takes no user input. It reads `main_doc.txt` and `documents/*.txt`
from the **current folder**, so run it inside the test-set folder:

```bash
cd ../1_STUDENTS_sample_set
../plagiarism_detector/plagiarism
```

| Command | What it does |
|---|---|
| `plagiarism` | efficient version (default) |
| `plagiarism brute` | brute-force version |
| `plagiarism compare` | both versions, checks identical results, prints times and speedup |
| `plagiarism benchmark [r]` | times both on 1/8 … 8/8 of the documents (best of r runs), writes `benchmark.csv` |
| `--dir <folder>` | read the input from another folder |

## Matching rule

Sentences are compared as sequences of lower-case words. They match if the word-level
edit distance (insert / delete / replace a word, swap two neighbouring words) is at most
30% of the word count of the longer sentence (rounded down).
Similarity rate = matched sentences of main_doc / all sentences of main_doc.

## Layout

```
src/            the program (plagiarism.h + 7 modules)
tests/          selftest.cpp (make test)
tools/          make_test_set.py  – larger / harder test sets with answer keys
                build_report.py   – builds report/submission.html and .pdf
report/         report_body.html (report text), data/*.csv (benchmarks), submission.pdf
```

## Submission PDF and presentation guides

```bash
python3 tools/build_report.py --pdf report/2477758_2361056_2475798_2360187.pdf
```

```bash
python3 tools/build_guides.py
```

The report text is in `report/report_body.html`. The guides (one per member, in
speaking order) go to `presentation/`.
