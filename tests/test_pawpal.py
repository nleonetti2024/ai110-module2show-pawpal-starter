"""Automated tests for the PawPal+ logic layer."""

import os
import sys
from datetime import date

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pawpal_system import Owner, Pet, Scheduler, Task  # noqa: E402

DAY = date(2026, 3, 10)


@pytest.fixture
def household():
    """An owner with two pets and no tasks yet."""
    owner = Owner("Jordan")
    mochi, luna = Pet("Mochi", "dog"), Pet("Luna", "cat")
    owner.add_pet(mochi)
    owner.add_pet(luna)
    return owner, mochi, luna, Scheduler(owner)


# --- Basic behavior ------------------------------------------------------------

def test_mark_complete_changes_status():
    task = Task("Morning walk", "07:30")
    assert task.completed is False
    task.mark_complete()
    assert task.completed is True


def test_adding_task_increases_pet_task_count():
    pet = Pet("Mochi", "dog")
    assert len(pet.tasks) == 0
    pet.add_task(Task("Breakfast", "08:00"))
    assert len(pet.tasks) == 1
    assert pet.tasks[0].pet_name == "Mochi"


def test_owner_collects_tasks_from_all_pets(household):
    owner, mochi, luna, _ = household
    mochi.add_task(Task("Walk", "07:00"))
    luna.add_task(Task("Feed", "08:00"))
    assert {t.description for t in owner.get_all_tasks()} == {"Walk", "Feed"}


def test_duplicate_pet_name_rejected(household):
    owner, *_ = household
    with pytest.raises(ValueError):
        owner.add_pet(Pet("mochi", "dog"))


# --- Sorting -------------------------------------------------------------------

def test_sort_by_time_returns_chronological_order(household):
    _, mochi, luna, scheduler = household
    mochi.add_task(Task("Evening walk", "18:00", due_date=DAY))
    luna.add_task(Task("Lunch", "12:15", due_date=DAY))
    mochi.add_task(Task("Morning walk", "07:30", due_date=DAY))
    assert [t.time for t in scheduler.sort_by_time()] == ["07:30", "12:15", "18:00"]


def test_sort_handles_unpadded_hours():
    # Without normalization, the string "9:00" would sort AFTER "10:00".
    tasks = [Task("B", "10:00", due_date=DAY), Task("A", "9:00", due_date=DAY)]
    assert [t.description for t in Scheduler(Owner("x")).sort_by_time(tasks)] == ["A", "B"]


def test_sort_orders_by_date_before_time():
    later_day_early = Task("Tomorrow early", "06:00", due_date=date(2026, 3, 11))
    today_late = Task("Today late", "22:00", due_date=DAY)
    result = Scheduler(Owner("x")).sort_by_time([later_day_early, today_late])
    assert [t.description for t in result] == ["Today late", "Tomorrow early"]


def test_todays_schedule_only_includes_that_day(household):
    _, mochi, _, scheduler = household
    mochi.add_task(Task("Today", "09:00", due_date=DAY))
    mochi.add_task(Task("Tomorrow", "08:00", due_date=date(2026, 3, 11)))
    assert [t.description for t in scheduler.get_todays_schedule(DAY)] == ["Today"]


def test_pet_with_no_tasks_gives_empty_schedule(household):
    *_, scheduler = household
    assert scheduler.get_todays_schedule(DAY) == []
    assert scheduler.detect_conflicts() == []


# --- Filtering -----------------------------------------------------------------

def test_filter_by_pet_and_status(household):
    _, mochi, luna, scheduler = household
    walk = Task("Walk", "07:00", due_date=DAY)
    mochi.add_task(walk)
    mochi.add_task(Task("Brush", "19:00", due_date=DAY))
    luna.add_task(Task("Feed", "08:00", due_date=DAY))
    walk.mark_complete()

    assert len(scheduler.filter_tasks(pet_name="mochi")) == 2  # case-insensitive
    assert [t.description for t in scheduler.filter_tasks(completed=True)] == ["Walk"]
    assert [t.description for t in scheduler.filter_tasks(pet_name="Mochi", completed=False)] == ["Brush"]


