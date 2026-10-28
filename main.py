"""CLI demo for PawPal+ — verifies the backend logic before it is wired to Streamlit."""

from pawpal_system import Owner, Pet, Scheduler, Task


def main() -> None:
    owner = Owner("Jordan")
    mochi = Pet("Mochi", "dog", age=3)
    luna = Pet("Luna", "cat", age=5)
    owner.add_pet(mochi)
    owner.add_pet(luna)

    mochi.add_task(Task("Morning walk", "07:30", duration_minutes=30, priority="high", frequency="daily"))
    mochi.add_task(Task("Evening walk", "18:00", duration_minutes=30, priority="medium", frequency="daily"))
    luna.add_task(Task("Breakfast", "08:00", duration_minutes=10, priority="high", frequency="daily"))
    luna.add_task(Task("Flea medication", "12:00", duration_minutes=5, priority="high", frequency="weekly"))

    scheduler = Scheduler(owner)
    print(Scheduler.format_schedule(scheduler.get_todays_schedule()))


if __name__ == "__main__":
    main()
