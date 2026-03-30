import streamlit as st
from pathlib import Path
from pawpal_system import Owner, Pet, Task, Scheduler, task_emoji

DATA_FILE = "data.json"

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")
st.title("🐾 PawPal+")
st.caption("Your daily pet care planner — prioritised, sorted, and conflict-checked.")

# ---------------------------------------------------------------------------
# Challenge 2: Data persistence — load from JSON on startup
# ---------------------------------------------------------------------------
if "owner" not in st.session_state:
    if Path(DATA_FILE).exists():
        try:
            st.session_state.owner = Owner.load_from_json(DATA_FILE)
        except Exception:
            st.session_state.owner = None
    else:
        st.session_state.owner = None


def autosave():
    """Save owner state to data.json if an owner exists."""
    if st.session_state.owner:
        st.session_state.owner.save_to_json(DATA_FILE)


# ---------------------------------------------------------------------------
# Section 1 — Owner & Pet Setup
# ---------------------------------------------------------------------------
st.header("1. Who's using PawPal+?")

with st.form("setup_form"):
    owner_name    = st.text_input("Your name", value="Jordan")
    available_time = st.number_input(
        "How many minutes do you have available today?",
        min_value=0, max_value=480, value=90, step=5,
    )
    pet_name = st.text_input("Pet name", value="Mochi")
    species  = st.selectbox("Species", ["dog", "cat", "rabbit", "bird", "other"])
    age      = st.number_input("Pet age (years)", min_value=0, max_value=30, value=3)
    breed    = st.text_input("Breed (optional)", value="")
    submitted = st.form_submit_button("Save owner & pet")

if submitted:
    owner = Owner(name=owner_name, available_minutes_per_day=int(available_time))
    pet   = Pet(name=pet_name, species=species, age=int(age), breed=breed)
    owner.add_pet(pet)
    st.session_state.owner = owner
    st.session_state.pop("plan", None)
    st.session_state.pop("scheduler", None)
    autosave()
    st.success(f"Saved! Welcome, {owner_name}. {pet_name} is ready.")

if st.session_state.owner is None:
    st.info("Fill in the form above to get started.")
    st.stop()

owner: Owner = st.session_state.owner

# Persistent data indicator
if Path(DATA_FILE).exists():
    st.caption(f"💾 Data loaded from `{DATA_FILE}` — your pets and tasks are saved between runs.")

# ---------------------------------------------------------------------------
# Section 2 — Manage Pets
# ---------------------------------------------------------------------------
st.divider()
st.header("2. Manage pets")

pets = owner.get_pets()
if pets:
    st.write("**Current pets:** " + ", ".join(
        f"{task_emoji('walk') if p.species == 'dog' else '🐱' if p.species == 'cat' else '🐾'} "
        f"{p.name} ({p.species}, {p.age}yr)" for p in pets
    ))

with st.expander("Add another pet"):
    with st.form("add_pet_form"):
        new_pet_name = st.text_input("Pet name")
        new_species  = st.selectbox("Species", ["dog", "cat", "rabbit", "bird", "other"], key="new_species")
        new_age      = st.number_input("Age (years)", min_value=0, max_value=30, value=1, key="new_age")
        new_breed    = st.text_input("Breed (optional)", key="new_breed")
        add_pet_submitted = st.form_submit_button("Add pet")

    if add_pet_submitted:
        if not new_pet_name.strip():
            st.error("Pet name cannot be empty.")
        elif owner.get_pet(new_pet_name):
            st.error(f"A pet named '{new_pet_name}' already exists.")
        else:
            new_pet = Pet(name=new_pet_name.strip(), species=new_species, age=int(new_age), breed=new_breed)
            owner.add_pet(new_pet)
            autosave()
            st.success(f"Added {new_pet_name}!")
            st.rerun()

# ---------------------------------------------------------------------------
# Section 3 — Add Tasks
# ---------------------------------------------------------------------------
st.divider()
st.header("3. Add care tasks")

pet_names = [p.name for p in owner.get_pets()]

