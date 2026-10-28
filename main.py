"""CLI demo for PawPal+ — verifies the backend logic before it is wired to Streamlit."""

from pawpal_system import Owner, Pet, Scheduler, Task


def main() -> None:
    owner = Owner("Jordan")
    mochi = Pet("Mochi", "dog", age=3)
    luna = Pet("Luna", "cat", age=5)
    owner.add_pet(mochi)
    owner.add_pet(luna)

    # Tasks are added deliberately out of time order to prove the sorting works.
    mochi.add_task(Task("Evening walk", "18:00", duration_minutes=30, priority="medium", frequency="daily"))
    luna.add_task(Task("Flea medication", "12:00", duration_minutes=5, priority="high", frequency="weekly"))
    mochi.add_task(Task("Morning walk", "7:30", duration_minutes=30, priority="high", frequency="daily"))
    luna.add_task(Task("Breakfast", "08:00", duration_minutes=10, priority="high", frequency="daily"))
    mochi.add_task(Task("Vet appointment", "12:00", duration_minutes=45, priority="high"))  # clashes with flea meds

    scheduler = Scheduler(owner)

    print("Tasks in the order they were added:")
    for t in scheduler.get_all_tasks():
        print(f"  {t.time}  {t.pet_name}: {t.description}")
    print()

    print(Scheduler.format_schedule(scheduler.get_todays_schedule()))
    print()

    print("Conflict check:")
    for warning in scheduler.detect_conflicts() or ["  No conflicts."]:
        print(f"  WARNING: {warning}")
    print()

    print(Scheduler.format_schedule(
        scheduler.sort_by_time(scheduler.filter_tasks(pet_name="Mochi")), "Filter: Mochi only"))
    print()

    morning_walk = next(t for t in mochi.tasks if t.description == "Morning walk")
    next_walk = scheduler.mark_task_complete(morning_walk)
    print(f"Completed '{morning_walk.description}' -> next one auto-created for {next_walk.due_date} at {next_walk.time}")
    print()

    print(Scheduler.format_schedule(
        scheduler.sort_by_time(scheduler.filter_tasks(completed=False)), "Filter: still to do (all dates)"))
    print()
    print(Scheduler.format_schedule(scheduler.get_todays_schedule(), "Today's Schedule (after completing the walk)"))


if __name__ == "__main__":
    main()
