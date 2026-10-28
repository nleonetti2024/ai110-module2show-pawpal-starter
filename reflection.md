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

- Did your design change during implementation?
- If yes, describe at least one change and why you made it.

---

## 2. Scheduling Logic and Tradeoffs

**a. Constraints and priorities**

- What constraints does your scheduler consider (for example: time, priority, preferences)?
- How did you decide which constraints mattered most?

**b. Tradeoffs**

- Describe one tradeoff your scheduler makes.
- Why is that tradeoff reasonable for this scenario?

---

## 3. AI Collaboration

**a. How you used AI**

- How did you use AI tools during this project (for example: design brainstorming, debugging, refactoring)?
- What kinds of prompts or questions were most helpful?

**b. Judgment and verification**

- Describe one moment where you did not accept an AI suggestion as-is.
- How did you evaluate or verify what the AI suggested?

---

## 4. Testing and Verification

**a. What you tested**

- What behaviors did you test?
- Why were these tests important?

**b. Confidence**

- How confident are you that your scheduler works correctly?
- What edge cases would you test next if you had more time?

---

## 5. Reflection

**a. What went well**

- What part of this project are you most satisfied with?

**b. What you would improve**

- If you had another iteration, what would you improve or redesign?

**c. Key takeaway**

- What is one important thing you learned about designing systems or working with AI on this project?
