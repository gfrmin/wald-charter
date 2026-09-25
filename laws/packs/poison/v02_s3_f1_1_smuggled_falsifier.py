# expect: PLATE
# rule: C2.S13
# Finding 1.1: a "falsifying record" no plate can leave — a terminal end and no after-report, in a World with no After-act. Accepted; the prior conditions on it; the Score does not see it.
world("f1-1", closed=True)
horizon(1, source="elicited")
depth(1, source="elicited")
space({"answer": ["a1", "a2"], "base": ["g1", "g2"]})
globals(["base"])
prior({"g1": 1/2, "g2": 1/2}, source="elicited")
local_prior({"g1": {"a1": 4/5, "a2": 1/5}, "g2": {"a1": 1/5, "a2": 4/5}}, source="elicited")
utility({"say a1": by("answer", {"a1": 1, "a2": -1}), "say a2": by("answer", {"a1": -1, "a2": 1})}, source="elicited")
price({"ask": 3}, source="elicited")
act("ask", once=True, kernel=table({("a1", "g1"): {"a1": 1}, ("a2", "g1"): {"a2": 1}, ("a1", "g2"): {"a1": 1}, ("a2", "g2"): {"a2": 1}}, source="elicited"), reads=["answer"])
counts([], sha256="71a60bfe1fc5708cb0b8f59ef618c69e7fbf3a09602859467d3eb5c114cd00d1", source="data")
falsifiers([[[["ask", "a2"]], "say a2", None]])
score(1, of="counts", source="data")
