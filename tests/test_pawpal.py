"""
Tests for PawPal+ core logic.
Run: python -m pytest
"""

import pytest
from datetime import date, timedelta
from pawpal_system import Task, Pet, Owner, Scheduler


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

def make_task(**kwargs):
    defaults = dict(title="Test task", duration_minutes=10, priority="medium")
    defaults.update(kwargs)
    return Task(**defaults)


def make_pet(**kwargs):
    defaults = dict(name="Buddy", species="dog", age=2)
    defaults.update(kwargs)
    return Pet(**defaults)


def make_scheduler(minutes=120):
    owner = Owner(name="Jordan", available_minutes_per_day=minutes)
    return owner, Scheduler(owner)


# ---------------------------------------------------------------------------
# Task — completion
# ---------------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# Task — recurring / next_due
# ---------------------------------------------------------------------------

def test_daily_task_sets_next_due_tomorrow():
    task = make_task(frequency="daily")
    task.mark_complete()
    assert task.next_due == date.today() + timedelta(days=1)


def test_weekly_task_sets_next_due_in_seven_days():
    task = make_task(frequency="weekly")
    task.mark_complete()
    assert task.next_due == date.today() + timedelta(weeks=1)


def test_as_needed_task_has_no_next_due():
    task = make_task(frequency="as-needed")
    task.mark_complete()
    assert task.next_due is None


def test_task_not_due_if_next_due_is_future():
    task = make_task(frequency="daily")
    task.mark_complete()  # sets next_due = tomorrow
    assert task.is_due(date.today()) is False


def test_task_is_due_when_next_due_is_today():
    task = make_task(frequency="daily")
    task.next_due = date.today()
    assert task.is_due(date.today()) is True


# ---------------------------------------------------------------------------
# Task — validation
# ---------------------------------------------------------------------------

def test_invalid_priority_raises():
    with pytest.raises(ValueError):
        Task(title="Bad task", duration_minutes=10, priority="urgent")


def test_invalid_frequency_raises():
    with pytest.raises(ValueError):
        Task(title="Bad task", duration_minutes=10, priority="low", frequency="monthly")


def test_invalid_start_time_raises():
    with pytest.raises(ValueError):
        Task(title="Bad task", duration_minutes=10, priority="low", start_time="7am")


# ---------------------------------------------------------------------------
# Pet
# ---------------------------------------------------------------------------

def test_add_task_increases_count():
    pet = make_pet()
    assert len(pet.get_tasks()) == 0
    pet.add_task(make_task(title="Feeding"))
    pet.add_task(make_task(title="Grooming", priority="low"))
    assert len(pet.get_tasks()) == 2


def test_remove_task_decreases_count():
    pet = make_pet()
    pet.add_task(make_task(title="Feeding"))
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


# ---------------------------------------------------------------------------
# Scheduler — scheduling
# ---------------------------------------------------------------------------

def test_schedule_respects_time_budget():
    owner, scheduler = make_scheduler(minutes=30)
    pet = make_pet()
    pet.add_task(make_task(title="Long task", duration_minutes=25, priority="high"))
    pet.add_task(make_task(title="Short task", duration_minutes=10, priority="medium"))
    owner.add_pet(pet)
    plan = scheduler.generate_schedule()
    assert plan.total_duration <= 30


def test_high_priority_scheduled_before_low():
    owner, scheduler = make_scheduler(minutes=60)
    pet = make_pet()
    pet.add_task(make_task(title="Low task", duration_minutes=10, priority="low"))
    pet.add_task(make_task(title="High task", duration_minutes=10, priority="high"))
    owner.add_pet(pet)
    plan = scheduler.generate_schedule()
    titles = [t.title for t in plan.scheduled_tasks]
    assert titles.index("High task") < titles.index("Low task")


def test_tasks_that_dont_fit_are_skipped():
    owner, scheduler = make_scheduler(minutes=10)
    pet = make_pet()
    pet.add_task(make_task(title="Quick task", duration_minutes=5, priority="high"))
    pet.add_task(make_task(title="Long task", duration_minutes=60, priority="medium"))
    owner.add_pet(pet)
    plan = scheduler.generate_schedule()
    assert any(t.title == "Quick task" for t in plan.scheduled_tasks)
    assert any(t.title == "Long task" for t in plan.skipped_tasks)


def test_completed_recurring_task_excluded_from_next_schedule():
    owner, scheduler = make_scheduler(minutes=60)
    pet = make_pet()
    task = make_task(title="Daily walk", frequency="daily")
    pet.add_task(task)
    owner.add_pet(pet)
    scheduler.mark_task_complete("Daily walk")
    # next_due is tomorrow — should not appear in today's schedule
    plan = scheduler.generate_schedule()
    assert all(t.title != "Daily walk" for t in plan.scheduled_tasks)


