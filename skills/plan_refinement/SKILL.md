---
name: plan_refinement
description: Rules for handling user feedback and updating active workout plans.
---

# Plan Refinement Skill

## Iterative Feedback Rules

When a user requests changes to an existing workout routine:

1.  **Fetch Active Plan:** Use `get_latest_workout_plan` to retrieve the current
    routine.
2.  **Apply Modifications:** Modify target exercises, sets, reps, or rest
    intervals based on user feedback.
3.  **Persist Changes:** Save updated routine using `save_workout_plan`.
4.  **Highlight Refinement:** Present updated routine highlighting the specific
    changes applied.
