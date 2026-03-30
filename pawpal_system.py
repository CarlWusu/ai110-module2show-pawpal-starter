"""
PawPal+ — Backend logic layer
Classes: Task, Pet, Owner, Scheduler, DailyPlan
"""

from dataclasses import dataclass, field
from datetime import date, timedelta


VALID_PRIORITIES = {"low", "medium", "high"}
VALID_FREQUENCIES = {"daily", "weekly", "as-needed"}
PRIORITY_ORDER = {"high": 0, "medium": 1, "low": 2}


@dataclass
class Task:
    """A single pet care activity."""
    title: str
    duration_minutes: int
    priority: str                   # "low", "medium", "high"
    description: str = ""           # human-readable explanation of the task
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
            _parse_time(self.start_time)  # raises ValueError if malformed

    def mark_complete(self) -> None:
        """Mark this task as completed and advance next_due for recurring tasks."""
        self.is_complete = True
        today = date.today()
        if self.frequency == "daily":
            self.next_due = today + timedelta(days=1)
        elif self.frequency == "weekly":
            self.next_due = today + timedelta(weeks=1)
        # "as-needed" tasks get no automatic next_due

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
            f"{self.title} ({self.task_type}){time_str} — "
            f"{self.duration_minutes} min, priority: {self.priority}, "
            f"frequency: {self.frequency} [{status}]"
        )
        if self.description:
            base += f"\n    {self.description}"
        return base


def _parse_time(hhmm: str) -> int:
    """Convert 'HH:MM' string to total minutes since midnight; raise ValueError if malformed."""
    try:
        h, m = hhmm.split(":")
        return int(h) * 60 + int(m)
    except (ValueError, AttributeError):
        raise ValueError(f"start_time must be in 'HH:MM' format, got '{hhmm}'")


@dataclass
class Pet:
    """Represents a pet belonging to an owner."""
    name: str
    species: str
    age: int
    breed: str = ""
    notes: str = ""                 # any special care notes (e.g. allergies, mobility issues)
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


class Scheduler:
    """Retrieves, organizes, and manages tasks across all pets for an owner."""

    def __init__(self, owner: Owner):
        """Initialize the Scheduler with an Owner whose pets and tasks it will manage."""
        self.owner = owner

    # ------------------------------------------------------------------
    # Sorting
    # ------------------------------------------------------------------

    def sort_by_time(self, tasks: list) -> list:
        """Sort a task list by start_time (HH:MM); tasks without a time go last."""
        def sort_key(task: Task) -> int:
            if task.start_time:
                return _parse_time(task.start_time)
            return 9999  # no start_time → append to end

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
    # Scheduling
    # ------------------------------------------------------------------

    def _get_schedulable_tasks(self) -> list:
        """Return pending, due tasks sorted by priority (high → medium → low)."""
        today = date.today()
        pending = [
            t for t in self.owner.get_all_pending_tasks()
            if t.is_due(today)
        ]
        return sorted(pending, key=lambda t: PRIORITY_ORDER.get(t.priority, 99))

    def generate_schedule(self, plan_date: date = None) -> DailyPlan:
        """Sort due pending tasks by priority, greedily select those that fit the time budget."""
        if plan_date is None:
            plan_date = date.today()

        time_budget = self.owner.get_available_time()
        sorted_tasks = self._get_schedulable_tasks()

        scheduled = []
        skipped = []
        time_used = 0

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
                # Overlap when one window starts before the other ends
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
            lines.append("")
            lines.append("Skipped tasks (not enough time remaining):")
            for task in plan.skipped_tasks:
                lines.append(f"  - {task.title}: {task.duration_minutes} min ({task.priority} priority)")

        lines.append(f"\nTotal time scheduled: {plan.total_duration} / {self.owner.get_available_time()} min")
        return "\n".join(lines)
