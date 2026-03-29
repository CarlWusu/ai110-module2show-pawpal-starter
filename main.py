"""
main.py — Manual testing ground for PawPal+ logic.
Run: python main.py
"""

from pawpal_system import Task, Pet, Owner, Scheduler


# --- Setup ---
owner = Owner(name="Jordan", available_minutes_per_day=90)

# Pet 1: Mochi the dog
mochi = Pet(name="Mochi", species="dog", age=3, breed="Shiba Inu")
mochi.add_task(Task(
    title="Morning walk",
    duration_minutes=30,
    priority="high",
    task_type="walk",
    frequency="daily",
    description="30-minute walk around the block before breakfast.",
))
mochi.add_task(Task(
    title="Breakfast feeding",
    duration_minutes=5,
    priority="high",
    task_type="feeding",
    frequency="daily",
    description="1 cup dry kibble with joint supplement.",
))
mochi.add_task(Task(
    title="Brush coat",
    duration_minutes=15,
    priority="low",
    task_type="grooming",
    frequency="weekly",
    description="Brush out loose fur to reduce shedding.",
))

# Pet 2: Luna the cat
luna = Pet(name="Luna", species="cat", age=5, notes="Indoor only, shy around strangers.")
luna.add_task(Task(
    title="Morning feeding",
    duration_minutes=5,
    priority="high",
    task_type="feeding",
    frequency="daily",
    description="Half can wet food in the morning.",
))
luna.add_task(Task(
    title="Playtime",
    duration_minutes=20,
    priority="medium",
    task_type="enrichment",
    frequency="daily",
    description="Interactive wand toy to keep Luna active.",
))
luna.add_task(Task(
    title="Flea medication",
    duration_minutes=5,
    priority="high",
    task_type="medication",
    frequency="weekly",
    description="Apply topical flea treatment between shoulder blades.",
))

owner.add_pet(mochi)
owner.add_pet(luna)

# --- Schedule ---
scheduler = Scheduler(owner=owner)
plan = scheduler.generate_schedule()

print("=" * 50)
print("         PAWPAL+ — TODAY'S SCHEDULE")
print("=" * 50)
print(plan.get_summary())
print()
print("--- Reasoning ---")
print(scheduler.explain_plan(plan))
print()
print("--- Completion Tracker ---")
print(scheduler.get_completion_summary())
