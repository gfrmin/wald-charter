# expect: GLOBAL
# Two Globals that copy each other, and a utility that pays on them. No local copies either.
world("paid-on-globals", closed=True)
horizon(1, source="elicited")
depth(1, source="elicited")
space({"coin": ["h", "t"], "g1": ["x", "y"], "g2": ["x", "y"]})
globals(["g1", "g2"])
prior({("x", "x"): 1/2, ("y", "y"): 1/2}, source="elicited")
local_prior({("x", "x"): {"h": 9/10, "t": 1/10}, ("y", "y"): {"h": 1/10, "t": 9/10}}, source="elicited")
utility({"pass": by("coin", {"h": 0, "t": 0}), "bet": {("h", "x", "x"): 1, ("t", "x", "x"): 1, ("h", "y", "y"): -1, ("t", "y", "y"): -1}}, source="elicited")
price({"look": 0}, source="elicited")
after("look", kernel=table({"pass": {("h", "x", "x"): {"h": 1, "t": 0}, ("t", "x", "x"): {"h": 0, "t": 1}, ("h", "y", "y"): {"h": 1, "t": 0}, ("t", "y", "y"): {"h": 0, "t": 1}}, "bet": {("h", "x", "x"): {"h": 1, "t": 0}, ("t", "x", "x"): {"h": 0, "t": 1}, ("h", "y", "y"): {"h": 1, "t": 0}, ("t", "y", "y"): {"h": 0, "t": 1}}}, source="data"), reads=["coin"])
