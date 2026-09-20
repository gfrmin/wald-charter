# Wordle on three words. Feedback is a host instrument: a pure function of the state, sourced, with no number inside it.
world("wordle mini", closed=True)
horizon(3, source="data")
depth(3, source="elicited")
space({"answer": ["cat", "cot", "dog"]})
prior({"cat": 1/3, "cot": 1/3, "dog": 1/3}, source="data")
utility({"give up": {"cat": -10, "cot": -10, "dog": -10}},
        ending={"cat": {"ggg": {"cat": 0, "cot": 0, "dog": 0}},
                "cot": {"ggg": {"cat": 0, "cot": 0, "dog": 0}},
                "dog": {"ggg": {"cat": 0, "cot": 0, "dog": 0}}}, source="data")
price({"cat": 1, "cot": 1, "dog": 1}, source="data")
act("cat", once=True, kernel=host("fb_cat", source="data"), reads=["answer"])
act("cot", once=True, kernel=host("fb_cot", source="data"), reads=["answer"])
act("dog", once=True, kernel=host("fb_dog", source="data"), reads=["answer"])