with st.form("task_form"):
    col1, col2, col3 = st.columns(3)
    with col1:
        task_title = st.text_input("Task title", value="Morning walk")
    with col2:
        duration = st.number_input("Duration (min)", min_value=1, max_value=240, value=20)
    with col3:
        priority = st.selectbox("Priority", ["high", "medium", "low"])

    col4, col5, col6 = st.columns(3)
    with col4:
        task_type = st.selectbox("Task type", ["walk", "feeding", "medication", "grooming", "enrichment", "general"])
    with col5:
        frequency = st.selectbox("Frequency", ["daily", "weekly", "as-needed"])
    with col6:
        start_time = st.text_input("Start time (HH:MM)", value="", placeholder="07:00")

    description = st.text_input("Description (optional)", value="")
    assign_to   = st.selectbox("Assign to pet", pet_names)
    add_task    = st.form_submit_button("Add task")

if add_task:
    try:
        task = Task(
            title=task_title,
            duration_minutes=int(duration),
            priority=priority,
            task_type=task_type,
            frequency=frequency,
            start_time=start_time.strip(),
            description=description,
        )
        owner.get_pet(assign_to).add_task(task)
        autosave()
        st.success(f"{task_emoji(task_type)} Added '{task_title}' to {assign_to}'s tasks.")
    except ValueError as e:
        st.error(f"Could not add task: {e}")

# Task table — filtered + sorted + Challenge 3/4 colour-coded
all_tasks = owner.get_all_tasks()
if all_tasks:
    st.subheader("Current tasks")
    col_f1, col_f2 = st.columns(2)
    with col_f1:
        filter_pet = st.selectbox("Filter by pet", ["All"] + pet_names, key="filter_pet")
    with col_f2:
        filter_status = st.selectbox("Filter by status", ["All", "Pending", "Complete"], key="filter_status")

    scheduler_preview = Scheduler(owner)
    status_arg = {"Pending": "pending", "Complete": "complete"}.get(filter_status)
    pet_arg    = None if filter_pet == "All" else filter_pet
    filtered   = scheduler_preview.filter_tasks(pet_name=pet_arg, status=status_arg)
    sorted_filtered = scheduler_preview.sort_by_time([t for _, t in filtered])

    if sorted_filtered:
        # Challenge 3 + 4: priority colour badges and task-type emojis
        PRIORITY_BADGE = {"high": "🔴 High", "medium": "🟡 Medium", "low": "🟢 Low"}
        rows = []
        for t in sorted_filtered:
            pet_label = next((p.name for p in owner.get_pets() if t in p.get_tasks()), "?")
            rows.append({
                "Pet":          pet_label,
                "Task":         f"{task_emoji(t.task_type)} {t.title}",
                "Type":         t.task_type,
                "Start":        t.start_time if t.start_time else "—",
                "Duration":     f"{t.duration_minutes} min",
                "Priority":     PRIORITY_BADGE.get(t.priority, t.priority),
                "Frequency":    t.frequency,
                "Score":        int(scheduler_preview.score_task(t)),
                "Status":       "✅ Done" if t.is_complete else "⏳ Pending",
            })
        st.dataframe(rows, use_container_width=True)
    else:
        st.info("No tasks match the current filter.")
else:
    st.info("No tasks yet — add one above.")

# ---------------------------------------------------------------------------
# Section 4 — Generate Schedule
# ---------------------------------------------------------------------------
st.divider()
st.header("4. Generate today's schedule")

# Challenge 1: let user choose scheduling mode
mode = st.radio(
    "Scheduling mode",
    ["Priority-based (High → Medium → Low)", "Weighted scoring (priority + frequency + efficiency)"],
    horizontal=True,
)
weighted_mode = mode.startswith("Weighted")

col_a, col_b, col_c = st.columns(3)
with col_a:
    if st.button("Generate schedule", type="primary"):
        scheduler = Scheduler(owner)
        plan = scheduler.generate_weighted_schedule() if weighted_mode else scheduler.generate_schedule()
        st.session_state.plan      = plan
        st.session_state.scheduler = scheduler
        st.session_state.weighted  = weighted_mode

