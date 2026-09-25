# Appendix A with a free `once` act `peek` whose outcome `drop` ends the episode (brief 007's Q8, brief 008's Q14): the After-act has a row for the ending end, written (act, outcome).
# exercises: V2.5
world("ending-outcome-graded", closed=True)
horizon(2, source="elicited")
depth(2, source="elicited")
space({"answer": ["a1", "a2"], "rel": ["9/10", "3/5"]})
globals(["rel"])
prior({"9/10": 1/2, "3/5": 1/2}, source="elicited")
local_prior({"9/10": {"a1": 1/2, "a2": 1/2}, "3/5": {"a1": 1/2, "a2": 1/2}}, source="elicited")
utility({"say a1": by("answer", {"a1": 1, "a2": -2}), "say a2": by("answer", {"a1": -2, "a2": 1}), "abstain": by("answer", {"a1": 0, "a2": 0})}, ending={"peek": {"drop": by("answer", {"a1": 0, "a2": 0})}}, source="elicited")
price({"ask": 0, "peek": 0, "grade": 0}, source="elicited")
act("ask", once=True, kernel=table({("a1", "9/10"): {"a1": 9/10, "a2": 1/10}, ("a2", "9/10"): {"a2": 9/10, "a1": 1/10}, ("a1", "3/5"): {"a1": 3/5, "a2": 2/5}, ("a2", "3/5"): {"a2": 3/5, "a1": 2/5}}, source="elicited"), reads=["answer", "rel"])
act("peek", once=True, kernel=table({("a1", "9/10"): {"drop": 1/2, "go": 1/2}, ("a2", "9/10"): {"drop": 1/2, "go": 1/2}, ("a1", "3/5"): {"drop": 1/2, "go": 1/2}, ("a2", "3/5"): {"drop": 1/2, "go": 1/2}}, source="elicited"), reads=["answer"])
after("grade", kernel=table({"say a1": {("a1", "9/10"): {"a1": 1}, ("a2", "9/10"): {"a2": 1}, ("a1", "3/5"): {"a1": 1}, ("a2", "3/5"): {"a2": 1}}, "say a2": {("a1", "9/10"): {"a1": 1}, ("a2", "9/10"): {"a2": 1}, ("a1", "3/5"): {"a1": 1}, ("a2", "3/5"): {"a2": 1}}, "abstain": {("a1", "9/10"): {"a1": 1}, ("a2", "9/10"): {"a2": 1}, ("a1", "3/5"): {"a1": 1}, ("a2", "3/5"): {"a2": 1}}, ("peek", "drop"): {("a1", "9/10"): {"a1": 1}, ("a2", "9/10"): {"a2": 1}, ("a1", "3/5"): {"a1": 1}, ("a2", "3/5"): {"a2": 1}}}, source="data"), reads=["answer"])
