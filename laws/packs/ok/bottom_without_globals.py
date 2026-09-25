# 4.2: v0's bottom, no Global component, an After-act (V2.9's Global value ()).
# exercises: V2.9, V2.14
world("open-a", bottom="none")
horizon(1, source="elicited")
depth(1, source="elicited")
space({"answer": ["a1", "a2", "none"]})
prior({"a1": 9/20, "a2": 9/20, "none": 1/10}, source="elicited")
utility({"say a1": by("answer", {"a1": 1, "a2": -2, "none": -2}), "say a2": by("answer", {"a1": -2, "a2": 1, "none": -2}), "abstain": by("answer", {"a1": 0, "a2": 0, "none": 0})}, source="elicited")
price({"ask": 0, "grade": 0}, source="elicited")
act("ask", once=True, kernel=table({"a1": {"a1": 9/10, "a2": 1/10}, "a2": {"a2": 9/10, "a1": 1/10}, "none": {"a1": 1/2, "a2": 1/2}}, source="elicited"), reads=["answer"])
after("grade", kernel=table({"say a1": {"a1": {"a1": 1}, "a2": {"a2": 1}, "none": {"a1": 1/10, "a2": 1/10, "none": 4/5}}, "say a2": {"a1": {"a1": 1}, "a2": {"a2": 1}, "none": {"a1": 1/10, "a2": 1/10, "none": 4/5}}, "abstain": {"a1": {"a1": 1}, "a2": {"a2": 1}, "none": {"a1": 1/10, "a2": 1/10, "none": 4/5}}}, source="data"), reads=["answer"])
