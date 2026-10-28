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

I used Claude (in agent mode on claude.ai) as the main builder for this project, and I acted as the person directing and checking the work. I gave it the assignment instructions and the link to the CodePath starter repo, and told it to do only the required parts and skip the optional extensions. Before it started, it asked what it needed: the starter code, and where the finished work should go.

It then worked through the phases in order (UML draft and class skeleton → core classes and `main.py` → Streamlit wiring → sorting, filtering, recurrence, and conflicts → tests → UI polish and docs), with a separate git commit after each phase. My part was getting the work into my own fork and running it myself on my computer.

The most useful prompts were the ones that set clear limits: what to build, what to leave out, and that it should tell me what it needed before starting instead of guessing.

**b. Judgment and verification**

I didn't take "it works" on faith, because the AI couldn't check everything itself. Its environment couldn't install Streamlit, so it tested `app.py` with a fake stand-in. The only real proof that the UI works was me running it. When I did, I hit problems the AI couldn't have seen:

- `git` wasn't installed on my Windows machine, so my first push failed and I had to install Git first.
- After installing the requirements, `streamlit run app.py` wasn't recognized because the Microsoft Store version of Python doesn't put Streamlit's folder on the PATH. Running `python -m streamlit run app.py` fixed it, and the app loaded and worked.

I also checked the backend separately from the UI by running `python main.py` and `python -m pytest`.

One design decision that came up during the build: the assignment suggests sorting `"HH:MM"` strings with a simple `lambda` key. The agent pointed out that this breaks when a time isn't zero-padded (`"7:30"` sorts after `"18:00"` as text), so instead of using the hint as-is, every time is normalized to `"07:30"` when a task is created. There's a test for that case (`test_sort_handles_unpadded_hours`), and the demo deliberately uses `"7:30"` to show it. The agent also broke the code on purpose three times to prove the tests can actually fail, so a passing run means something.

**Staying organized:** everything happened in one conversation, but each phase ended with its own commit (`chore:` skeleton → `feat:` core → `feat:` UI → `feat:` algorithms → `test:` suite → `docs:` final), so the commit history shows exactly what changed at each step.

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

An AI agent can build a whole working project very quickly, but "the AI says it works" isn't the same as it working on my machine. The code itself was fine, but the problems I actually hit were setup problems (Git missing, Streamlit not on the PATH) that only showed up when I ran things myself. Being the "lead architect" with a tool this capable means setting the scope clearly, checking the result against the requirements, and verifying it on my own computer. I also need to understand the design well enough to explain it, since I'm the one turning it in.