# --- Recurring tasks -----------------------------------------------------------

def test_completing_daily_task_creates_next_day_task(household):
    _, mochi, _, scheduler = household
    walk = Task("Morning walk", "07:30", frequency="daily", due_date=DAY)
    mochi.add_task(walk)

    follow_up = scheduler.mark_task_complete(walk)

    assert walk.completed is True
    assert follow_up is not None
    assert follow_up.due_date == date(2026, 3, 11)
    assert follow_up.time == "07:30"
    assert follow_up.completed is False
    assert follow_up in mochi.tasks and len(mochi.tasks) == 2


def test_completing_weekly_task_creates_task_seven_days_later(household):
    _, _, luna, scheduler = household
    meds = Task("Flea meds", "12:00", frequency="weekly", due_date=DAY)
    luna.add_task(meds)
    assert scheduler.mark_task_complete(meds).due_date == date(2026, 3, 17)


def test_daily_recurrence_crosses_month_boundary(household):
    _, mochi, _, scheduler = household
    walk = Task("Walk", "07:00", frequency="daily", due_date=date(2026, 3, 31))
    mochi.add_task(walk)
    assert scheduler.mark_task_complete(walk).due_date == date(2026, 4, 1)


def test_one_off_task_does_not_recur(household):
    _, mochi, _, scheduler = household
    vet = Task("Vet visit", "15:00", frequency="once", due_date=DAY)
    mochi.add_task(vet)
    assert scheduler.mark_task_complete(vet) is None
    assert len(mochi.tasks) == 1


def test_completing_twice_does_not_duplicate_follow_up(household):
    _, mochi, _, scheduler = household
    walk = Task("Walk", "07:00", frequency="daily", due_date=DAY)
    mochi.add_task(walk)
    scheduler.mark_task_complete(walk)
    scheduler.mark_task_complete(walk)
    assert len(mochi.tasks) == 2


# --- Conflict detection --------------------------------------------------------

def test_conflict_detected_for_different_pets_same_time(household):
    _, mochi, luna, scheduler = household
    mochi.add_task(Task("Vet", "12:00", due_date=DAY))
    luna.add_task(Task("Flea meds", "12:00", due_date=DAY))
    warnings = scheduler.detect_conflicts()
    assert len(warnings) == 1
    assert "12:00" in warnings[0] and "Mochi: Vet" in warnings[0] and "Luna: Flea meds" in warnings[0]


def test_conflict_detected_for_same_pet_same_time(household):
    _, mochi, _, scheduler = household
    mochi.add_task(Task("Walk", "08:00", due_date=DAY))
    mochi.add_task(Task("Breakfast", "8:00", due_date=DAY))  # same slot once normalized
    assert len(scheduler.detect_conflicts()) == 1


def test_no_conflict_for_different_times_or_dates(household):
    _, mochi, luna, scheduler = household
    mochi.add_task(Task("Walk", "08:00", due_date=DAY))
    luna.add_task(Task("Feed", "08:01", due_date=DAY))
    luna.add_task(Task("Feed tomorrow", "08:00", due_date=date(2026, 3, 11)))
    assert scheduler.detect_conflicts() == []


def test_completed_tasks_do_not_count_as_conflicts(household):
    _, mochi, luna, scheduler = household
    walk = Task("Walk", "08:00", due_date=DAY)
    mochi.add_task(walk)
    luna.add_task(Task("Feed", "08:00", due_date=DAY))
    walk.mark_complete()
    assert scheduler.detect_conflicts() == []


# --- Input validation ----------------------------------------------------------

@pytest.mark.parametrize("bad_time", ["25:00", "12:60", "noon", ""])
def test_invalid_time_rejected(bad_time):
    with pytest.raises(ValueError):
        Task("Walk", bad_time)


def test_invalid_frequency_rejected():
    with pytest.raises(ValueError):
        Task("Walk", "08:00", frequency="monthly")
