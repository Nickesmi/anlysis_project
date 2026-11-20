#!/usr/bin/env python3
"""
Test-set generator for the CMP3005 plagiarism detector (helper tool, not part
of the graded C++ program).

Two kinds of test sets are built from the sentences of a given sample set:

  accuracy  Uses the real documents of the sample set. Some documents are held
            out; main_doc.txt gets `--planted` sentences copied from the other
            documents (each with 0..`--max-edits` random word edits: insert,
            delete, replace, swap neighbours) plus `--unseen` sentences taken
            from the held-out documents, which therefore appear in no document.
            answer_key.txt lists how many sentences were planted per document.

  scale     Builds `--docs` documents (e.g. 200, like the hidden test set) by
            copying the sample documents with their sentence order shuffled,
            and copies main_doc.txt. Used for running-time measurements.

Examples:
  python3 tools/make_test_set.py accuracy --source ../1_STUDENTS_sample_set --out /tmp/acc1 --seed 1
  python3 tools/make_test_set.py scale --source ../1_STUDENTS_sample_set --out /tmp/scale200 --docs 200
"""
import argparse
import os
import random
import re
import shutil

# Same rule as the C++ program: split after . ! ? + whitespace, not after
# Mr. / St. / single capital initials, and not after a closing quote.
SENTENCE_END = re.compile(r'(?<!\bMr\.)(?<!\bSt\.)(?<!\b[A-Z]\.)(?<=[.!?])\s+(?=["\'(\[A-Z0-9])')


def read_sentences(path):
    with open(path, encoding="utf-8", errors="replace") as f:
        text = " ".join(f.read().split())
    return [s.strip() for s in SENTENCE_END.split(text) if s.strip()]


def natural_key(name):
    return [int(t) if t.isdigit() else t for t in re.split(r"(\d+)", name)]


def load_documents(source):
    folder = os.path.join(source, "documents")
    names = sorted((n for n in os.listdir(folder) if n.endswith(".txt")), key=natural_key)
    return [(n, read_sentences(os.path.join(folder, n))) for n in names]


def edit_sentence(sentence, edits, vocabulary, rng):
    """Applies `edits` random word edits; returns (new sentence, list of edits)."""
    words = sentence.split()
    done = []
    for _ in range(edits):
        op = rng.choice(["insert", "delete", "replace", "swap"])
        if op == "insert":
            w = rng.choice(vocabulary)
            p = rng.randrange(1, len(words))
            words.insert(p, w)
            done.append('inserted "%s"' % w)
        elif op == "delete" and len(words) > 4:
            p = rng.randrange(1, len(words) - 1)
            done.append('deleted "%s"' % words.pop(p))
        elif op == "replace":
            p = rng.randrange(1, len(words) - 1)
            w = rng.choice(vocabulary)
            done.append('replaced "%s" with "%s"' % (words[p], w))
            words[p] = w
        else:
            p = rng.randrange(1, len(words) - 2)
            words[p], words[p + 1] = words[p + 1], words[p]
            done.append('swapped "%s" and "%s"' % (words[p + 1], words[p]))
    return " ".join(words), done


def make_accuracy(args):
    rng = random.Random(args.seed)
    docs = load_documents(args.source)
    held_out = set(rng.sample(range(len(docs)), args.held_out))
    copied = [d for i, d in enumerate(docs) if i not in held_out]
    unseen_pool = [s for i, d in enumerate(docs) if i in held_out for s in d[1]
                   if len(s.split()) >= args.min_words]
    vocabulary = sorted({w.strip('.,;:!?"()').lower() for _, sents in copied for s in sents
                         for w in s.split() if w.strip('.,;:!?"()').isalpha()})

    # Plant sentences: a few documents get most of them, like the sample set.
    sources = rng.sample(range(len(copied)), min(args.sources, len(copied)))
    weights = [rng.randint(1, 8) for _ in sources]
    main_lines, key = [], {}
    used = set()
    for _ in range(args.planted):
        d = rng.choices(sources, weights)[0]
        name, sents = copied[d]
        choices = [s for s in sents if len(s.split()) >= args.min_words and (d, s) not in used]
        s = rng.choice(choices)
        used.add((d, s))
        edits = rng.randint(0, args.max_edits)
        new, done = edit_sentence(s, edits, vocabulary, rng) if edits else (s, [])
        main_lines.append(new)
        key.setdefault(name, []).append((len(s.split()), edits, "; ".join(done)))
    main_lines += rng.sample(unseen_pool, args.unseen)
    rng.shuffle(main_lines)

    out_docs = os.path.join(args.out, "documents")
    shutil.rmtree(args.out, ignore_errors=True)
    os.makedirs(out_docs)
    for i, (name, sents) in enumerate(copied, 1):
        with open(os.path.join(out_docs, "document%d.txt" % i), "w") as f:
            f.write(" ".join(sents) + "\n")
        key[("document%d.txt" % i, name)] = key.pop(name, [])
    with open(os.path.join(args.out, "main_doc.txt"), "w") as f:
        for i in range(0, len(main_lines), 5):
            f.write(" ".join(main_lines[i:i + 5]) + "\n\n")
    with open(os.path.join(args.out, "answer_key.txt"), "w") as f:
        f.write("main_doc.txt sentences: %d, planted: %d\n" % (len(main_lines), args.planted))
        for (new_name, _), planted in sorted(key.items(), key=lambda kv: -len(kv[1])):
            if planted:
                f.write("%s %d\n" % (new_name, len(planted)))
                for words, edits, done in planted:
                    f.write("    %d words, %d edits %s\n" % (words, edits, done))
    print("accuracy test set written to", args.out)


def make_scale(args):
    rng = random.Random(args.seed)
    docs = load_documents(args.source)
    out_docs = os.path.join(args.out, "documents")
    shutil.rmtree(args.out, ignore_errors=True)
    os.makedirs(out_docs)
    for i in range(args.docs):
        _, sents = docs[i % len(docs)]
        sents = list(sents)
        if i >= len(docs):
            rng.shuffle(sents)
        with open(os.path.join(out_docs, "document%d.txt" % (i + 1)), "w") as f:
            f.write(" ".join(sents) + "\n")
    shutil.copy(os.path.join(args.source, "main_doc.txt"), os.path.join(args.out, "main_doc.txt"))
    print("scale test set with %d documents written to %s" % (args.docs, args.out))


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("kind", choices=["accuracy", "scale"])
    p.add_argument("--source", required=True, help="sample set folder (main_doc.txt + documents/)")
    p.add_argument("--out", required=True, help="output folder (will be replaced)")
    p.add_argument("--seed", type=int, default=1)
    p.add_argument("--docs", type=int, default=200, help="scale: number of documents")
    p.add_argument("--held-out", type=int, default=4, help="accuracy: documents used for unseen sentences")
    p.add_argument("--sources", type=int, default=6, help="accuracy: documents that sentences are copied from")
    p.add_argument("--planted", type=int, default=40)
    p.add_argument("--unseen", type=int, default=20)
    p.add_argument("--max-edits", type=int, default=2)
    p.add_argument("--min-words", type=int, default=8)
    args = p.parse_args()
    make_accuracy(args) if args.kind == "accuracy" else make_scale(args)


if __name__ == "__main__":
    main()
