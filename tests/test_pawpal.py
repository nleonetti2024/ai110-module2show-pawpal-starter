"""Automated tests for the PawPal+ logic layer."""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pawpal_system import Pet, Task  # noqa: E402


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
