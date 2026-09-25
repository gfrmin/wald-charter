"""
page_check.py - traceability for a page written as rules stated once (SURFACE v0.2 onward). A gate check.
  python3 laws/page_check.py [PAGE]            check        python3 laws/page_check.py [PAGE] --render     rewrite derived sections

A rule is stated once, as a list item beginning `**V2.k**`; everything else cites it. Other signed pages' rules are cited
by ID: `C2.S12` is CHARTER v0.2's S12, `V0.reads` SURFACE v0's reads rule. The references carry the rule of every refusal
they make: `[V2.k]` in a surface_check message, `refused(NAME, "C2.X")` in counts_check. A poison declares `# expect: NAME`
and `# rule: ID`; a lawful pack may declare `# exercises: ID, ...`. Checked:
  T1 every rule is stated exactly once, and every cited ID is a stated rule or a known external one;
  T2 every refusal site in the references names a rule the page states or cites;
  T3 every (rule, name) a reference can refuse by at declaration has a poison, and every poison dies by its declared name
     and rule, not merely its name;
  T4 every stated rule is tested: a refusal site with a poison, or a lawful pack or gate check that exercises it;
  T5 the page's generated sections are what the rules and references give.
"""
import glob, os, re, sys
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
EXTERNAL = {"C2.S11", "C2.S12", "C2.S13", "C2.S14", "C2.S15", "C2.J20", "C2.J26", "V0.reads"}
PLAY_ONLY = {("C2.J26", "FALSIFIED"),                # raised during a plate, never at declaration
             ("C2.J20", "PRIOR")}                   # the charter's backstop behind R2 and R3, reached only through the dict interface
GATE_EXERCISES = {"V2.13": "encoding_check.py"}       # rules a gate check exercises beyond the corpus
ID = r"(V2\.\d+|C2\.[A-Z]\d+|V0\.[a-z]+)"

def rules(text):
    defs = re.findall(r"^- \*\*(V2\.\d+)\*\*", text, re.M)
    return defs, set(re.findall(r"\b" + ID + r"\b", text))

def sites():
    out = set()
    s = open(os.path.join(HERE, "surface_check.py"), encoding="utf-8").read()
    for name, rule in re.findall(r'Refused\("([A-Z_]+)", f?["\']\[' + ID + r'\]', s): out.add((rule, name))
    for rule in re.findall(r'\("DUPLICATE", \("\[(V2\.\d+)\] "', s): out.add((rule, "DUPLICATE"))
    c = open(os.path.join(HERE, "counts_check.py"), encoding="utf-8").read()
    for name, rule in re.findall(r'refused\("([A-Z_]+)", "' + ID + r'"\)', c): out.add((rule, name))
    return out

def packs():
    import surface_check as SC
    pois, lawful = [], []
    for f in sorted(glob.glob(os.path.join(HERE, "packs/poison/v02_*.py"))):
        t = open(f, encoding="utf-8", newline="").read()
        want = t.splitlines()[0].replace("# expect:", "").strip()
        rule = (re.search(r"^# rule: (\S+)", t, re.M) or [None, None])[1]
        try: SC.check(t, {}, os.path.dirname(f)); got, grule = "ACCEPTED", None
        except Exception as e:
            got = getattr(e, "name", "?"); m = re.search(r"\[" + ID + r"\]", str(e)); grule = m.group(1) if m else None
        pois.append((os.path.basename(f), want, rule, got, grule))
    for f in sorted(glob.glob(os.path.join(HERE, "packs/ok/*.py"))):
        t = open(f, encoding="utf-8", newline="").read()
        ex = re.search(r"^# exercises: (.+)$", t, re.M)
        if ex: lawful.append((os.path.basename(f), [x.strip() for x in ex.group(1).split(",")]))
    return pois, lawful

def render(defs, site, pois, lawful):
    names = {}
    for rule, name in sorted(site):
        if (rule, name) not in PLAY_ONLY: names.setdefault(name, set()).add(rule)
    ref = "\n".join(f"- **{n}**: " + ", ".join(sorted(rs, key=lambda r: (not r.startswith("V2."), int(r[3:]) if r.startswith("V2.") else 0, r))) for n, rs in sorted(names.items()))
    rows = ["| rule | refused by | poisons | exercised by |", "| --- | --- | --- | --- |"]
    for r in defs + sorted(EXTERNAL):
        ns = sorted({n for (rr, n) in site if rr == r and (rr, n) not in PLAY_ONLY})
        ps = sorted(p[0][4:-3] for p in pois if p[2] == r)
        ex = sorted(l[0][:-3] for l in lawful if r in l[1]) + ([GATE_EXERCISES[r]] if r in GATE_EXERCISES else [])
        if not (ns or ps or ex): continue
        rows.append(f"| {r} | {', '.join(ns) or '—'} | {len(ps)} | {', '.join(ex) or '—'} |")
    return {"refusals": ref + "\n", "trace": "\n".join(rows) + "\n"}

def main(page, write=False):
    text = open(page, encoding="utf-8").read(); fails = []
    defs, cited = rules(text); site = sites(); pois, lawful = packs()
    # T1
    for r in set(defs):
        if defs.count(r) != 1: fails.append(f"T1 {r} is stated {defs.count(r)} times")
    for r in cited:
        if r.startswith("V2.") and r not in defs: fails.append(f"T1 {r} is cited but never stated")
        if not r.startswith("V2.") and r not in EXTERNAL: fails.append(f"T1 {r} is cited but is no known external rule")
    # T2
    for rule, name in sorted(site):
        if rule.startswith("V2.") and rule not in defs: fails.append(f"T2 the reference refuses {name} by {rule}, which the page does not state")
        if not rule.startswith("V2.") and rule not in cited: fails.append(f"T2 the reference refuses {name} by {rule}, which the page does not cite")
    # T3
    for rule, name in sorted(site - PLAY_ONLY):
        if not any(p[2] == rule and p[1] == name for p in pois): fails.append(f"T3 no poison dies by {name} under {rule}")
    for f, want, rule, got, grule in pois:
        if rule is None: fails.append(f"T3 {f} declares no rule")
        elif got != want or grule != rule: fails.append(f"T3 {f} declares {want} by {rule}; it dies by {got} by {grule}")
    # T4
    for r in defs:
        tested = any(rr == r for rr, _ in site) or any(r in l[1] for l in lawful) or r in GATE_EXERCISES
        if not tested: fails.append(f"T4 {r} is stated and nothing tests it")
    # T5
    gen = render(defs, site, pois, lawful)
    for key, body in gen.items():
        m = re.search(r"(<!-- generated:" + key + r" -->\n)(.*?)(<!-- /generated -->)", text, re.S)
        if not m: fails.append(f"T5 the page has no generated section '{key}'"); continue
        if m.group(2) != body:
            if write: text = text[:m.start(2)] + body + text[m.end(2):]
            else: fails.append(f"T5 the generated section '{key}' is stale (run with --render)")
    if write: open(page, "w", encoding="utf-8").write(text); return main(page)
    for f in fails: print("FAIL", f)
    print(f"page: {len(defs)} rules stated once, {len(site)} refusal sites, {len(pois)} poisons, {len(lawful)} lawful packs declaring what they exercise; "
          + ("PAGE CHECK PASSES" if not fails else f"PAGE CHECK FAILS ({len(fails)})"))
    return not fails

if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    page = args[0] if args else os.path.join(HERE, "..", "SURFACE-v0.2.md")
    sys.exit(0 if main(page, "--render" in sys.argv) else 1)
