# Attack 1, finding 1a, said lawfully: two acts read one draw, and the draw is a component of the space (S2).
world("shared draw", closed=True)
clock(horizon=2, depth=2, source="elicited")
space(side=["x", "y"], draw=["p", "m"])
prior({("x", "p"): 3/8, ("x", "m"): 1/8, ("y", "p"): 1/8, ("y", "m"): 3/8}, source="data")
utility({"go": by("side", {"x": 1, "y": -4}), "hold": by("side", {"x": 0, "y": 0})}, source="elicited")
price({"k1": 1/20, "k2": 1/20}, source="elicited")
act("k1", once=True, kernel=point("draw"), reads=["draw"])
act("k2", once=True, kernel=point("draw"), reads=["draw"])
