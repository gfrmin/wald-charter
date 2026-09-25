# expect: MISSING
# rule: V2.3
# QUESTIONS.md Q17: the cost table before local_prior, which says what the states are that it counts; the reference raised AttributeError.
world("think-with-globals", closed=True)
horizon(2, source="elicited")
depth(1, source="elicited")
space({"answer": ["a1", "a2"], "rel": ["9/10", "3/5"]})
globals(["rel"])
prior({"9/10": 1/2, "3/5": 1/2}, source="elicited")
cost([100, 200, 300, 400], source="elicited")
local_prior({"9/10": {"a1": 1/2, "a2": 1/2}, "3/5": {"a1": 1/2, "a2": 1/2}}, source="elicited")
depth_plus(2, source="elicited")
think(fraction=1/2, source="elicited")
rate(1/1000, source="elicited")
utility({"say a1": by("answer", {"a1": 1, "a2": -2}), "say a2": by("answer", {"a1": -2, "a2": 1}), "abstain": by("answer", {"a1": 0, "a2": 0})}, source="elicited")
price({"ask": 1/20, "grade": 0}, source="elicited")
act("ask", once=False, kernel=table({("a1", "9/10"): {"a1": 9/10, "a2": 1/10}, ("a2", "9/10"): {"a2": 9/10, "a1": 1/10}, ("a1", "3/5"): {"a1": 3/5, "a2": 2/5}, ("a2", "3/5"): {"a2": 3/5, "a1": 2/5}}, source="elicited"), reads=["answer", "rel"])
after("grade", kernel=table({"say a1": {("a1", "9/10"): {"a1": 1}, ("a2", "9/10"): {"a2": 1}, ("a1", "3/5"): {"a1": 1}, ("a2", "3/5"): {"a2": 1}}, "say a2": {("a1", "9/10"): {"a1": 1}, ("a2", "9/10"): {"a2": 1}, ("a1", "3/5"): {"a1": 1}, ("a2", "3/5"): {"a2": 1}}, "abstain": {("a1", "9/10"): {"a1": 1}, ("a2", "9/10"): {"a2": 1}, ("a1", "3/5"): {"a1": 1}, ("a2", "3/5"): {"a2": 1}}}, source="data"), reads=["answer"])
