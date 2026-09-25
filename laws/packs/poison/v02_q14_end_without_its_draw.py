# expect: PLATE
# rule: C2.S13
# QUESTIONS.md Q14: a record that ends at peek's ending outcome with no draw of it; no episode writes that, so no declaration could have.
world("ending-outcome-graded", closed=True)
horizon(2, source="elicited")
depth(2, source="elicited")
space({"answer": ["a1", "a2"], "rel": ["9/10", "3/5"]})
globals(["rel"])
prior({"9/10": 1/2, "3/5": 1/2}, source="elicited")
local_prior({"9/10": {"a1": 1/2, "a2": 1/2}, "3/5": {"a1": 1/2, "a2": 1/2}}, source="elicited")
utility({"say a1": by("answer", {"a1": 1, "a2": -2}), "say a2": by("answer", {"a1": -2, "a2": 1}), "abstain": by("answer", {"a1": 0, "a2": 0})}, ending={"peek": {"drop": by("answer", {"a1": 1/2, "a2": 1/2})}}, source="elicited")
price({"ask": 0, "peek": 0, "grade": 0}, source="elicited")
act("ask", once=True, kernel=table({("a1", "9/10"): {"a1": 9/10, "a2": 1/10}, ("a2", "9/10"): {"a2": 9/10, "a1": 1/10}, ("a1", "3/5"): {"a1": 3/5, "a2": 2/5}, ("a2", "3/5"): {"a2": 3/5, "a1": 2/5}}, source="elicited"), reads=["answer", "rel"])
act("peek", once=True, kernel=table({("a1", "9/10"): {"drop": 1/2, "go": 1/2}, ("a2", "9/10"): {"drop": 1/2, "go": 1/2}, ("a1", "3/5"): {"drop": 1/2, "go": 1/2}, ("a2", "3/5"): {"drop": 1/2, "go": 1/2}}, source="elicited"), reads=["answer"])
after("grade", kernel=table({"say a1": {("a1", "9/10"): {"a1": 1}, ("a2", "9/10"): {"a2": 1}, ("a1", "3/5"): {"a1": 1}, ("a2", "3/5"): {"a2": 1}}, "say a2": {("a1", "9/10"): {"a1": 1}, ("a2", "9/10"): {"a2": 1}, ("a1", "3/5"): {"a1": 1}, ("a2", "3/5"): {"a2": 1}}, "abstain": {("a1", "9/10"): {"a1": 1}, ("a2", "9/10"): {"a2": 1}, ("a1", "3/5"): {"a1": 1}, ("a2", "3/5"): {"a2": 1}}, ("peek", "drop"): {("a1", "9/10"): {"a1": 1}, ("a2", "9/10"): {"a2": 1}, ("a1", "3/5"): {"a1": 1}, ("a2", "3/5"): {"a2": 1}}}, source="data"), reads=["answer"])
counts([[[], 'end:peek=drop', 'a1', 1]], sha256='3cd94f9684c247499b80fb17fda21866d849b067f0b53a58e8b1a21ae8b430dd', source="data")
score(1/2, of="counts", source="data")
