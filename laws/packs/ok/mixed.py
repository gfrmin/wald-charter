# Surface attack 1, finding 4.2: mixture weights are housed numbers.
world("p", closed=True)
horizon(1, source="elicited")
depth(1, source="elicited")
space({"health": ["sick", "well"]})
prior({"sick": 1/5, "well": 4/5}, source="data")
utility({"treat": {"sick": 0, "well": -2}, "leave": {"sick": -10, "well": 0}}, source="elicited")
price({"test": 1/2}, source="elicited")
act("test", once=True, kernel=mixture([(9/10, table({"sick": {"+": 9/10, "-": 1/10}, "well": {"+": 1/5, "-": 4/5}}, source="data")), (1/10, by("health", {"sick": {"+": 1/2, "-": 1/2}, "well": {"+": 1/2, "-": 1/2}}, source="data"))], source="data"), reads=["health"])
