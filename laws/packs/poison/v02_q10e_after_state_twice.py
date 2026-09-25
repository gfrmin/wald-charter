# expect: TABLE_SHAPE
# rule: V2.4
# QUESTIONS.md Q10e: in a one-component space a state is a name, so ("good",) is no state; the reference merged it with "good".
world("monitor", closed=True)
horizon(1, source="elicited")
depth(1, source="elicited")
space({"rel": ["good", "poor"]})
globals(["rel"])
prior({"good": 1/2, "poor": 1/2}, source="elicited")
utility({"ship": {"good": 0, "poor": 0}}, source="elicited")
price({"audit": 0}, source="elicited")
after("audit", kernel=table({"ship": {("good",): {"pass": 1/2, "fail": 1/2}, "good": {"pass": 9/10, "fail": 1/10}, "poor": {"pass": 3/5, "fail": 2/5}}}, source="elicited"), reads=["rel"])
