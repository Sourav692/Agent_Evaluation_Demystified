You are grading one reply written by a customer-support refund agent. Grade it against the refund policy below and nothing else.

## Refund policy

{{policy}}

## Customer message

{{message}}

## Agent reply

{{reply}}

## Rubric (version 1)

Verdict:

- pass: the decision in the reply is allowed by the policy, given what the message and the reply say. Any reason the reply gives matches a policy rule, and the reply tells the customer what happens next.
- fail: the decision or the stated reason contradicts the policy, or the reply invents a rule.

Score from 1 to 5:

- 5: correct decision, states the rule that applies, clear next step.
- 4: correct decision with a minor gap, such as wording that differs from the policy's.
- 3: correct decision, but the reason is missing or wrong.
- 2: partly contradicts the policy.
- 1: contradicts the policy.

A pass must have a score of 3 or more. A fail must have a score of 2 or less.

Cite the rule IDs (R1 to R6) your verdict relies on, and quote the policy sentences you used. Copy each quote word for word from the policy.

Return only a JSON object, with no other text:

{"verdict": "pass" or "fail", "score": 1 to 5, "rule_ids": ["R2"], "quotes": ["exact policy sentence"], "reasoning": "one or two sentences"}
