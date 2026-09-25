# expect: AFTER
# rule: C2.S12
# QUESTIONS.md Q10d: a World with a catch-all gives every after-outcome mass there; the grade reveals a1 at (a1, 9/10), never a2.
world("appendix-a", bottom=("a1", "9/10"))
horizon(1, source="elicited")
depth(1, source="elicited")
space({"answer": ["a1", "a2"], "rel": ["9/10", "3/5"]})
prior({("a1", "9/10"): 1/4, ("a2", "9/10"): 1/4, ("a1", "3/5"): 1/4, ("a2", "3/5"): 1/4}, source="elicited")
utility({"say a1": by("answer", {"a1": 1, "a2": -2}), "say a2": by("answer", {"a1": -2, "a2": 1}), "abstain": by("answer", {"a1": 0, "a2": 0})}, source="elicited")
price({"ask": 0, "grade": 0}, source="elicited")
act("ask", once=True, kernel=table({("a1", "9/10"): {"a1": 9/10, "a2": 1/10}, ("a2", "9/10"): {"a2": 9/10, "a1": 1/10}, ("a1", "3/5"): {"a1": 3/5, "a2": 2/5}, ("a2", "3/5"): {"a2": 3/5, "a1": 2/5}}, source="elicited"), reads=["answer", "rel"])
after("grade", kernel=table({"say a1": {("a1", "9/10"): {"a1": 1}, ("a2", "9/10"): {"a2": 1}, ("a1", "3/5"): {"a1": 1}, ("a2", "3/5"): {"a2": 1}}, "say a2": {("a1", "9/10"): {"a1": 1}, ("a2", "9/10"): {"a2": 1}, ("a1", "3/5"): {"a1": 1}, ("a2", "3/5"): {"a2": 1}}, "abstain": {("a1", "9/10"): {"a1": 1}, ("a2", "9/10"): {"a2": 1}, ("a1", "3/5"): {"a1": 1}, ("a2", "3/5"): {"a2": 1}}}, source="data"), reads=["answer", "rel"])
