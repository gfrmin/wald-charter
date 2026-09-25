# expect: PRIOR
# rule: V2.2
# K20: a zero cell in P(Global). v0 refuses a zero prior cell; K20's joint support just leaves its pairs out.
world("zero-global", closed=True)
horizon(1, source="elicited")
depth(1, source="elicited")
space({"answer": ["a1", "a2"], "rel": ["x", "y"]})
globals(["rel"])
prior({"x": 1, "y": 0}, source="elicited")
local_prior({"x": {"a1": 1, "a2": 0}, "y": {"a1": 0, "a2": 1}}, source="elicited")
utility({"say a1": by("answer", {"a1": 1}), "say a2": by("answer", {"a1": -2}), "abstain": by("answer", {"a1": 0})}, source="elicited")
price({"grade": 0}, source="elicited")
after("grade", kernel=table({"say a1": {("a1", "x"): {"a1": 1, "a2": 0}}, "say a2": {("a1", "x"): {"a1": 1, "a2": 0}}, "abstain": {("a1", "x"): {"a1": 1, "a2": 0}}}, source="data"), reads=["answer"])
