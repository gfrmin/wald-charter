# expect: PLATE
# A plate learns its instrument lies (one wrong grade), then a right grade falsifies it.
# Its Counts and falsifying record, shipped to the same declaration.
world("liar", closed=True)
horizon(1, source="elicited")
depth(1, source="elicited")
space({"answer": ["a1", "a2"], "inst": ["honest", "liar"]})
globals(["inst"])
prior({"honest": 3/4, "liar": 1/4}, source="elicited")
local_prior({"honest": {"a1": 1/2, "a2": 1/2}, "liar": {"a1": 1/2, "a2": 1/2}}, source="elicited")
utility({"say a1": by("answer", {"a1": 1, "a2": -2}), "say a2": by("answer", {"a1": -2, "a2": 1}), "abstain": by("answer", {"a1": 0, "a2": 0})}, source="elicited")
price({"ask": 0, "grade": 0}, source="elicited")
act("ask", once=True, kernel=table({("a1", "honest"): {"a1": 1, "a2": 0}, ("a2", "honest"): {"a1": 0, "a2": 1}, ("a1", "liar"): {"a1": 0, "a2": 1}, ("a2", "liar"): {"a1": 1, "a2": 0}}, source="elicited"), reads=["answer", "inst"])
after("grade", kernel=table({"say a1": {("a1", "honest"): {"a1": 1, "a2": 0}, ("a1", "liar"): {"a1": 1, "a2": 0}, ("a2", "honest"): {"a1": 0, "a2": 1}, ("a2", "liar"): {"a1": 0, "a2": 1}}, "say a2": {("a1", "honest"): {"a1": 1, "a2": 0}, ("a1", "liar"): {"a1": 1, "a2": 0}, ("a2", "honest"): {"a1": 0, "a2": 1}, ("a2", "liar"): {"a1": 0, "a2": 1}}, "abstain": {("a1", "honest"): {"a1": 1, "a2": 0}, ("a1", "liar"): {"a1": 1, "a2": 0}, ("a2", "honest"): {"a1": 0, "a2": 1}, ("a2", "liar"): {"a1": 0, "a2": 1}}}, source="data"), reads=["answer"])
counts([[[["ask", "a1"]], "say a1", "a2", 1]], sha256="71e648e1643abf37a5417a0b4a4e77140ff6ef6801db791a44e35c35b54cddfc", source="data")
falsifiers([[[["ask", "a1"]], "say a2", "a1"]])
score(0, of="counts", source="data")
