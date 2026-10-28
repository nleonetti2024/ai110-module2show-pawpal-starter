# 🐾 PawPal+

**PawPal+** is a pet-care scheduling app for busy owners. It tracks every pet's daily routine (walks, feedings, medications, appointments), puts them in one chronological schedule, warns you about clashing times, and automatically re-schedules recurring tasks when you check them off.

The backend (`pawpal_system.py`) was built and verified from the command line first (`main.py` + `pytest`), then connected to a Streamlit UI (`app.py`).

## ✨ Features

- **Multi-pet households** — one owner, any number of pets, each with its own task list (duplicate or blank pet names are rejected).
- **Rich tasks** — description, time, date, duration, priority (low / medium / high), and frequency (once / daily / weekly).
- **Sorting by time** — every view is in chronological order (`Scheduler.sort_by_time()`), with times normalized to `HH:MM` so `"7:30"` sorts before `"18:00"`.
- **Filtering** — by pet, by completion status, or both (`Scheduler.filter_tasks()`).
- **Conflict warnings** — flags any two pending tasks booked for the same date and start time, for the same pet or different pets (`Scheduler.detect_conflicts()`), as a warning rather than an error.
- **Daily / weekly recurrence** — completing a recurring task automatically creates its next occurrence one day or one week later using `timedelta` (`Scheduler.mark_task_complete()` → `Task.next_occurrence()`).
- **Input validation** — invalid times (e.g. `25:00`), frequencies, priorities, and durations raise a clear `ValueError`.
- **Session memory** — the Streamlit app keeps your `Owner` object in `st.session_state`, so pets and tasks survive every rerun during a session.

## 🏗️ System Design

| Class | Responsibility |
|-------|----------------|
| `Task` (dataclass) | One care activity: what, when, how long, priority, how often, done or not. Knows how to create its next occurrence. |
| `Pet` (dataclass) | A pet's details and the tasks that belong to it. |
| `Owner` | Holds the pets and gathers all of their tasks. |
| `Scheduler` | The "brain": reads tasks from the Owner and sorts, filters, checks conflicts, and handles completing recurring tasks. |

UML diagrams (Mermaid): `diagrams/uml_draft.mmd` (Phase 1 draft) and `diagrams/uml_final.mmd` (matches the final code; also saved as `diagrams/uml.mmd`). Paste either one into the [Mermaid Live Editor](https://mermaid.live) to view it.

## Getting started

### Setup

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### Run it

```bash
python main.py          # CLI demo
streamlit run app.py    # web app
python -m pytest        # tests
```

## 🖥️ Sample Output

Output of `python main.py`. Tasks are added out of order on purpose, and two tasks share 12:00 to show the conflict warning. (Dates show the day the demo was run.)

```
Tasks in the order they were added:
  18:00  Mochi: Evening walk
  07:30  Mochi: Morning walk
  12:00  Mochi: Vet appointment
  12:00  Luna: Flea medication
  08:00  Luna: Breakfast

Today's Schedule
================
  [ ] Wed 10/28 07:30  Mochi    Morning walk            30 min  high    daily
  [ ] Wed 10/28 08:00  Luna     Breakfast               10 min  high    daily
  [ ] Wed 10/28 12:00  Mochi    Vet appointment         45 min  high    once
  [ ] Wed 10/28 12:00  Luna     Flea medication          5 min  high    weekly
  [ ] Wed 10/28 18:00  Mochi    Evening walk            30 min  medium  daily

Conflict check:
  WARNING: Conflict on 2026-10-28 at 12:00 -> Mochi: Vet appointment, Luna: Flea medication

Filter: Mochi only
==================
  [ ] Wed 10/28 07:30  Mochi    Morning walk            30 min  high    daily
  [ ] Wed 10/28 12:00  Mochi    Vet appointment         45 min  high    once
  [ ] Wed 10/28 18:00  Mochi    Evening walk            30 min  medium  daily

Completed 'Morning walk' -> next one auto-created for 2026-10-29 at 07:30

Filter: still to do (all dates)
===============================
  [ ] Wed 10/28 08:00  Luna     Breakfast               10 min  high    daily
  [ ] Wed 10/28 12:00  Mochi    Vet appointment         45 min  high    once
  [ ] Wed 10/28 12:00  Luna     Flea medication          5 min  high    weekly
  [ ] Wed 10/28 18:00  Mochi    Evening walk            30 min  medium  daily
  [ ] Thu 10/29 07:30  Mochi    Morning walk            30 min  high    daily

Today's Schedule (after completing the walk)
============================================
  [x] Wed 10/28 07:30  Mochi    Morning walk            30 min  high    daily
  [ ] Wed 10/28 08:00  Luna     Breakfast               10 min  high    daily
  [ ] Wed 10/28 12:00  Mochi    Vet appointment         45 min  high    once
  [ ] Wed 10/28 12:00  Luna     Flea medication          5 min  high    weekly
  [ ] Wed 10/28 18:00  Mochi    Evening walk            30 min  medium  daily
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

**Main UI features** (`streamlit run app.py`):

- **Owner name** at the top.
- **1. Add a pet** — name, species, and age → calls `Owner.add_pet()`. Shows a success message, or an error for a blank or duplicate name. Your pets and their task counts are listed underneath.
- **2. Schedule a task** — pick the pet, then enter the task name, date, time, duration, priority, and how often it repeats → creates a `Task` and calls `Pet.add_task()`.
- **3. Schedule** — choose a date to view. You get:
  - a **"Mark a task complete"** picker with a ✅ Done button → `Scheduler.mark_task_complete()`, which reports when the next daily/weekly occurrence was added;
  - **Filter by pet** and **Filter by status** (All / To do / Done) → `Scheduler.filter_tasks()`;
  - a yellow **⚠️ conflict warning** (`st.warning`) for every double-booked time slot → `Scheduler.detect_conflicts()`, or a green `st.success` "No scheduling conflicts";
  - a **table** (`st.table`) of the day's tasks sorted by time, with 🔴/🟡/🟢 priority and ✅/⏳ status, plus a "X of Y done" progress line.

**Example workflow:**

1. Add a pet **Mochi** (dog) and a pet **Luna** (cat).
2. Schedule Mochi's **Evening walk** at 18:00 (daily), then **Morning walk** at 07:30 (daily) — added out of order.
3. Schedule Luna's **Flea meds** at 12:00 (weekly) and Mochi's **Vet visit** at 12:00 (once).
4. Look at **3. Schedule**: the tasks appear in time order (07:30, 12:00, 12:00, 18:00), and a warning says *Conflict at 12:00 → Mochi: Vet visit, Luna: Flea meds*.
5. Mark **Morning walk** done: the app confirms it and says the next daily walk was added for tomorrow at 07:30. The row now shows ✅ done.
6. Set **Filter by pet = Luna** and **Filter by status = To do** → only Luna's flea meds remain.
7. Change **Show schedule for** to tomorrow → the new 07:30 Morning walk is there, created automatically.

**Key Scheduler behaviors shown:** chronological sorting, filtering by pet and status, conflict warnings, and daily recurrence. The same behaviors appear in the CLI output under Sample Output above.
