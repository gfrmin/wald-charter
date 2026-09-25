# expect: NOT_A_DECLARATION
# rule: V2.11
# The grade reports a1 as U+1F600 and a2 as the surrogate pair spelt by escapes. Counts: one grade, U+1F600 written as itself.
world("smile", closed=True)
horizon(1, source="elicited")
depth(1, source="elicited")
space({"answer": ["a1", "a2"], "rel": ["9/10", "1/10"]})
globals(["rel"])
prior({"9/10": 1/2, "1/10": 1/2}, source="elicited")
local_prior({"9/10": {"a1": 1/2, "a2": 1/2}, "1/10": {"a1": 1/2, "a2": 1/2}}, source="elicited")
utility({"say a1": by("answer", {"a1": 1, "a2": -2}), "say a2": by("answer", {"a1": -2, "a2": 1}), "abstain": by("answer", {"a1": 0, "a2": 0})}, source="elicited")
price({"ask": 0, "grade": 0}, source="elicited")
act("ask", once=True, kernel=table({("a1", "9/10"): {"a1": 9/10, "a2": 1/10}, ("a2", "9/10"): {"a2": 9/10, "a1": 1/10}, ("a1", "1/10"): {"a1": 1/10, "a2": 9/10}, ("a2", "1/10"): {"a2": 1/10, "a1": 9/10}}, source="elicited"), reads=["answer", "rel"])
after("grade", kernel=table({"say a1": {("a1", "9/10"): {"😀": 1, "\ud83d\ude00": 0}, ("a1", "1/10"): {"😀": 1, "\ud83d\ude00": 0}, ("a2", "9/10"): {"😀": 0, "\ud83d\ude00": 1}, ("a2", "1/10"): {"😀": 0, "\ud83d\ude00": 1}}, "say a2": {("a1", "9/10"): {"😀": 1, "\ud83d\ude00": 0}, ("a1", "1/10"): {"😀": 1, "\ud83d\ude00": 0}, ("a2", "9/10"): {"😀": 0, "\ud83d\ude00": 1}, ("a2", "1/10"): {"😀": 0, "\ud83d\ude00": 1}}, "abstain": {("a1", "9/10"): {"😀": 1, "\ud83d\ude00": 0}, ("a1", "1/10"): {"😀": 1, "\ud83d\ude00": 0}, ("a2", "9/10"): {"😀": 0, "\ud83d\ude00": 1}, ("a2", "1/10"): {"😀": 0, "\ud83d\ude00": 1}}}, source="data"), reads=["answer"])
counts([[[["ask", "a1"]], "say a1", "😀", 1]], sha256="92042f78d6f088ab810a54a93b08441336a99295484e4065b2c8526ffed4b1c3", source="data")
score(1/4, of="counts", source="data")
