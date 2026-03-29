"""
PawPal+ — Backend logic layer
Classes: Owner, Pet, Task, Scheduler, DailyPlan
"""

from dataclasses import dataclass, field
from datetime import date


@dataclass
class Task:
    """A single pet care activity."""
    title: str
    duration_minutes: int
    priority: str                  # "low", "medium", "high"
    task_type: str = "general"     # e.g. "walk", "feeding", "medication", "grooming"

    def describe(self) -> str:
        return f"{self.title} ({self.task_type}) — {self.duration_minutes} min, priority: {self.priority}"


@dataclass
class Pet:
    """Represents a pet belonging to an owner."""
    name: str
    species: str
    age: int
    _tasks: list = field(default_factory=list, repr=False)

    def add_task(self, task: Task) -> None:
        self._tasks.append(task)

    def get_tasks(self) -> list:
        return list(self._tasks)


@dataclass
class Owner:
    """Represents the pet owner and their daily time constraints."""
    name: str
    available_minutes_per_day: int
    _pets: list = field(default_factory=list, repr=False)

    def add_pet(self, pet: Pet) -> None:
        self._pets.append(pet)

    def get_pets(self) -> list:
        return list(self._pets)

    def get_available_time(self) -> int:
        return self.available_minutes_per_day


class DailyPlan:
    """The output of the Scheduler — an ordered list of tasks for a single day."""

    def __init__(self, scheduled_tasks: list[Task], plan_date: date, skipped_tasks: list[Task] = None):
        self.scheduled_tasks = scheduled_tasks
        self.date = plan_date
        self.skipped_tasks = skipped_tasks or []
        self.total_duration = sum(t.duration_minutes for t in scheduled_tasks)

    def display(self) -> None:
        print(f"\n--- Daily Plan for {self.date} ---")
        for i, task in enumerate(self.scheduled_tasks, 1):
            print(f"  {i}. {task.describe()}")
        print(f"Total time: {self.total_duration} min")
        if self.skipped_tasks:
            print("Skipped (not enough time):")
            for task in self.skipped_tasks:
                print(f"  - {task.describe()}")

    def get_summary(self) -> str:
        lines = [f"Plan for {self.date} — {self.total_duration} min scheduled:"]
        for i, task in enumerate(self.scheduled_tasks, 1):
            lines.append(f"  {i}. {task.describe()}")
        if self.skipped_tasks:
            lines.append("Skipped:")
            for task in self.skipped_tasks:
                lines.append(f"  - {task.describe()}")
        return "\n".join(lines)


# Priority ordering used by the scheduler
PRIORITY_ORDER = {"high": 0, "medium": 1, "low": 2}


class Scheduler:
    """Selects and orders tasks that fit within the owner's available time."""

    def __init__(self, owner: Owner, tasks: list[Task]):
        self.owner = owner
        self.tasks = tasks

    def generate_schedule(self, plan_date: date = None) -> DailyPlan:
        """
        Sort tasks by priority (high first), then greedily select tasks
        that fit within the owner's available time for the day.
        """
        if plan_date is None:
            plan_date = date.today()

        time_budget = self.owner.get_available_time()
        sorted_tasks = sorted(self.tasks, key=lambda t: PRIORITY_ORDER.get(t.priority, 99))

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

    def explain_plan(self, plan: DailyPlan) -> str:
        """Return a human-readable explanation of why each task was included or skipped."""
        lines = [
            f"{self.owner.name} has {self.owner.get_available_time()} minutes available today.",
            f"Tasks were sorted by priority (high → medium → low) and selected greedily.",
            "",
            "Included tasks:",
        ]
        for task in plan.scheduled_tasks:
            lines.append(f"  - {task.title}: {task.duration_minutes} min ({task.priority} priority)")

        if plan.skipped_tasks:
            lines.append("")
            lines.append("Skipped tasks (not enough time remaining):")
            for task in plan.skipped_tasks:
                lines.append(f"  - {task.title}: {task.duration_minutes} min ({task.priority} priority)")

        lines.append(f"\nTotal time scheduled: {plan.total_duration} / {self.owner.get_available_time()} min")
        return "\n".join(lines)
