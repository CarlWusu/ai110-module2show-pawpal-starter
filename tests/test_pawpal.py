"""
Tests for PawPal+ core logic.
Run: python -m pytest
"""

import pytest
from pawpal_system import Task, Pet, Owner, Scheduler


# --- Fixtures ---

def make_task(**kwargs):
    defaults = dict(title="Test task", duration_minutes=10, priority="medium")
    defaults.update(kwargs)
    return Task(**defaults)


def make_pet(**kwargs):
    defaults = dict(name="Buddy", species="dog", age=2)
    defaults.update(kwargs)
    return Pet(**defaults)


# --- Task tests ---

def test_mark_complete_changes_status():
    task = make_task(title="Morning walk", priority="high")
    assert task.is_complete is False
    task.mark_complete()
    assert task.is_complete is True


def test_reset_clears_completion():
    task = make_task()
    task.mark_complete()
    task.reset()
    assert task.is_complete is False


# --- Pet tests ---

def test_add_task_increases_count():
    pet = make_pet()
    assert len(pet.get_tasks()) == 0
    pet.add_task(make_task(title="Feeding"))
    pet.add_task(make_task(title="Grooming", priority="low"))
    assert len(pet.get_tasks()) == 2


def test_remove_task_decreases_count():
    pet = make_pet()
    pet.add_task(make_task(title="Feeding"))
    assert len(pet.get_tasks()) == 1
    removed = pet.remove_task("Feeding")
    assert removed is True
    assert len(pet.get_tasks()) == 0


def test_remove_nonexistent_task_returns_false():
    pet = make_pet()
    assert pet.remove_task("Does not exist") is False


def test_get_pending_tasks_excludes_completed():
    pet = make_pet()
    t1 = make_task(title="Walk")
    t2 = make_task(title="Feed")
    t1.mark_complete()
    pet.add_task(t1)
    pet.add_task(t2)
    assert len(pet.get_pending_tasks()) == 1
    assert pet.get_pending_tasks()[0].title == "Feed"


# --- Scheduler tests ---

def test_schedule_respects_time_budget():
    owner = Owner(name="Jordan", available_minutes_per_day=30)
    pet = make_pet()
    pet.add_task(make_task(title="Long task", duration_minutes=25, priority="high"))
    pet.add_task(make_task(title="Short task", duration_minutes=10, priority="medium"))
    owner.add_pet(pet)
    plan = Scheduler(owner).generate_schedule()
    assert plan.total_duration <= 30


def test_high_priority_scheduled_before_low():
    owner = Owner(name="Jordan", available_minutes_per_day=60)
    pet = make_pet()
    pet.add_task(make_task(title="Low task", duration_minutes=10, priority="low"))
    pet.add_task(make_task(title="High task", duration_minutes=10, priority="high"))
    owner.add_pet(pet)
    plan = Scheduler(owner).generate_schedule()
    titles = [t.title for t in plan.scheduled_tasks]
    assert titles.index("High task") < titles.index("Low task")


def test_tasks_that_dont_fit_are_skipped():
    owner = Owner(name="Jordan", available_minutes_per_day=10)
    pet = make_pet()
    pet.add_task(make_task(title="Quick task", duration_minutes=5, priority="high"))
    pet.add_task(make_task(title="Long task", duration_minutes=60, priority="medium"))
    owner.add_pet(pet)
    plan = Scheduler(owner).generate_schedule()
    assert any(t.title == "Quick task" for t in plan.scheduled_tasks)
    assert any(t.title == "Long task" for t in plan.skipped_tasks)


# --- Validation tests ---

def test_invalid_priority_raises():
    with pytest.raises(ValueError):
        Task(title="Bad task", duration_minutes=10, priority="urgent")


def test_invalid_frequency_raises():
    with pytest.raises(ValueError):
        Task(title="Bad task", duration_minutes=10, priority="low", frequency="monthly")
