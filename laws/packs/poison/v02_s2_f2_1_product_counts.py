# expect: NOT_A_DECLARATION
# rule: V2.6
# Appendix A with `ask` returning two reports at once: v0's product of the rel-reliable report and a 4/5 one. One episode shipped.
world("appendix-a", closed=True)
horizon(1, source="elicited")
depth(1, source="elicited")
space({"answer": ["a1", "a2"], "rel": ["9/10", "3/5"]})
globals(["rel"])
prior({"9/10": 1/2, "3/5": 1/2}, source="elicited")
local_prior({"9/10": {"a1": 1/2, "a2": 1/2}, "3/5": {"a1": 1/2, "a2": 1/2}}, source="elicited")
utility({"say a1": by("answer", {"a1": 1, "a2": -2}), "say a2": by("answer", {"a1": -2, "a2": 1}), "abstain": by("answer", {"a1": 0, "a2": 0})}, source="elicited")
price({"ask": 0, "grade": 0}, source="elicited")
act("ask", once=True, kernel=product(table({("a1", "9/10"): {"a1": 9/10, "a2": 1/10}, ("a2", "9/10"): {"a2": 9/10, "a1": 1/10}, ("a1", "3/5"): {"a1": 3/5, "a2": 2/5}, ("a2", "3/5"): {"a2": 3/5, "a1": 2/5}}, source="elicited"), by("answer", {"a1": {"a1": 4/5, "a2": 1/5}, "a2": {"a1": 1/5, "a2": 4/5}}, source="elicited")), reads=["answer", "rel"])
after("grade", kernel=table({"say a1": {("a1", "9/10"): {"a1": 1}, ("a2", "9/10"): {"a2": 1}, ("a1", "3/5"): {"a1": 1}, ("a2", "3/5"): {"a2": 1}}, "say a2": {("a1", "9/10"): {"a1": 1}, ("a2", "9/10"): {"a2": 1}, ("a1", "3/5"): {"a1": 1}, ("a2", "3/5"): {"a2": 1}}, "abstain": {("a1", "9/10"): {"a1": 1}, ("a2", "9/10"): {"a2": 1}, ("a1", "3/5"): {"a1": 1}, ("a2", "3/5"): {"a2": 1}}}, source="data"), reads=["answer"])
counts([[[["ask", ["a1", "a1"]]], "say a1", "a1", 1]], sha256="ad87684c914b3341648605e5ed02580db1afa60aebe556128160035b39295834", source="data")
score(3/10, of="counts", source="data")
