# expect: PLATE
# rule: C2.S13
# Finding 1.1, scaled: two such records as "falsifiers" — each record once, as the draft asks.
world("f1-1b", closed=True)
horizon(1, source="elicited")
depth(1, source="elicited")
space({"answer": ["a1", "a2"], "base": ["g1", "g2"]})
globals(["base"])
prior({"g1": 1/2, "g2": 1/2}, source="elicited")
local_prior({"g1": {"a1": 4/5, "a2": 1/5}, "g2": {"a1": 1/5, "a2": 4/5}}, source="elicited")
utility({"say a1": by("answer", {"a1": 1, "a2": -1}), "say a2": by("answer", {"a1": -1, "a2": 1})}, source="elicited")
price({"ask": 3}, source="elicited")
act("ask", once=True, kernel=table({("a1", "g1"): {"a1": 1}, ("a2", "g1"): {"a2": 1}, ("a1", "g2"): {"a1": 1}, ("a2", "g2"): {"a2": 1}}, source="elicited"), reads=["answer"])
counts([], sha256="84ba3a612d1963d61a03863c0bf816bf41989d1da46845116f15cfcb30e90b9c", source="data")
falsifiers([[[["ask", "a2"]], "say a2", None], [[["ask", "a2"]], "say a1", None]])
score(1, of="counts", source="data")
