---
name: workout_planning
description: Guidelines for querying exercise catalog and structuring routines.
---

# Workout Planning Skill

## 1. Dynamic Catalog Querying

Query the database catalog using `search_exercise_catalog` with filter criteria:

*   `equipment`: Match user equipment (`bodyweight`, `dumbbell`, `barbell`).
*   `primary_goal`: Match goal (`strength`, `muscle_gain`, `endurance`,
    `weight_loss`).
*   `muscle_group`: Target groups (`chest`, `back`, `legs`, `shoulders`,
    `cardio`, `core`).

--------------------------------------------------------------------------------

## 2. Complete Session Structure (Warm-Up, Main Block, Cool-Down)

Every training session MUST be structured into 3 distinct phases:

### Phase 1: Dynamic Warm-Up (5 – 10 Mins)

*   Query dynamic mobility and warm-up exercises targeting muscle groups.

### Phase 2: Main Exercise Block (30 – 45 Mins)

#### A. Resistance & Strength Track (`strength`, `muscle_gain`, `hypertrophy`):

Structure 4 to 5 complementary exercises retrieved from
`search_exercise_catalog`:

1.  **Main Heavy Compound Movement:** (3-5 sets)
2.  **Secondary Compound Movement:** (3-4 sets)
3.  **Target Muscle Isolation Exercise:** (3 sets)
4.  **Core / Stamina Finisher:** (3 sets)

#### B. Cardio & Endurance Track (`endurance`, `cardio`, `weight_loss`):

Structure cardio-focused sessions retrieved from `search_exercise_catalog`:

1.  **Primary Aerobic Block:** High-Intensity Interval Training (HIIT) OR
    Steady-State Zone 2 Cardio (20 to 30 mins).
2.  **Secondary Core & Stamina Finisher:** Core conditioning or bodyweight
    circuit (3 sets).

### Phase 3: Cool-Down & Static Stretching (5 – 10 Mins)

*   Query static stretches and recovery exercises targeting trained muscles.

--------------------------------------------------------------------------------

## 3. Schedule & Unavailable Days

*   Respect user unavailable days. Mark unavailable days strictly as **Rest &
    Recovery Days**.
