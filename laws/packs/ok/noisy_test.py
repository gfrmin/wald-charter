# A parameter, arithmetic in cells, and a garbled instrument: the appendix test read through a lying channel.
world("noisy test", closed=True)
clock(horizon=1, depth=1, source="elicited")
space(health=["sick", "well"])
param("lie", 1/10, source="elicited")
prior({"sick": 1/5, "well": 4/5}, source="data")
utility({"treat": {"sick": 0, "well": -2}, "leave": {"sick": -10, "well": 0}}, source="elicited")
price({"test": 1/2}, source="elicited")
act("test", once=True,
    kernel=compose(table({"sick": {"+": 9/10, "-": 1/10}, "well": {"+": 1/5, "-": 4/5}}, source="elicited"),
                   {"+": {"+": 1 - lie, "-": lie}, "-": {"+": lie, "-": 1 - lie}}, source="elicited"))
