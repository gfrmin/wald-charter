# expect: DUPLICATE
world("wordle mini", closed=True)
horizon(3, source="data")
depth(3, source="elicited")
space({"answer": ["cat", "cot", "dog"]})
prior({"cat": 1/3, "cot": 1/3, "dog": 1/3}, source="data")
utility({"give up": {"cat": -10, "cot": -10, "dog": -10}},
        ending={"cat": {"ggg": {"cat": 0, "cot": 0, "dog": 0}, "ggg": {"cat": 1, "cot": 1, "dog": 1}},
                "cot": {"ggg": {"cat": 0, "cot": 0, "dog": 0}},
                "dog": {"ggg": {"cat": 0, "cot": 0, "dog": 0}}}, source="elicited")
price({"cat": 1, "cot": 1, "dog": 1}, source="data")
act("cat", once=True, kernel=table({"cat": {"---": 0, "g-g": 0, "ggg": 1}, "cot": {"---": 0, "g-g": 1, "ggg": 0}, "dog": {"---": 1, "g-g": 0, "ggg": 0}}, source="data"), reads=["answer"])
act("cot", once=True, kernel=table({"cat": {"-g-": 0, "g-g": 1, "ggg": 0}, "cot": {"-g-": 0, "g-g": 0, "ggg": 1}, "dog": {"-g-": 1, "g-g": 0, "ggg": 0}}, source="data"), reads=["answer"])
act("dog", once=True, kernel=table({"cat": {"---": 1, "-g-": 0, "ggg": 0}, "cot": {"---": 0, "-g-": 1, "ggg": 0}, "dog": {"---": 0, "-g-": 0, "ggg": 1}}, source="data"), reads=["answer"])
