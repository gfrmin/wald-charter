"""
encoding_check.py - SURFACE v0.2 R13, the canonical encoding, checked by a second encoder written from the page's byte
rules alone (no JSON library), against the reference `counts_check.counts_sha`, on the page's own vectors and on
fuzzed names from every character class the rules treat differently. A gate check: it runs before any attack.
"""
import hashlib, random, re, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from collections import Counter
import counts_check as C

def escape_table(page):
    """V2.13's escapes, read from the page itself: rows `| U+XXXX | U+YYYY | written as |`, the first row whose range holds
    the character deciding. The encoder below is built from these rows and nothing else, so a sentence of the page cannot
    say one thing while this checks another (attack session 4 on SURFACE v0.2, 4.1)."""
    txt = open(page, encoding="utf-8").read(); rows = []
    for lo, hi, how in re.findall(r"^\| U\+([0-9A-F]{4,6}) \| U\+([0-9A-F]{4,6}) \| (.+?) \|$", txt, re.M):
        rows.append((int(lo, 16), int(hi, 16), how.strip().strip("`")))
    return rows

ROWS = []
def esc(ch):
    o = ord(ch)
    for lo, hi, how in ROWS:
        if lo <= o <= hi:
            if how == "itself": return ch
            if how == "\\uXXXX": return "\\u%04x" % o
            if how == "\\uXXXX\\uXXXX":
                v = o - 0x10000; return "\\u%04x\\u%04x" % (0xD800 + (v >> 10), 0xDC00 + (v & 0x3FF))
            return how
    raise ValueError(f"V2.13's table has no row for U+{o:04X}")
def s(x): return "null" if x is None else '"' + "".join(esc(c) for c in x) + '"'
def arr(xs): return "[" + ",".join(xs) + "]"
def rec(obs, t, oa, n=None):
    parts = [arr(arr([s(a), s(o)]) for a, o in obs), s(t), s(oa)] + ([str(n)] if n is not None else [])
    return arr(parts)
def canonical(counts, falsifiers=()):
    rows = sorted(rec(o, t, a, n) for (o, t, a), n in counts.items())
    fal = sorted(rec(o, t, a) for (o, t, a) in falsifiers)
    return arr([arr(rows), arr(fal)])

def page_vectors(page):
    txt = open(page, encoding="utf-8").read()
    return re.findall(r"\| `(\[\[.*?\]\])` \| `([0-9a-f]{64})` \|", txt)

def main(page, trials=3000, seed=11):
    fails = []; ROWS[:] = escape_table(page)
    if len(ROWS) < 5: fails.append("V2.13's escape table is missing or unreadable")
    for b, d in page_vectors(page):
        if hashlib.sha256(b.encode("ascii")).hexdigest() != d: fails.append(f"page vector {b[:40]} does not hash to its digest")
    if len(page_vectors(page)) < 5: fails.append("the page shows fewer than five vectors")
    rng = random.Random(seed)
    alphabet = list("ab/1 \"\\\x7f") + ["\b", "\f", "\n", "\r", "\t", "\x01", "\x1f", "é", "ß", "中", "\u2028", "😀", "\U0010ffff"]
    name = lambda: "".join(rng.choice(alphabet) for _ in range(rng.randint(1, 4)))
    for _ in range(trials):
        counts = Counter(); fal = []
        for _ in range(rng.randint(0, 3)):
            obs = tuple((name(), name()) for _ in range(rng.randint(0, 2)))
            counts[(obs, name(), rng.choice([None, name()]))] += rng.randint(1, 10**rng.randint(0, 22))
        for _ in range(rng.randint(0, 2)): fal.append((tuple((name(), name()) for _ in range(rng.randint(1, 2))), rng.choice([None, name()]), rng.choice([None, name()])))
        mine = hashlib.sha256(canonical(counts, fal).encode("utf-8")).hexdigest()
        if mine != C.counts_sha(counts, fal): fails.append(f"encoders disagree on {dict(counts)} {fal}"); break
    for f in fails: print("FAIL", f)
    print(f"encoding: {len(page_vectors(page))} page vectors, {trials} fuzzed record sets; " + ("ENCODING PASSES" if not fails else "ENCODING FAILS"))
    return not fails

if __name__ == "__main__":
    sys.exit(0 if main(sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "SURFACE-v0.2.md")) else 1)
