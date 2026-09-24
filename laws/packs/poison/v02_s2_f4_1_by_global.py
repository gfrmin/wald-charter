# expect: GLOBAL
# The answer copies the Global (P(answer | rel) zero off the diagonal); the utility is spelt by('rel').
world("diagonal", closed=True)
horizon(1, source="elicited")
depth(1, source="elicited")
space({"answer": ["a1", "a2"], "rel": ["x", "y"]})
globals(["rel"])
prior({"x": 1/2, "y": 1/2}, source="elicited")
local_prior({"x": {"a1": 1, "a2": 0}, "y": {"a1": 0, "a2": 1}}, source="elicited")
utility({"say a1": by("rel", {"x": 1, "y": -2}), "say a2": by("rel", {"x": -2, "y": 1}), "abstain": by("rel", {"x": 0, "y": 0})}, source="elicited")
price({"grade": 0}, source="elicited")
after("grade", kernel=table({"say a1": {("a1", "x"): {"a1": 1, "a2": 0}, ("a2", "y"): {"a1": 0, "a2": 1}}, "say a2": {("a1", "x"): {"a1": 1, "a2": 0}, ("a2", "y"): {"a1": 0, "a2": 1}}, "abstain": {("a1", "x"): {"a1": 1, "a2": 0}, ("a2", "y"): {"a1": 0, "a2": 1}}}, source="data"), reads=["answer"])
