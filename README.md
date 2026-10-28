# PawPal+ (Module 2 Project)

You are building **PawPal+**, a Streamlit app that helps a pet owner plan care tasks for their pet.

## Scenario

A busy pet owner needs help staying consistent with pet care. They want an assistant that can:

- Track pet care tasks (walks, feeding, meds, enrichment, grooming, etc.)
- Consider constraints (time available, priority, owner preferences)
- Produce a daily plan and explain why it chose that plan

Your job is to design the system first (UML), then implement the logic in Python, then connect it to the Streamlit UI.

## What you will build

Your final app should:

- Let a user enter basic owner + pet info
- Let a user add/edit tasks (duration + priority at minimum)
- Generate a daily schedule/plan based on constraints and priorities
- Display the plan clearly (and ideally explain the reasoning)
- Include tests for the most important scheduling behaviors

## Getting started

### Setup

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### Suggested workflow

1. Read the scenario carefully and identify requirements and edge cases.
2. Draft a UML diagram (classes, attributes, methods, relationships).
3. Convert UML into Python class stubs (no logic yet).
4. Implement scheduling logic in small increments.
5. Add tests to verify key behaviors.
6. Connect your logic to the Streamlit UI in `app.py`.
7. Refine UML so it matches what you actually built.

## 🖥️ Sample Output

Paste a sample of your app's CLI or Streamlit output here so a reader can see what a generated plan looks like:

Output of `python main.py`:

```
Today's Schedule
================
  [ ] 07:30  Mochi    Morning walk            30 min  high    daily
  [ ] 08:00  Luna     Breakfast               10 min  high    daily
  [ ] 12:00  Luna     Flea medication          5 min  high    weekly
  [ ] 18:00  Mochi    Evening walk            30 min  medium  daily
```

## 🧪 Testing PawPal+

Run the full suite from the project root:

```bash
python -m pytest
```

`tests/test_pawpal.py` has 24 tests covering:

- **Basics** — `mark_complete()` flips the status, adding a task increases a pet's task count, the Owner collects tasks from every pet, and duplicate pet names are rejected.
- **Sorting correctness** — tasks come back in chronological order even when added out of order; unpadded times like `"9:00"` sort before `"10:00"`; the date is compared before the time; "today's schedule" excludes other days.
- **Filtering** — by pet (case-insensitive), by completion status, and by both together.
- **Recurrence logic** — a completed daily task creates a new task for the next day (including across a month boundary); weekly tasks move forward 7 days; one-off tasks don't recur; completing a task twice doesn't create a duplicate.
- **Conflict detection** — two tasks at the same time are flagged for different pets and for the same pet; different times or dates are not flagged; completed tasks are ignored.
- **Edge cases and validation** — a pet with no tasks produces an empty schedule and no conflicts; invalid times (`25:00`, `12:60`, `noon`, blank) and invalid frequencies raise `ValueError`.

Tests use fixed dates, so they pass the same way on any day. To make sure the tests really catch bugs, I broke the code on purpose three ways: removed the time normalization, set the daily step to 0 days, and counted completed tasks as conflicts. Each time, at least one test failed.

Sample test output:

```
============================= test session starts ==============================
platform linux -- Python 3.13.18, pytest-9.1.1, pluggy-1.6.0
rootdir: .../pawpal
collected 24 items

tests/test_pawpal.py ........................                            [100%]

============================== 24 passed in 0.10s ==============================
```

**Confidence level: ★★★★☆ (4/5)** — every required behavior and the main edge cases are tested and passing. I'm holding back one star because conflict detection only compares exact start times (overlapping durations aren't caught), and the Streamlit UI is verified by hand rather than by automated tests.

## 📐 Smarter Scheduling

All scheduling logic lives in `pawpal_system.py`.

| Feature | Method(s) | Notes |
|---------|-----------|-------|
| Task sorting | `Scheduler.sort_by_time()`, `Scheduler.get_todays_schedule()` | Chronological order by due date, then `"HH:MM"` time, using `sorted()` with a `lambda` key. Times are normalized to zero-padded `HH:MM` when a `Task` is created (`normalize_time()`), so `"7:30"` correctly sorts before `"18:00"`. |
| Filtering | `Scheduler.filter_tasks(pet_name=..., completed=...)` | Filter by pet name (case-insensitive), by completion status, or both. Leaving a filter as `None` skips it. |
| Conflict handling | `Scheduler.detect_conflicts()` | Groups pending tasks by `(date, start time)` and returns a readable warning string for every slot with 2+ tasks — across the same pet or different pets. It never raises, so the UI just displays the warnings. |
| Recurring tasks | `Scheduler.mark_task_complete()`, `Task.next_occurrence()` | Completing a `daily` task creates a new copy due the next day (`timedelta(days=1)`); `weekly` creates one 7 days later. One-off (`once`) tasks just complete. Completing an already-done task does not create a duplicate. |

## 📸 Demo Walkthrough

Describe your app in numbered steps so a reader can follow along without watching a video:

1. <!-- Describe this step -->
2. <!-- Describe this step -->
3. <!-- Describe this step -->
4. <!-- Describe this step -->
5. <!-- Add more steps as needed -->

**Screenshot or video** *(optional)*: <!-- Insert a screenshot or link to a demo video here -->