# ---------------------------------------------------------------------------
# Scheduler — sorting
# ---------------------------------------------------------------------------

def test_sort_by_time_orders_correctly():
    owner, scheduler = make_scheduler()
    tasks = [
        make_task(title="Evening", start_time="19:00"),
        make_task(title="Morning", start_time="07:00"),
        make_task(title="Noon", start_time="12:00"),
    ]
    result = scheduler.sort_by_time(tasks)
    assert [t.title for t in result] == ["Morning", "Noon", "Evening"]


def test_sort_by_time_puts_no_time_last():
    owner, scheduler = make_scheduler()
    tasks = [
        make_task(title="No time"),
        make_task(title="Early", start_time="06:00"),
    ]
    result = scheduler.sort_by_time(tasks)
    assert result[0].title == "Early"
    assert result[-1].title == "No time"


# ---------------------------------------------------------------------------
# Scheduler — filtering
# ---------------------------------------------------------------------------

def test_filter_by_pet_name():
    owner, scheduler = make_scheduler()
    dog = Pet(name="Rex", species="dog", age=2)
    cat = Pet(name="Whiskers", species="cat", age=3)
    dog.add_task(make_task(title="Walk"))
    cat.add_task(make_task(title="Feed"))
    owner.add_pet(dog)
    owner.add_pet(cat)
    results = scheduler.filter_tasks(pet_name="Rex")
    assert all(pet == "Rex" for pet, _ in results)
    assert len(results) == 1


def test_filter_by_status_pending():
    owner, scheduler = make_scheduler()
    pet = make_pet()
    t1 = make_task(title="Done task")
    t2 = make_task(title="Pending task")
    t1.mark_complete()
    pet.add_task(t1)
    pet.add_task(t2)
    owner.add_pet(pet)
    results = scheduler.filter_tasks(status="pending")
    titles = [t.title for _, t in results]
    assert "Pending task" in titles
    assert "Done task" not in titles


# ---------------------------------------------------------------------------
# Scheduler — conflict detection
# ---------------------------------------------------------------------------

def test_detect_overlapping_tasks():
    owner, scheduler = make_scheduler()
    tasks = [
        make_task(title="Task A", start_time="08:00", duration_minutes=30),
        make_task(title="Task B", start_time="08:20", duration_minutes=20),
    ]
    warnings = scheduler.detect_conflicts(tasks)
    assert len(warnings) == 1
    assert "Task A" in warnings[0]
    assert "Task B" in warnings[0]


def test_no_conflict_for_sequential_tasks():
    owner, scheduler = make_scheduler()
    tasks = [
        make_task(title="Task A", start_time="08:00", duration_minutes=30),
        make_task(title="Task B", start_time="08:30", duration_minutes=20),
    ]
    assert scheduler.detect_conflicts(tasks) == []


def test_tasks_without_start_time_not_flagged():
    owner, scheduler = make_scheduler()
    tasks = [
        make_task(title="Task A"),  # no start_time
        make_task(title="Task B"),  # no start_time
    ]
    assert scheduler.detect_conflicts(tasks) == []


def test_exact_same_start_time_is_a_conflict():
    """Two tasks at identical start times must be flagged."""
    owner, scheduler = make_scheduler()
    tasks = [
        make_task(title="Task A", start_time="09:00", duration_minutes=20),
        make_task(title="Task B", start_time="09:00", duration_minutes=15),
    ]
    warnings = scheduler.detect_conflicts(tasks)
    assert len(warnings) == 1


# ---------------------------------------------------------------------------
# Edge cases
# ---------------------------------------------------------------------------

def test_schedule_with_no_tasks_produces_empty_plan():
    """A pet with no tasks should yield an empty schedule, not an error."""
    owner, scheduler = make_scheduler(minutes=60)
    owner.add_pet(make_pet(name="Empty"))
    plan = scheduler.generate_schedule()
    assert plan.scheduled_tasks == []
    assert plan.skipped_tasks == []
    assert plan.total_duration == 0


def test_schedule_with_zero_budget_skips_all_tasks():
    """If the owner has no time, every task should land in skipped."""
    owner, scheduler = make_scheduler(minutes=0)
    pet = make_pet()
    pet.add_task(make_task(title="Any task", duration_minutes=5, priority="high"))
    owner.add_pet(pet)
    plan = scheduler.generate_schedule()
    assert plan.scheduled_tasks == []
    assert len(plan.skipped_tasks) == 1


