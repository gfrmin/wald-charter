# Surface attack 1, finding 1.1, said lawfully: the cutoff is a fitted parameter in the pack, handed to the host.
world("cutoff", closed=True)
horizon(1, source="elicited")
depth(1, source="elicited")
space({"health": ["sick", "well"], "marker": ["m10", "m40", "m80"]})
param("cutoff", 42, source="fitted")
prior({("sick", "m10"): 1/50, ("sick", "m40"): 3/50, ("sick", "m80"): 6/50,
       ("well", "m10"): 24/50, ("well", "m40"): 12/50, ("well", "m80"): 4/50}, source="data")
utility({"treat": by("health", {"sick": 0, "well": -2}), "leave": by("health", {"sick": -10, "well": 0})}, source="elicited")
price({"assay": 7/10}, source="elicited")
act("assay", once=True, kernel=host("over_cutoff", cutoff, source="fitted"), reads=["marker"])
