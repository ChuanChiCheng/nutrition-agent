# Evaluation response capture correction

The original formal run extracted only `Result.data.message` or `reply`. Structured service results rendered by `nutrition_demo.display.render` were omitted. Recording an approval/rejection result could replace the final reply with null. The judge conversation also excluded approval_result entries.

The corrected `nutrition_eval.episode._reply` calls the same terminal renderer as the application. Each interaction retains its full visible text; the final reply holds the last rendered response. `nutrition_eval.judge._conversation` includes approval_result, allowing the response rubric to consider both the displayed preview and confirmation/rejection.

Capture identity is terminal-render-v1; judge adapter identity is nutrition-reply-judge-v2. Frozen config and CLI metadata record the change and preflight verifies the capture version.

Regression tests reproduce P01 with a rendered preview and structured rejection, assert exact equality with terminal output, and inspect the judge input for both responses. Other tests cover structured profile results, inventory confirmations, and errors. No replacement live evaluation was run; the original formal results remain preserved.
