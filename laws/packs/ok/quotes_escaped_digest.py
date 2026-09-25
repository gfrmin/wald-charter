# 4.1: an outcome name holding a double quote.
# exercises: V2.13
world("quote", closed=True)
horizon(1, source="elicited")
depth(1, source="elicited")
space({"answer": ["p", "q"], "rel": ["hi", "lo"]})
globals(["rel"])
prior({"hi": 1/2, "lo": 1/2}, source="elicited")
local_prior({"hi": {"p": 1/2, "q": 1/2}, "lo": {"p": 1/2, "q": 1/2}}, source="elicited")
utility({"say p": by("answer", {"p": 1, "q": -2}), "say q": by("answer", {"p": -2, "q": 1}), "abstain": by("answer", {"p": 0, "q": 0})}, source="elicited")
price({"ask": 1/4}, source="elicited")
act("ask", once=True, kernel=table({("p", "hi"): {"p": 4/5, "q": 1/10, 'p"]],"say p",null,1],[[["ask","q': 1/10}, ("q", "hi"): {"q": 4/5, "p": 1/10, 'p"]],"say p",null,1],[[["ask","q': 1/10}, ("p", "lo"): {"p": 1/2, "q": 1/4, 'p"]],"say p",null,1],[[["ask","q': 1/4}, ("q", "lo"): {"q": 1/2, "p": 1/4, 'p"]],"say p",null,1],[[["ask","q': 1/4}}, source="elicited"), reads=["answer", "rel"])
counts([[[["ask", 'p"]],"say p",null,1],[[["ask","q']], "say q", None, 1]], sha256="aa91714c44b937a1eee767b21b7b6f96f3471a1692e84fe859941cf6435c44ba", source="data")
score(7/40, of="counts", source="data")
