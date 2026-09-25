"""
mutation_check.py - a gate check (kit v0.13): every mutation of every corpus pack (mutations.py) makes the reference
return a World or raise a named refusal, never another exception. A crash is not a verdict (QUESTIONS.md Q3, Q17): a
reader that raises where the page refuses tells a builder nothing about the name.
  python3 laws/mutation_check.py
"""
import os, sys, time
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import mutations as MU, surface_check as SC

OK = os.path.join(HERE, "packs", "ok")

def verdict(text):
    "a World, a refusal's name, or the exception that is neither"
    try: SC.check(text, {}, OK); return "ACCEPTED", None
    except SC.Refused as e: return e.name, None
    except Exception as e: return None, f"{type(e).__name__}: {str(e)[:100]}"

def main():
    t0 = time.time(); n, crashes = 0, []
    for name, text in MU.corpus():
        for label, v in MU.all_variants(name, text):
            n += 1; got, crash = verdict(v)
            if crash: crashes.append(f"{name} :: {label}: raised {crash}")
    kinds = {}
    for c in crashes: kinds.setdefault(c.split(": raised ")[1].split(":")[0], []).append(c)
    for k, cs in sorted(kinds.items()):
        print(f"FAIL {len(cs)} variants raise {k}; the first: {cs[0][:200]}")
    print(f"mutation: {n} variants of the corpus in {time.time() - t0:.0f}s; "
          + ("MUTATION PASSES" if not crashes else f"MUTATION FAILS ({len(crashes)} raise instead of refusing)"))
    return not crashes

if __name__ == "__main__":
    sys.exit(0 if main() else 1)
