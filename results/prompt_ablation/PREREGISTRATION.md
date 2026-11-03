# Prompt ablation (registered before running)
Objection addressed: the system prompt ("Use the provided tools to answer"; a separate concerns field) may instruct relay.
Cells where the record contains the truth: (a) benchmark protein tasks, full record, plausible paired-field corruption (the sequence
contradicts the value); (b) agreement arm C (molecular weight asked, three agreeing fields, full record), three samples; (c) coherent
plausible protein errors, full record (nothing in the record contradicts the value). Models: Opus 5, Gemini 4 Argon, DeepSeek V4.1 Flash
(Flash added on (b)). Variants: default; no_tool_instruction; record_errors; two_fields (answer = best estimate, graded as usual).
Predictions. PA1: record_errors lowers relay on (a) by >= 20 points for every model. PA2: no_tool_instruction changes relay on (a) and (b)
by < 10 points for every model (the instruction is not the cause). PA3: two_fields lowers relay of `answer` on (a) by >= 20 points, and
`database_value` matches the record's value in >= 90% of runs. PA4: on (c), no variant lowers relay below 80% for any model: no prompt
can catch an error the record does not contradict. Tests: two-sided McNemar on task-paired outcomes per model; PA4 descriptive.
