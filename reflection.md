# PawPal+ Project Reflection

## 1. System Design

**Core user actions**

1. **Add a pet** — enter a pet's name, species, and age so PawPal+ can track care for it.
2. **Schedule a care task** — add a task (walk, feeding, medication, vet appointment) for a specific pet with a time, duration, priority, and how often it repeats.
3. **See today's schedule** — view every pet's tasks for today in time order, with warnings when two tasks collide, and check tasks off as they get done.

**a. Initial design**

My initial UML (`diagrams/uml_draft.mmd`) had four classes:

- **Task** (dataclass) — one care activity. Holds the description, time (`"HH:MM"`), duration, priority, frequency (`once` / `daily` / `weekly`), and whether it is completed. Its only behavior is `mark_complete()`.
- **Pet** (dataclass) — the pet's name, species, and age, plus the list of tasks that belong to it. Responsible for `add_task()`.
- **Owner** — the person using the app. Holds a list of pets and can collect every task across all of them with `get_all_tasks()`.
- **Scheduler** — the "brain." It is given an Owner and asks it for tasks, then organizes them (`sort_by_time()`, `get_todays_schedule()`).

Relationships: an Owner *has* many Pets, each Pet *owns* many Tasks (composition — a task doesn't exist without its pet), and the Scheduler *reads from* the Owner rather than storing its own copy of the tasks.

**b. Design changes**

Yes. Reviewing the skeleton showed several gaps, and I changed the design before and during implementation:

1. **Added `due_date` to `Task`.** The draft only had a clock time. Without a date, "today's schedule" can't tell today from tomorrow, and recurrence ("same task, next day") has nothing to add one day to. This was the most important change.
2. **Added `pet_name` to `Task`, set automatically by `Pet.add_task()`.** Once the Scheduler merges tasks from every pet into one list, each task needs to say which pet it belongs to. Otherwise the schedule can't print "Mochi: Morning walk" or group conflicts by pet. I chose a simple name tag over storing a full `Pet` reference inside each `Task`, which would create a circular link that is harder to print and test.
3. **Put recurrence in `Scheduler.mark_task_complete()`, not just in `Task`.** `Task.next_occurrence()` only builds the next copy. The Scheduler decides to attach it to the right pet, because the Scheduler is the class that can look up pets through the Owner. That way a `Task` never needs to know about other objects.
4. **Added `Owner.get_pet()`, `Scheduler.filter_tasks()`, `detect_conflicts()`, and `normalize_time()`.** The final UML (`diagrams/uml_final.mmd`) shows all of these.

---

## 2. Scheduling Logic and Tradeoffs

**a. Constraints and priorities**

The scheduler considers:

- **Date and time** — the main constraint. Everything is ordered by due date, then start time, and "today's schedule" only shows tasks due on the chosen day.
- **Conflicts** — two pending tasks in the same date and time slot produce a warning.
- **Completion status** — finished tasks drop out of conflict checks and can be filtered out.
- **Frequency** — daily and weekly tasks come back automatically after they are completed.
- **Priority and duration** — stored on every task and shown in the CLI and UI so the owner can see what matters most. The scheduler does not reorder tasks by priority.

I decided **time** mattered most because pet care is tied to the clock: meds every 12 hours, walks before work, feeding at the same time each day. An owner mainly needs to know "what's next, and is anything double-booked?" Priority is shown as information so the owner can decide what to skip on a busy day. I kept that decision with the owner instead of having the app silently reorder things.

**b. Tradeoffs**

My conflict detection only flags tasks that start at the **exact same date and time**. It does not check whether durations overlap. For example, a 30-minute walk at 07:30 and breakfast at 07:45 really do overlap, but no warning appears.

I think this is reasonable for a first version. Exact-match checking is simple and fast: one pass that groups tasks by `(date, time)` with a dictionary, instead of comparing every pair of tasks. It catches the most obvious mistake, which is booking two things in the same slot. It also avoids false alarms. Many pet tasks can happen alongside each other, like giving the cat breakfast while the dog finishes eating, so warning about every partial overlap would get noisy. The method returns warning strings and doesn't raise errors, so a conflict never crashes the app. The owner just sees the warning and decides what to do.

---

## 3. AI Collaboration

**a. How you used AI**

I used Claude as an AI coding agent through the whole build, working one phase at a time:

- **Design** — turning my four classes into a Mermaid UML draft and a dataclass skeleton, then reviewing the skeleton for missing relationships. That review found the missing `due_date` and pet link.
- **Implementation** — writing the core classes, then the algorithm layer (sorting with a `lambda` key, filtering, `timedelta`-based recurrence, and the conflict check).
- **Verification** — writing the CLI demo and the pytest suite, running them after every phase, and checking the Streamlit wiring.
- **Documentation** — docstrings, README sections, and the final UML update.

The most helpful requests were **specific and tied to a file or behavior**, like "review `pawpal_system.py` for missing relationships," "what are the edge cases for recurring tasks?", or "make conflict detection return warnings instead of crashing." Broad requests like "make it smarter" were less useful than naming the exact behavior I wanted.

**b. Judgment and verification**

The project hint was to sort tasks with `sorted(tasks, key=lambda t: t.time)` on `"HH:MM"` strings. That's correct only when every time is zero-padded. If someone types `"7:30"`, string comparison puts it **after** `"18:00"`, because the character `"7"` comes after `"1"`. Instead of accepting the one-line sort as-is, I added `normalize_time()`, which validates every time when a `Task` is created and rewrites it as `"07:30"`. The sort stays a simple, readable `lambda`, and it is now always correct. Sorting by `(due_date, time)` also keeps tomorrow's tasks after today's.

For conflict detection, I chose a version that groups tasks into a dictionary keyed by `(date, time)` instead of a nested loop comparing every pair. It's a single pass, and each warning lists every task in the slot at once instead of producing one warning per pair.

**How I verified:** `main.py` deliberately adds `"7:30"` out of order and books two tasks at 12:00, and I checked the printed output. Every rule has a pytest test (including `test_sort_handles_unpadded_hours`). I also broke the code on purpose three times (removing the normalization, setting the daily step to 0 days, and counting completed tasks as conflicts) to confirm the tests fail when the logic is wrong.

**Organization:** instead of one long unstructured conversation, I worked through the phases in order (UML/skeleton → core logic → UI wiring → algorithms → tests → polish) and committed after each one. That kept each step's goal clear and made it easy to see which change introduced what.

---

## 4. Testing and Verification

**a. What you tested**

24 tests in `tests/test_pawpal.py`:

- **Basics:** `mark_complete()`, adding tasks to a pet, the Owner collecting tasks across pets, duplicate pet names.
- **Sorting:** chronological order for out-of-order input, unpadded times, date before time, and "today" excluding other days.
- **Filtering:** by pet, by status, and both.
- **Recurrence:** daily → next day (including March 31 → April 1), weekly → +7 days, one-off tasks don't recur, completing twice doesn't create duplicates.
- **Conflicts:** same time for different pets and for the same pet, no false alarms for different times or dates, completed tasks ignored.
- **Edge cases and validation:** a pet with no tasks, and bad times or frequencies.

These matter because the scheduler's value is that the owner can **trust** it. A sorting bug could show a 7:30 medication after dinner, a recurrence bug could silently drop tomorrow's walk, and a missed conflict could double-book a vet visit. The UI only shows whatever the backend returns, so testing the backend directly is the real evidence that the app works.

**b. Confidence**

**4 out of 5.** All 24 tests pass, they use fixed dates so they don't depend on what day they run, and the deliberate-bug check showed they catch real mistakes. I'm not giving 5 because conflict detection ignores overlapping durations, and the Streamlit UI was checked by hand rather than by automated tests.

Next I would test:
- overlapping-duration conflicts (07:30 for 30 minutes vs. 07:45), once that feature exists;
- tasks that cross midnight (23:30 for 60 minutes);
- weekly recurrence over a daylight-saving change and at the end of the year;
- removing a pet that still has tasks;
- two pets whose names differ only by capitalization in conflict messages.

---

## 5. Reflection

**a. What went well**

The clean split between the logic layer and the UI. Everything smart lives in `pawpal_system.py` and was proven with `main.py` and pytest before Streamlit was involved. As a result, `app.py` is mostly forms that call `Owner.add_pet()`, `Pet.add_task()`, and `Scheduler` methods. I'm also happy with the recurrence flow: you check off a daily walk and tomorrow's walk just appears.

**b. What you would improve**

- Detect **overlapping durations**, not just identical start times, maybe with a setting so tasks like feeding can be marked "okay to overlap."
- Use priority to **suggest a fix** for each conflict (for example, "move the low-priority task").
- **Save data** to a file so pets and tasks survive closing the app (right now `st.session_state` only lasts for one browser session).
- Allow **editing and deleting** tasks from the UI, and give each task a unique ID instead of finding it by its fields.

**c. Key takeaway**

AI makes writing code fast, but I'm still responsible for the **design and the proof**. The AI could produce a working-looking sort or skeleton in seconds, but deciding that a task needs a date, noticing that string sorting breaks on `"7:30"`, and making sure the tests can actually fail were judgment calls I had to check against the UML and requirements. Being the "lead architect" meant deciding what the system should be, asking for focused pieces, and accepting nothing without running it.
