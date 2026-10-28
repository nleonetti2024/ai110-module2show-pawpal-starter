"""PawPal+ logic layer: Owner, Pet, Task, and Scheduler classes."""

from dataclasses import dataclass, field
from datetime import date, datetime

VALID_PRIORITIES = ("low", "medium", "high")
VALID_FREQUENCIES = ("once", "daily", "weekly")


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


@dataclass
class Pet:
    """A pet and the care tasks it needs."""

    name: str
    species: str
    age: int = 0
    tasks: list[Task] = field(default_factory=list)

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
        """Return tasks ordered by time of day."""
        tasks = self.get_all_tasks() if tasks is None else tasks
        return sorted(tasks, key=lambda t: t.time)

    def get_todays_schedule(self, on_date: date | None = None) -> list[Task]:
        """Return the tasks due on a date (default today), in time order."""
        on_date = on_date or date.today()
        return self.sort_by_time([t for t in self.get_all_tasks() if t.due_date == on_date])

    @staticmethod
    def format_schedule(tasks: list[Task], title: str = "Today's Schedule") -> str:
        """Render tasks as a readable, aligned text table for the terminal."""
        lines = [title, "=" * len(title)]
        if not tasks:
            lines.append("  (no tasks)")
        for t in tasks:
            status = "x" if t.completed else " "
            lines.append(
                f"  [{status}] {t.time}  {t.pet_name:<8} {t.description:<22} "
                f"{t.duration_minutes:>3} min  {t.priority:<6}  {t.frequency}"
            )
        return "\n".join(lines)
