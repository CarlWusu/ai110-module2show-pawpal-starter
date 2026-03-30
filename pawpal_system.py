"""
PawPal+ — Backend logic layer
Classes: Task, Pet, Owner, Scheduler, DailyPlan
"""

import json
from dataclasses import dataclass, field
from datetime import date, timedelta
from pathlib import Path


VALID_PRIORITIES = {"low", "medium", "high"}
VALID_FREQUENCIES = {"daily", "weekly", "as-needed"}
PRIORITY_ORDER = {"high": 0, "medium": 1, "low": 2}

# Challenge 1: weighted scoring weights
PRIORITY_WEIGHT  = {"high": 100, "medium": 60, "low": 20}
FREQUENCY_WEIGHT = {"daily": 30, "weekly": 10, "as-needed": 5}
EFFICIENCY_THRESHOLD = 15   # tasks ≤ this many minutes get a small efficiency bonus

# Challenge 4: task-type emojis for UI display
TASK_TYPE_EMOJI = {
    "walk":       "🦮",
    "feeding":    "🍽️",
    "medication": "💊",
    "grooming":   "✂️",
    "enrichment": "🧸",
    "general":    "📋",
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _parse_time(hhmm: str) -> int:
    """Convert 'HH:MM' string to total minutes since midnight; raise ValueError if malformed."""
    try:
        h, m = hhmm.split(":")
        return int(h) * 60 + int(m)
    except (ValueError, AttributeError):
        raise ValueError(f"start_time must be in 'HH:MM' format, got '{hhmm}'")


def task_emoji(task_type: str) -> str:
    """Return the display emoji for a task type."""
    return TASK_TYPE_EMOJI.get(task_type, "📋")


# ---------------------------------------------------------------------------
# Task
# ---------------------------------------------------------------------------

@dataclass
class Task:
    """A single pet care activity."""
    title: str
    duration_minutes: int
    priority: str                   # "low", "medium", "high"
    description: str = ""
    task_type: str = "general"      # "walk", "feeding", "medication", "grooming", etc.
    frequency: str = "daily"        # "daily", "weekly", "as-needed"
    start_time: str = ""            # optional scheduled start in "HH:MM" format
    is_complete: bool = False
    next_due: date = None           # set automatically when a recurring task is completed

    def __post_init__(self):
        """Validate priority, frequency, and start_time format after dataclass initialization."""
        if self.priority not in VALID_PRIORITIES:
            raise ValueError(f"priority must be one of {VALID_PRIORITIES}, got '{self.priority}'")
        if self.frequency not in VALID_FREQUENCIES:
            raise ValueError(f"frequency must be one of {VALID_FREQUENCIES}, got '{self.frequency}'")
        if self.start_time:
            _parse_time(self.start_time)

    def mark_complete(self) -> None:
        """Mark this task as completed and advance next_due for recurring tasks."""
        self.is_complete = True
        today = date.today()
        if self.frequency == "daily":
            self.next_due = today + timedelta(days=1)
        elif self.frequency == "weekly":
            self.next_due = today + timedelta(weeks=1)

    def reset(self) -> None:
        """Reset completion status (e.g. at the start of a new day)."""
        self.is_complete = False

    def is_due(self, on_date: date = None) -> bool:
        """Return True if this task is due on the given date (defaults to today)."""
        if on_date is None:
            on_date = date.today()
        if self.next_due is None:
            return True
        return self.next_due <= on_date

    def describe(self) -> str:
        """Return a formatted one-line summary of this task including status."""
        status = "done" if self.is_complete else "pending"
        time_str = f" @ {self.start_time}" if self.start_time else ""
        base = (
            f"{task_emoji(self.task_type)} {self.title} ({self.task_type}){time_str} — "
            f"{self.duration_minutes} min, priority: {self.priority}, "
            f"frequency: {self.frequency} [{status}]"
        )
        if self.description:
            base += f"\n    {self.description}"
        return base

    # Challenge 2: JSON serialisation
    def to_dict(self) -> dict:
        """Serialise this Task to a plain dictionary suitable for JSON export."""
        return {
            "title":            self.title,
            "duration_minutes": self.duration_minutes,
            "priority":         self.priority,
            "description":      self.description,
            "task_type":        self.task_type,
            "frequency":        self.frequency,
            "start_time":       self.start_time,
            "is_complete":      self.is_complete,
            "next_due":         self.next_due.isoformat() if self.next_due else None,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Task":
        """Reconstruct a Task from a plain dictionary (e.g. loaded from JSON)."""
        next_due_raw = data.get("next_due")
        next_due = date.fromisoformat(next_due_raw) if next_due_raw else None
        return cls(
            title=data["title"],
            duration_minutes=data["duration_minutes"],
            priority=data["priority"],
            description=data.get("description", ""),
            task_type=data.get("task_type", "general"),
            frequency=data.get("frequency", "daily"),
            start_time=data.get("start_time", ""),
            is_complete=data.get("is_complete", False),
            next_due=next_due,
        )


# ---------------------------------------------------------------------------
# Pet
# ---------------------------------------------------------------------------

@dataclass
class Pet:
    """Represents a pet belonging to an owner."""
    name: str
    species: str
    age: int
    breed: str = ""
    notes: str = ""
    _tasks: list = field(default_factory=list, repr=False)

    def add_task(self, task: Task) -> None:
        """Append a Task to this pet's task list."""
        self._tasks.append(task)

    def remove_task(self, title: str) -> bool:
        """Remove a task by title. Returns True if found and removed."""
        for i, task in enumerate(self._tasks):
            if task.title.lower() == title.lower():
                self._tasks.pop(i)
                return True
        return False

    def get_tasks(self) -> list:
        """Return a copy of all tasks assigned to this pet."""
        return list(self._tasks)

    def get_pending_tasks(self) -> list:
        """Return only tasks not yet marked complete."""
        return [t for t in self._tasks if not t.is_complete]

    def get_completed_tasks(self) -> list:
        """Return only tasks that have been marked complete."""
        return [t for t in self._tasks if t.is_complete]

    def reset_all_tasks(self) -> None:
        """Reset completion status on all tasks (call at start of each day)."""
        for task in self._tasks:
            task.reset()

    # Challenge 2: JSON serialisation
    def to_dict(self) -> dict:
        """Serialise this Pet and all its tasks to a plain dictionary."""
        return {
            "name":    self.name,
            "species": self.species,
            "age":     self.age,
            "breed":   self.breed,
            "notes":   self.notes,
            "tasks":   [t.to_dict() for t in self._tasks],
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Pet":
        """Reconstruct a Pet (including tasks) from a plain dictionary."""
        pet = cls(
            name=data["name"],
            species=data["species"],
            age=data["age"],
            breed=data.get("breed", ""),
            notes=data.get("notes", ""),
        )
        for task_data in data.get("tasks", []):
            pet.add_task(Task.from_dict(task_data))
        return pet


# ---------------------------------------------------------------------------
# Owner
# ---------------------------------------------------------------------------

@dataclass
class Owner:
    """Represents the pet owner and their daily time constraints."""
    name: str
    available_minutes_per_day: int
    _pets: list = field(default_factory=list, repr=False)

    def add_pet(self, pet: Pet) -> None:
        """Add a Pet to this owner's list of pets."""
        self._pets.append(pet)

    def remove_pet(self, name: str) -> bool:
        """Remove a pet by name. Returns True if found and removed."""
        for i, pet in enumerate(self._pets):
            if pet.name.lower() == name.lower():
                self._pets.pop(i)
                return True
        return False

    def get_pets(self) -> list:
        """Return a copy of all pets belonging to this owner."""
        return list(self._pets)

    def get_pet(self, name: str) -> "Pet | None":
        """Look up a single pet by name."""
        for pet in self._pets:
            if pet.name.lower() == name.lower():
                return pet
        return None

    def get_available_time(self) -> int:
        """Return the number of minutes the owner has available today."""
        return self.available_minutes_per_day

    def get_all_tasks(self) -> list:
        """Collect all tasks across all pets — bridges Owner → Pet → Task chain."""
        tasks = []
        for pet in self._pets:
            tasks.extend(pet.get_tasks())
        return tasks

    def get_all_pending_tasks(self) -> list:
        """Collect only incomplete tasks across all pets."""
        tasks = []
        for pet in self._pets:
            tasks.extend(pet.get_pending_tasks())
        return tasks

    def reset_day(self) -> None:
        """Reset all task completion statuses across all pets for a new day."""
        for pet in self._pets:
            pet.reset_all_tasks()

    # Challenge 2: JSON persistence
    def to_dict(self) -> dict:
        """Serialise this Owner and all owned pets/tasks to a plain dictionary."""
        return {
            "name":                     self.name,
            "available_minutes_per_day": self.available_minutes_per_day,
            "pets":                     [p.to_dict() for p in self._pets],
        }

    def save_to_json(self, path: str = "data.json") -> None:
        """Write the full owner/pet/task state to a JSON file at the given path."""
        Path(path).write_text(json.dumps(self.to_dict(), indent=2))

    @classmethod
    def from_dict(cls, data: dict) -> "Owner":
        """Reconstruct an Owner (including pets and tasks) from a plain dictionary."""
        owner = cls(
            name=data["name"],
            available_minutes_per_day=data["available_minutes_per_day"],
        )
        for pet_data in data.get("pets", []):
            owner.add_pet(Pet.from_dict(pet_data))
        return owner

    @classmethod
    def load_from_json(cls, path: str = "data.json") -> "Owner":
        """Load and reconstruct an Owner from a JSON file; raise FileNotFoundError if missing."""
        data = json.loads(Path(path).read_text())
        return cls.from_dict(data)


# ---------------------------------------------------------------------------
# DailyPlan
# ---------------------------------------------------------------------------

class DailyPlan:
    """The output of the Scheduler — an ordered list of tasks for a single day."""

    def __init__(self, scheduled_tasks: list, plan_date: date, skipped_tasks: list = None):
        self.scheduled_tasks = scheduled_tasks
        self.date = plan_date
        self.skipped_tasks = skipped_tasks or []
        self.total_duration = sum(t.duration_minutes for t in scheduled_tasks)

    def display(self) -> None:
        """Print the full daily plan including skipped tasks to stdout."""
        print(f"\n--- Daily Plan for {self.date} ---")
        for i, task in enumerate(self.scheduled_tasks, 1):
            print(f"  {i}. {task.describe()}")
        print(f"\nTotal time: {self.total_duration} min")
        if self.skipped_tasks:
            print("\nSkipped (not enough time):")
            for task in self.skipped_tasks:
                print(f"  - {task.describe()}")

    def get_summary(self) -> str:
        """Return the daily plan as a formatted multi-line string for display in the UI."""
        lines = [f"Plan for {self.date} — {self.total_duration} min scheduled:"]
        for i, task in enumerate(self.scheduled_tasks, 1):
            lines.append(f"  {i}. {task.describe()}")
        if self.skipped_tasks:
            lines.append("\nSkipped:")
            for task in self.skipped_tasks:
                lines.append(f"  - {task.describe()}")
        return "\n".join(lines)


# ---------------------------------------------------------------------------
# Scheduler
# ---------------------------------------------------------------------------

class Scheduler:
    """Retrieves, organizes, and manages tasks across all pets for an owner."""

    def __init__(self, owner: Owner):
        """Initialize the Scheduler with an Owner whose pets and tasks it will manage."""
        self.owner = owner

    # ------------------------------------------------------------------
    # Challenge 1: Weighted prioritization
    # ------------------------------------------------------------------

    def score_task(self, task: Task) -> float:
        """Compute a composite priority score for a task.

        Score = priority_weight + frequency_urgency + efficiency_bonus.
        Higher scores are scheduled first. This ranks tasks more nuancedly
        than a simple high/medium/low sort: a daily high-priority 10-min task
        scores above a weekly high-priority 60-min task.
        """
        p_score = PRIORITY_WEIGHT.get(task.priority, 0)
        f_score = FREQUENCY_WEIGHT.get(task.frequency, 0)
        efficiency_bonus = 10 if task.duration_minutes <= EFFICIENCY_THRESHOLD else 0
        return p_score + f_score + efficiency_bonus

    def generate_weighted_schedule(self, plan_date: date = None) -> DailyPlan:
        """Schedule tasks using composite scoring instead of pure priority ordering.

        Tasks are ranked by score (priority + frequency urgency + efficiency bonus),
        then selected greedily within the time budget. Daily high-priority short tasks
        rank above weekly high-priority long tasks, giving the owner quick wins first.
        """
        if plan_date is None:
            plan_date = date.today()

        today = date.today()
        pending = [t for t in self.owner.get_all_pending_tasks() if t.is_due(today)]
        ranked = sorted(pending, key=self.score_task, reverse=True)

        time_budget = self.owner.get_available_time()
        scheduled, skipped, time_used = [], [], 0

        for task in ranked:
            if time_used + task.duration_minutes <= time_budget:
                scheduled.append(task)
                time_used += task.duration_minutes
            else:
                skipped.append(task)

        return DailyPlan(scheduled_tasks=scheduled, plan_date=plan_date, skipped_tasks=skipped)

    def explain_weighted_plan(self, plan: DailyPlan) -> str:
        """Explain the weighted schedule, showing each task's composite score."""
        lines = [
            f"{self.owner.name} has {self.owner.get_available_time()} minutes available today.",
            "Tasks were ranked by composite score (priority + frequency urgency + efficiency bonus).",
            "",
            "Included tasks (score → title):",
        ]
        for task in plan.scheduled_tasks:
            score = self.score_task(task)
            lines.append(
                f"  [{score:3.0f}] {task_emoji(task.task_type)} {task.title} — "
                f"{task.duration_minutes} min ({task.priority}, {task.frequency})"
            )
        if plan.skipped_tasks:
            lines.append("\nSkipped (not enough time):")
            for task in plan.skipped_tasks:
                score = self.score_task(task)
                lines.append(f"  [{score:3.0f}] {task.title} — {task.duration_minutes} min")
        lines.append(f"\nTotal time scheduled: {plan.total_duration} / {self.owner.get_available_time()} min")
        return "\n".join(lines)

    # ------------------------------------------------------------------
    # Sorting
    # ------------------------------------------------------------------

    def sort_by_time(self, tasks: list) -> list:
        """Sort a task list by start_time (HH:MM); tasks without a time go last."""
        def sort_key(task: Task) -> int:
            return _parse_time(task.start_time) if task.start_time else 9999
        return sorted(tasks, key=sort_key)

    # ------------------------------------------------------------------
    # Filtering
    # ------------------------------------------------------------------

    def filter_tasks(self, pet_name: str = None, status: str = None) -> list:
        """Return tasks filtered by pet name and/or status ('pending' or 'complete').

        Both filters are optional and can be combined. If neither is given,
        all tasks across all pets are returned.
        """
        results = []
        for pet in self.owner.get_pets():
            if pet_name and pet.name.lower() != pet_name.lower():
                continue
            for task in pet.get_tasks():
                if status == "pending" and task.is_complete:
                    continue
                if status == "complete" and not task.is_complete:
                    continue
                results.append((pet.name, task))
        return results

    # ------------------------------------------------------------------
    # Scheduling (original priority-based)
    # ------------------------------------------------------------------

    def _get_schedulable_tasks(self) -> list:
        """Return pending, due tasks sorted by priority (high → medium → low)."""
        today = date.today()
        pending = [t for t in self.owner.get_all_pending_tasks() if t.is_due(today)]
        return sorted(pending, key=lambda t: PRIORITY_ORDER.get(t.priority, 99))

    def generate_schedule(self, plan_date: date = None) -> DailyPlan:
        """Sort due pending tasks by priority, greedily select those that fit the time budget."""
        if plan_date is None:
            plan_date = date.today()

        time_budget = self.owner.get_available_time()
        sorted_tasks = self._get_schedulable_tasks()
        scheduled, skipped, time_used = [], [], 0

        for task in sorted_tasks:
            if time_used + task.duration_minutes <= time_budget:
                scheduled.append(task)
                time_used += task.duration_minutes
            else:
                skipped.append(task)

        return DailyPlan(scheduled_tasks=scheduled, plan_date=plan_date, skipped_tasks=skipped)

    # ------------------------------------------------------------------
    # Completion
    # ------------------------------------------------------------------

    def mark_task_complete(self, title: str) -> bool:
        """Mark a task complete by title; advances next_due for recurring tasks. Returns True if found."""
        for task in self.owner.get_all_tasks():
            if task.title.lower() == title.lower():
                task.mark_complete()
                return True
        return False

    def get_completion_summary(self) -> str:
        """Return a progress summary of completed vs total tasks."""
        all_tasks = self.owner.get_all_tasks()
        done = [t for t in all_tasks if t.is_complete]
        lines = [
            f"Progress for {self.owner.name}:",
            f"  {len(done)} of {len(all_tasks)} tasks complete",
        ]
        if done:
            lines.append("  Completed:")
            for t in done:
                next_str = f" (next due: {t.next_due})" if t.next_due else ""
                lines.append(f"    - {t.title}{next_str}")
        remaining = [t for t in all_tasks if not t.is_complete]
        if remaining:
            lines.append("  Remaining:")
            for t in remaining:
                lines.append(f"    - {t.title} ({t.priority} priority)")
        return "\n".join(lines)

    # ------------------------------------------------------------------
    # Conflict detection
    # ------------------------------------------------------------------

    def detect_conflicts(self, tasks: list) -> list:
        """Check a list of tasks for time overlaps; return warning strings for each conflict found.

        Only tasks with a start_time set are evaluated. Two tasks conflict when
        their time windows [start, start + duration) overlap. Returns an empty
        list if no conflicts are found.
        """
        timed = [(t, _parse_time(t.start_time)) for t in tasks if t.start_time]
        warnings = []
        for i in range(len(timed)):
            for j in range(i + 1, len(timed)):
                task_a, start_a = timed[i]
                task_b, start_b = timed[j]
                end_a = start_a + task_a.duration_minutes
                end_b = start_b + task_b.duration_minutes
                if start_a < end_b and start_b < end_a:
                    warnings.append(
                        f"CONFLICT: '{task_a.title}' ({task_a.start_time}, "
                        f"{task_a.duration_minutes} min) overlaps with "
                        f"'{task_b.title}' ({task_b.start_time}, {task_b.duration_minutes} min)"
                    )
        return warnings

    # ------------------------------------------------------------------
    # Explanation
    # ------------------------------------------------------------------

    def explain_plan(self, plan: DailyPlan) -> str:
        """Return a human-readable explanation of why each task was included or skipped."""
        lines = [
            f"{self.owner.name} has {self.owner.get_available_time()} minutes available today.",
            "Tasks were sorted by priority (high → medium → low) and selected greedily.",
            "",
            "Included tasks:",
        ]
        for task in plan.scheduled_tasks:
            time_str = f" @ {task.start_time}" if task.start_time else ""
            lines.append(
                f"  - {task.title}{time_str}: {task.duration_minutes} min "
                f"({task.priority} priority, {task.frequency})"
            )
        if plan.skipped_tasks:
            lines.append("\nSkipped tasks (not enough time remaining):")
            for task in plan.skipped_tasks:
                lines.append(f"  - {task.title}: {task.duration_minutes} min ({task.priority} priority)")
        lines.append(f"\nTotal time scheduled: {plan.total_duration} / {self.owner.get_available_time()} min")
        return "\n".join(lines)
