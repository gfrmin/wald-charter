# expect: NOT_A_DECLARATION
# rule: V2.1
# 3.3 X
world("g0", closed=True)
horizon(1, source="elicited")
depth(1, source="elicited")
space({"answer": ["a1", "a2"]})
globals([])
prior({"a1": 1/2, "a2": 1/2}, source="elicited")
utility({"say a1": by("answer", {"a1": 1, "a2": -2}), "say a2": by("answer", {"a1": -2, "a2": 1}), "abstain": by("answer", {"a1": 0, "a2": 0})}, source="elicited")
price({"ask": 0, "grade": 0}, source="elicited")
act("ask", once=True, kernel=table({"a1": {"a1": 9/10, "a2": 1/10}, "a2": {"a2": 9/10, "a1": 1/10}}, source="elicited"), reads=["answer"])
after("grade", kernel=table({"say a1": {"a1": {"a1": 1}, "a2": {"a2": 1}}, "say a2": {"a1": {"a1": 1}, "a2": {"a2": 1}}, "abstain": {"a1": {"a1": 1}, "a2": {"a2": 1}}}, source="data"), reads=["answer"])
