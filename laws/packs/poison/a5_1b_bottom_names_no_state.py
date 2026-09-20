# expect: ZERO_EVIDENCE
world("p", bottom="other")
horizon(1, source="elicited")
depth(1, source="elicited")
space({"health": ["sick", "well", "rest"]})
prior({"sick": 1/5, "well": 3/5, "rest": 1/5}, source="data")
utility({"treat": {"sick": 0, "well": -2, "rest": -1}, "leave": {"sick": -10, "well": 0, "rest": -1}}, source="elicited")
price({"test": 1/2}, source="elicited")
act("test", once=True, kernel=table({"sick": {"+": 9/10, "-": 1/10}, "well": {"+": 1/5, "-": 4/5}, "rest": {"+": 1/2, "-": 1/2}}, source="data"), reads=["health"])
