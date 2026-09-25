# Finding 4.1: a monitor — every component Global, no local_prior (§1, K19) — shipping one graded episode.
# exercises: V2.6, V2.8
world("monitor", closed=True)
horizon(1, source="elicited")
depth(1, source="elicited")
space({"rel": ["9/10", "3/5"]})
globals(["rel"])
prior({"9/10": 1/2, "3/5": 1/2}, source="elicited")
utility({"file": {"9/10": 0, "3/5": 0}}, source="elicited")
price({"grade": 0}, source="elicited")
after("grade", kernel=table({"file": {"9/10": {"right": 9/10, "wrong": 1/10}, "3/5": {"right": 3/5, "wrong": 2/5}}}, source="elicited"), reads=["rel"])
counts([[[], "file", "right", 1]], sha256="28be867e442d14e525cbde62198fab12853558e10ef0bd9d8e2dc2ca9298df7b", source="data")
score(3/4, of="counts", source="data")
