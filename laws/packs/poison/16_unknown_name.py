# expect: UNKNOWN_NAME
world("p", closed=True)
clock(horizon=1, depth=1, source="elicited")
space(health=["sick", "well"])
prior({"sick": 1 - p_well, "well": 4/5}, source="data")
utility({"treat": {"sick": 0, "well": -2}, "leave": {"sick": -10, "well": 0}}, source="elicited")
price({"test": 1/2}, source="elicited")
act("test", once=True, kernel=table({"sick": {"+": 9/10, "-": 1/10}, "well": {"+": 1/5, "-": 4/5}}, source="data"))