def test_filter_returns_empty_for_unknown_pet():
    """Filtering by a pet name that doesn't exist should return an empty list."""
    owner, scheduler = make_scheduler()
    owner.add_pet(make_pet(name="Rex"))
    results = scheduler.filter_tasks(pet_name="Nonexistent")
    assert results == []


def test_sort_empty_list_returns_empty():
    """Sorting an empty task list should not raise and should return empty."""
    _, scheduler = make_scheduler()
    assert scheduler.sort_by_time([]) == []


def test_detect_conflicts_single_task_no_conflict():
    """A single timed task cannot conflict with anything."""
    _, scheduler = make_scheduler()
    tasks = [make_task(title="Solo", start_time="10:00", duration_minutes=30)]
    assert scheduler.detect_conflicts(tasks) == []


# ---------------------------------------------------------------------------
# Challenge 1: Weighted scoring
# ---------------------------------------------------------------------------

def test_score_task_high_daily_scores_above_low_weekly():
    _, scheduler = make_scheduler()
    high_daily  = make_task(priority="high", frequency="daily")
    low_weekly  = make_task(priority="low",  frequency="weekly")
    assert scheduler.score_task(high_daily) > scheduler.score_task(low_weekly)


def test_score_task_efficiency_bonus_for_short_tasks():
    _, scheduler = make_scheduler()
    short = make_task(priority="medium", frequency="daily", duration_minutes=10)
    long  = make_task(priority="medium", frequency="daily", duration_minutes=60)
    assert scheduler.score_task(short) > scheduler.score_task(long)


def test_weighted_schedule_respects_time_budget():
    owner, scheduler = make_scheduler(minutes=30)
    pet = make_pet()
    pet.add_task(make_task(title="A", duration_minutes=20, priority="high",   frequency="daily"))
    pet.add_task(make_task(title="B", duration_minutes=20, priority="medium", frequency="daily"))
    owner.add_pet(pet)
    plan = scheduler.generate_weighted_schedule()
    assert plan.total_duration <= 30


def test_weighted_schedule_prefers_daily_over_weekly_same_priority():
    """A daily medium task should outscore a weekly medium task."""
    owner, scheduler = make_scheduler(minutes=60)
    pet = make_pet()
    daily  = make_task(title="Daily",  priority="medium", frequency="daily",  duration_minutes=10)
    weekly = make_task(title="Weekly", priority="medium", frequency="weekly", duration_minutes=10)
    pet.add_task(weekly)
    pet.add_task(daily)
    owner.add_pet(pet)
    plan = scheduler.generate_weighted_schedule()
    titles = [t.title for t in plan.scheduled_tasks]
    assert titles.index("Daily") < titles.index("Weekly")


# ---------------------------------------------------------------------------
# Challenge 2: JSON persistence
# ---------------------------------------------------------------------------

import json, tempfile, os
from datetime import date


def test_task_round_trips_through_dict():
    t = make_task(title="Walk", priority="high", frequency="daily", start_time="07:00")
    t.mark_complete()
    restored = Task.from_dict(t.to_dict())
    assert restored.title        == t.title
    assert restored.is_complete  == t.is_complete
    assert restored.next_due     == t.next_due


def test_pet_round_trips_through_dict():
    pet = make_pet(name="Rex")
    pet.add_task(make_task(title="Feed", priority="high"))
    restored = Pet.from_dict(pet.to_dict())
    assert restored.name == "Rex"
    assert len(restored.get_tasks()) == 1
    assert restored.get_tasks()[0].title == "Feed"


def test_owner_saves_and_loads_from_json():
    owner = Owner(name="Sam", available_minutes_per_day=60)
    pet   = make_pet(name="Buddy")
    pet.add_task(make_task(title="Walk", priority="high", frequency="daily"))
    owner.add_pet(pet)

    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
        path = f.name
    try:
        owner.save_to_json(path)
        loaded = Owner.load_from_json(path)
        assert loaded.name == "Sam"
        assert loaded.available_minutes_per_day == 60
        assert len(loaded.get_pets()) == 1
        assert loaded.get_pets()[0].name == "Buddy"
        assert len(loaded.get_all_tasks()) == 1
        assert loaded.get_all_tasks()[0].title == "Walk"
    finally:
        os.unlink(path)


def test_load_from_missing_file_raises():
    with pytest.raises(FileNotFoundError):
        Owner.load_from_json("/tmp/does_not_exist_pawpal.json")
