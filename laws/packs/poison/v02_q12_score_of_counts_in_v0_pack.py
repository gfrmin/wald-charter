# expect: MISSING
# rule: V2.8
# QUESTIONS.md Q12: a Score of Counts in a pack with no Counts, and nothing else of SURFACE v0.2; the reference dropped it.
world("p", closed=True)
horizon(1, source="elicited")
depth(1, source="elicited")
space({"health": ["sick", "well"]})
prior({"sick": 1/5, "well": 4/5}, source="data")
utility({"treat": {"sick": 0, "well": -2}, "leave": {"sick": -10, "well": 0}}, source="elicited")
price({"test": 1/2}, source="elicited")
act("test", once=True, kernel=table({"sick": {"+": 9/10, "-": 1/10}, "well": {"+": 1/5, "-": 4/5}}, source="data"), reads=["health"])
score(1, of="counts", source="data")
