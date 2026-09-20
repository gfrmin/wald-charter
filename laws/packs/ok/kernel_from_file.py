# A kernel read from a data file, pinned by the sha256 of its bytes.
world("p", closed=True)
horizon(1, source="elicited")
depth(1, source="elicited")
space({"health": ["sick", "well"]})
prior({"sick": 1/5, "well": 4/5}, source="data")
utility({"treat": {"sick": 0, "well": -2}, "leave": {"sick": -10, "well": 0}}, source="elicited")
price({"test": 1/2}, source="elicited")
act("test", once=True, kernel=data("appendix_kernel.json", sha256="0e540c2b97eaf6a48baf9d2cac4728dc6a84bb0bdd7a953db230ee3bd365a048", source="data"), reads=["health"])
