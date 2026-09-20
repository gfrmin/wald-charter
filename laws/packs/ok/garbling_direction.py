# Surface attack 2, finding 3.1: the outer key of a garbling is what the first kernel emitted; the inner key is what is seen.
world("turn", closed=True)
horizon(1, source="elicited")
depth(1, source="elicited")
space({"s": ["a", "b", "c"]})
prior({"a": 1/2, "b": 1/4, "c": 1/4}, source="data")
utility({"go": {"a": 1, "b": 1, "c": -5}, "hold": {"a": 0, "b": 0, "c": 0}}, source="elicited")
price({"look": 3/8}, source="elicited")
act("look", once=True, kernel=compose(point("s"), {"a": {"a": 2/3, "b": 1/3, "c": 0}, "b": {"a": 0, "b": 2/3, "c": 1/3}, "c": {"a": 1/3, "b": 0, "c": 2/3}}, source="elicited"), reads=["s"])
