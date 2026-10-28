"""PawPal+ logic layer: Owner, Pet, Task, and Scheduler classes."""

from dataclasses import dataclass, field, replace
from collections import defaultdict
from datetime import date, datetime, timedelta

VALID_PRIORITIES = ("low", "medium", "high")
VALID_FREQUENCIES = ("once", "daily", "weekly")
RECURRENCE_STEP = {"daily": timedelta(days=1), "weekly": timedelta(weeks=1)}


def normalize_time(value: str) -> str:
    """Validate a clock time and return it zero-padded as "HH:MM" (e.g. "9:05" -> "09:05")."""
    try:
        return datetime.strptime(value.strip(), "%H:%M").strftime("%H:%M")
    except (ValueError, AttributeError):
        raise ValueError(f"Invalid time {value!r}; expected HH:MM in 24-hour format") from None


@dataclass
class Task:
    """A single pet-care activity (walk, feeding, medication, appointment...)."""

    description: str
    time: str  # "HH:MM", 24-hour clock
    duration_minutes: int = 15
    priority: str = "medium"  # low | medium | high
    frequency: str = "once"  # once | daily | weekly
    due_date: date = field(default_factory=date.today)
    completed: bool = False
    pet_name: str = ""  # filled in by Pet.add_task

    def __post_init__(self) -> None:
        """Validate fields and normalize the time string."""
        self.time = normalize_time(self.time)
        self.priority = self.priority.lower()
        self.frequency = self.frequency.lower()
        if self.priority not in VALID_PRIORITIES:
            raise ValueError(f"priority must be one of {VALID_PRIORITIES}")
        if self.frequency not in VALID_FREQUENCIES:
            raise ValueError(f"frequency must be one of {VALID_FREQUENCIES}")
        if self.duration_minutes <= 0:
            raise ValueError("duration_minutes must be positive")

    def mark_complete(self) -> None:
        """Mark this task as done."""
        self.completed = True

    def next_occurrence(self) -> "Task | None":
        """Return a fresh, incomplete copy due one step later (daily: +1 day, weekly: +7 days), or None for one-off tasks."""
        step = RECURRENCE_STEP.get(self.frequency)
        if step is None:
            return None
        return replace(self, due_date=self.due_date + step, completed=False)


@dataclass
class Pet:
    """A pet and the care tasks it needs."""

    name: str
    species: str
    age: int = 0
    tasks: list[Task] = field(default_factory=list)

    def __post_init__(self) -> None:
        """Reject blank pet names."""
        self.name = self.name.strip()
        if not self.name:
            raise ValueError("Pet name cannot be blank")

    def add_task(self, task: Task) -> None:
        """Attach a task to this pet and tag it with the pet's name."""
        task.pet_name = self.name
        self.tasks.append(task)

    def remove_task(self, task: Task) -> None:
        """Remove a task from this pet."""
        self.tasks.remove(task)


class Owner:
    """A pet owner who manages one or more pets."""

    def __init__(self, name: str):
        """Create an owner with no pets yet."""
        self.name = name
        self.pets: list[Pet] = []

    def add_pet(self, pet: Pet) -> None:
        """Add a pet; pet names must be unique for this owner."""
        if self.get_pet(pet.name) is not None:
            raise ValueError(f"{self.name} already has a pet named {pet.name!r}")
        self.pets.append(pet)

    def get_pet(self, name: str) -> Pet | None:
        """Return the pet with this name (case-insensitive), or None."""
        for pet in self.pets:
            if pet.name.lower() == name.lower():
                return pet
        return None

    def get_all_tasks(self) -> list[Task]:
        """Return every task across all of this owner's pets."""
        return [task for pet in self.pets for task in pet.tasks]


class Scheduler:
    """The 'brain' that retrieves and organizes tasks across all of an owner's pets."""

    def __init__(self, owner: Owner):
        """Create a scheduler that reads tasks from the given owner."""
        self.owner = owner

    def get_all_tasks(self) -> list[Task]:
        """Fetch all tasks from the owner's pets."""
        return self.owner.get_all_tasks()

    def sort_by_time(self, tasks: list[Task] | None = None) -> list[Task]:
        """Return tasks in chronological order (by due date, then "HH:MM" time).

        Times are normalized to zero-padded "HH:MM" when a Task is created, so plain
        string comparison sorts them correctly ("09:00" < "13:30").
        """
        tasks = self.get_all_tasks() if tasks is None else tasks
        return sorted(tasks, key=lambda t: (t.due_date, t.time))

    def filter_tasks(
        self,
        tasks: list[Task] | None = None,
        pet_name: str | None = None,
        completed: bool | None = None,
    ) -> list[Task]:
        """Return tasks matching a pet name and/or completion status; None means "don't filter on this"."""
        tasks = self.get_all_tasks() if tasks is None else tasks
        return [
            t for t in tasks
            if (pet_name is None or t.pet_name.lower() == pet_name.lower())
            and (completed is None or t.completed == completed)
        ]

    def get_todays_schedule(self, on_date: date | None = None) -> list[Task]:
        """Return the tasks due on a date (default today), in time order."""
        on_date = on_date or date.today()
        return self.sort_by_time([t for t in self.get_all_tasks() if t.due_date == on_date])

    def mark_task_complete(self, task: Task) -> Task | None:
        """Complete a task; for daily/weekly tasks, add and return the next occurrence on the same pet."""
        if task.completed:
            return None  # already done: don't spawn a duplicate follow-up
        task.mark_complete()
        follow_up = task.next_occurrence()
        if follow_up is not None:
            pet = self.owner.get_pet(task.pet_name)
            if pet is None:
                raise ValueError(f"Task {task.description!r} isn't attached to one of {self.owner.name}'s pets")
            pet.add_task(follow_up)
        return follow_up

    def detect_conflicts(self, tasks: list[Task] | None = None) -> list[str]:
        """Return a warning for each date + start time shared by two or more pending tasks.

        Lightweight by design: it only flags exact start-time matches (not overlapping
        durations) and never raises, so the caller can just display the warnings.
        """
        tasks = self.get_all_tasks() if tasks is None else tasks
        slots: dict[tuple[date, str], list[Task]] = defaultdict(list)
        for t in tasks:
            if not t.completed:
                slots[(t.due_date, t.time)].append(t)

        warnings = []
        for (day, time), clashing in sorted(slots.items()):
            if len(clashing) > 1:
                who = ", ".join(f"{t.pet_name}: {t.description}" for t in clashing)
                warnings.append(f"Conflict on {day.isoformat()} at {time} -> {who}")
        return warnings

    @staticmethod
    def format_schedule(tasks: list[Task], title: str = "Today's Schedule") -> str:
        """Render tasks as a readable, aligned text table for the terminal."""
        lines = [title, "=" * len(title)]
        if not tasks:
            lines.append("  (no tasks)")
        for t in tasks:
            status = "x" if t.completed else " "
            lines.append(
                f"  [{status}] {t.due_date:%a %m/%d} {t.time}  {t.pet_name:<8} {t.description:<22} "
                f"{t.duration_minutes:>3} min  {t.priority:<6}  {t.frequency}"
            )
        return "\n".join(lines)