with col_b:
    if st.button("Reset day"):
        owner.reset_day()
        autosave()
        st.session_state.pop("plan", None)
        st.session_state.pop("scheduler", None)
        st.success("All tasks reset for a new day.")
        st.rerun()

with col_c:
    if st.button("💾 Save data"):
        autosave()
        st.success(f"Saved to `{DATA_FILE}`.")

if "plan" in st.session_state:
    plan      = st.session_state.plan
    scheduler = st.session_state.scheduler
    was_weighted = st.session_state.get("weighted", False)

    # Conflict warnings — prominent banner
    timed_tasks = [t for t in plan.scheduled_tasks if t.start_time]
    conflicts   = scheduler.detect_conflicts(timed_tasks)
    if conflicts:
        st.warning(
            f"⚠️ **{len(conflicts)} scheduling conflict(s) detected.** "
            "Two or more tasks overlap in time. Adjust start times to resolve."
        )
        with st.expander("View conflict details"):
            for w in conflicts:
                st.markdown(f"- {w}")

    # Schedule display — sorted chronologically, Challenge 3/4 colour + emoji
    st.subheader("Today's plan")
    PRIORITY_DOT = {"high": "🔴", "medium": "🟡", "low": "🟢"}

    if plan.scheduled_tasks:
        sorted_plan = scheduler.sort_by_time(plan.scheduled_tasks)
        for i, task in enumerate(sorted_plan, 1):
            dot      = PRIORITY_DOT.get(task.priority, "⚪")
            emoji    = task_emoji(task.task_type)
            time_str = f"@ {task.start_time} " if task.start_time else ""
            done     = task.is_complete
            label    = f"~~{task.title}~~" if done else f"**{task.title}**"
            score_str = f" · score {int(scheduler.score_task(task))}" if was_weighted else ""
            st.markdown(
                f"{dot} {i}. {emoji} {label} {time_str}— "
                f"{task.duration_minutes} min · `{task.frequency}`{score_str}"
                + (" ✅" if done else "")
            )
            if task.description and not done:
                st.caption(f"    {task.description}")
    else:
        st.warning("No tasks could be scheduled. Try adding tasks or increasing your available time.")

    # Metrics
    remaining = owner.get_available_time() - plan.total_duration
    c1, c2, c3 = st.columns(3)
    c1.metric("Scheduled",  f"{plan.total_duration} min")
    c2.metric("Available",  f"{owner.get_available_time()} min")
    c3.metric("Remaining",  f"{remaining} min")

    # Skipped tasks
    if plan.skipped_tasks:
        with st.expander(f"⏭ Skipped tasks ({len(plan.skipped_tasks)}) — not enough time"):
            for task in plan.skipped_tasks:
                dot = PRIORITY_DOT.get(task.priority, "⚪")
                st.markdown(f"- {dot} {task_emoji(task.task_type)} **{task.title}** ({task.duration_minutes} min · `{task.priority}`)")

    # Reasoning
    with st.expander("How was this plan built?"):
        if was_weighted:
            st.text(scheduler.explain_weighted_plan(plan))
        else:
            st.text(scheduler.explain_plan(plan))

    # Mark complete
    st.subheader("Mark tasks complete")
    task_titles = [t.title for t in plan.scheduled_tasks if not t.is_complete]
    if task_titles:
        done_title = st.selectbox("Select completed task", task_titles)
        if st.button("Mark complete ✅"):
            scheduler.mark_task_complete(done_title)
            autosave()
            for t in owner.get_all_tasks():
                if t.title.lower() == done_title.lower() and t.next_due:
                    st.success(f"'{done_title}' done! 🎉 Next due: {t.next_due}")
                    break
            else:
                st.success(f"'{done_title}' marked as done! 🎉")
            st.rerun()
    else:
        st.success("🎉 All scheduled tasks complete for today!")

    # Progress
    with st.expander("Progress summary"):
        all_t  = owner.get_all_tasks()
        done_n = sum(1 for t in all_t if t.is_complete)
        st.progress(done_n / len(all_t) if all_t else 0)
        st.text(scheduler.get_completion_summary())
