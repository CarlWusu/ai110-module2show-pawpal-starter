"""
main.py — Manual testing ground for PawPal+ logic.
Run: python3 main.py
"""

from pawpal_system import Task, Pet, Owner, Scheduler


# ---------------------------------------------------------------------------
# Setup
# ---------------------------------------------------------------------------
owner = Owner(name="Jordan", available_minutes_per_day=90)

mochi = Pet(name="Mochi", species="dog", age=3, breed="Shiba Inu")
mochi.add_task(Task(
    title="Morning walk",
    duration_minutes=30,
    priority="high",
    task_type="walk",
    frequency="daily",
    start_time="07:00",
    description="30-minute walk around the block before breakfast.",
))
mochi.add_task(Task(
    title="Breakfast feeding",
    duration_minutes=5,
    priority="high",
    task_type="feeding",
    frequency="daily",
    start_time="07:35",
    description="1 cup dry kibble with joint supplement.",
))
mochi.add_task(Task(
    title="Brush coat",
    duration_minutes=15,
    priority="low",
    task_type="grooming",
    frequency="weekly",
    start_time="18:00",
    description="Brush out loose fur to reduce shedding.",
))
# Added out-of-order to demonstrate sorting
mochi.add_task(Task(
    title="Evening walk",
    duration_minutes=20,
    priority="medium",
    task_type="walk",
    frequency="daily",
    start_time="17:30",
    description="Short evening stroll.",
))

luna = Pet(name="Luna", species="cat", age=5, notes="Indoor only.")
luna.add_task(Task(
    title="Morning feeding",
    duration_minutes=5,
    priority="high",
    task_type="feeding",
    frequency="daily",
    start_time="07:10",
    description="Half can wet food in the morning.",
))
luna.add_task(Task(
    title="Playtime",
    duration_minutes=20,
    priority="medium",
    task_type="enrichment",
    frequency="daily",
    start_time="19:00",
    description="Interactive wand toy to keep Luna active.",
))
luna.add_task(Task(
    title="Flea medication",
    duration_minutes=5,
    priority="high",
    task_type="medication",
    frequency="weekly",
    start_time="08:00",
    description="Apply topical flea treatment between shoulder blades.",
))
# Intentional conflict: overlaps with "Morning walk" (07:00–07:30)
luna.add_task(Task(
    title="Vet call",
    duration_minutes=15,
    priority="medium",
    task_type="general",
    frequency="as-needed",
    start_time="07:20",
    description="Quick phone check-in with the vet.",
))

owner.add_pet(mochi)
owner.add_pet(luna)

scheduler = Scheduler(owner=owner)

# ---------------------------------------------------------------------------
# 1. Basic schedule
# ---------------------------------------------------------------------------
print("=" * 55)
print("         PAWPAL+ — TODAY'S SCHEDULE")
print("=" * 55)
plan = scheduler.generate_schedule()
print(plan.get_summary())
print()
print("--- Reasoning ---")
print(scheduler.explain_plan(plan))

# ---------------------------------------------------------------------------
# 2. Sort by time
# ---------------------------------------------------------------------------
print()
print("=" * 55)
print("         ALL TASKS SORTED BY START TIME")
print("=" * 55)
all_tasks = owner.get_all_tasks()
sorted_tasks = scheduler.sort_by_time(all_tasks)
for task in sorted_tasks:
    time_str = task.start_time if task.start_time else "no time"
    print(f"  {time_str}  {task.title} ({task.duration_minutes} min, {task.priority})")

# ---------------------------------------------------------------------------
# 3. Filter tasks
# ---------------------------------------------------------------------------
print()
print("=" * 55)
print("         FILTER: MOCHI'S TASKS ONLY")
print("=" * 55)
mochi_tasks = scheduler.filter_tasks(pet_name="Mochi")
for pet_name, task in mochi_tasks:
    print(f"  [{pet_name}] {task.title} — {task.priority} priority")

print()
print("--- Filter: pending tasks across all pets ---")
pending = scheduler.filter_tasks(status="pending")
for pet_name, task in pending:
    print(f"  [{pet_name}] {task.title}")

# ---------------------------------------------------------------------------
# 4. Recurring tasks — mark complete and check next_due
# ---------------------------------------------------------------------------
print()
print("=" * 55)
print("         RECURRING TASK DEMO")
print("=" * 55)
scheduler.mark_task_complete("Morning walk")
scheduler.mark_task_complete("Morning feeding")  # Luna's

print("After marking 'Morning walk' and 'Morning feeding' complete:")
print(scheduler.get_completion_summary())

# Show next_due was set automatically
for task in owner.get_all_tasks():
    if task.is_complete and task.next_due:
        print(f"  → '{task.title}' next due: {task.next_due}")

# ---------------------------------------------------------------------------
# 5. Conflict detection
# ---------------------------------------------------------------------------
print()
print("=" * 55)
print("         CONFLICT DETECTION")
print("=" * 55)
conflicts = scheduler.detect_conflicts(owner.get_all_tasks())
if conflicts:
    for warning in conflicts:
        print(f"  ⚠  {warning}")
else:
    print("  No conflicts detected.")
