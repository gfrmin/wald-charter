# expect: UNDECLARED_READ
world("tied", closed=True)
horizon(1, source="elicited")
depth(1, source="elicited")
space({"side": ["x", "y"], "draw": ["p", "m"]})
prior({("x", "p"): 1/2, ("y", "m"): 1/2}, source="data")
utility({"go": by("side", {"x": 1, "y": -4}), "hold": by("side", {"x": 0, "y": 0})}, source="elicited")
price({"k1": 1/20}, source="elicited")
act("k1", once=True, kernel=point("draw"), reads=["side"])
