import streamlit as st
from pawpal_system import Owner, Pet, Task, Scheduler

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")

st.title("🐾 PawPal+")
st.caption("Your daily pet care planner — prioritised, sorted, and conflict-checked.")

# ---------------------------------------------------------------------------
# Session state initialisation
# ---------------------------------------------------------------------------
if "owner" not in st.session_state:
    st.session_state.owner = None

# ---------------------------------------------------------------------------
# Section 1 — Owner & Pet Setup
# ---------------------------------------------------------------------------
st.header("1. Who's using PawPal+?")

with st.form("setup_form"):
    owner_name = st.text_input("Your name", value="Jordan")
    available_time = st.number_input(
        "How many minutes do you have available today?",
        min_value=0, max_value=480, value=90, step=5,
    )
    pet_name = st.text_input("Pet name", value="Mochi")
    species = st.selectbox("Species", ["dog", "cat", "rabbit", "bird", "other"])
    age = st.number_input("Pet age (years)", min_value=0, max_value=30, value=3)
    breed = st.text_input("Breed (optional)", value="")
    submitted = st.form_submit_button("Save owner & pet")

if submitted:
    owner = Owner(name=owner_name, available_minutes_per_day=int(available_time))
    pet = Pet(name=pet_name, species=species, age=int(age), breed=breed)
    owner.add_pet(pet)
    st.session_state.owner = owner
    st.session_state.pop("plan", None)
    st.session_state.pop("scheduler", None)
    st.success(f"Saved! Welcome, {owner_name}. {pet_name} is ready.")

if st.session_state.owner is None:
    st.info("Fill in the form above to get started.")
    st.stop()

owner: Owner = st.session_state.owner

# ---------------------------------------------------------------------------
# Section 2 — Manage Pets
# ---------------------------------------------------------------------------
st.divider()
st.header("2. Manage pets")

pets = owner.get_pets()
if pets:
    st.write("**Current pets:** " + ", ".join(f"{p.name} ({p.species}, {p.age}yr)" for p in pets))

with st.expander("Add another pet"):
    with st.form("add_pet_form"):
        new_pet_name = st.text_input("Pet name")
        new_species = st.selectbox("Species", ["dog", "cat", "rabbit", "bird", "other"], key="new_species")
        new_age = st.number_input("Age (years)", min_value=0, max_value=30, value=1, key="new_age")
        new_breed = st.text_input("Breed (optional)", key="new_breed")
        add_pet_submitted = st.form_submit_button("Add pet")

    if add_pet_submitted:
        if not new_pet_name.strip():
            st.error("Pet name cannot be empty.")
        elif owner.get_pet(new_pet_name):
            st.error(f"A pet named '{new_pet_name}' already exists.")
        else:
            new_pet = Pet(name=new_pet_name.strip(), species=new_species, age=int(new_age), breed=new_breed)
            owner.add_pet(new_pet)
            st.success(f"Added {new_pet_name} to your pets!")
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
        start_time = st.text_input("Start time (HH:MM, optional)", value="", placeholder="07:00")

    description = st.text_input("Description (optional)", value="")
    assign_to = st.selectbox("Assign to pet", pet_names)
    add_task = st.form_submit_button("Add task")

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
        pet = owner.get_pet(assign_to)
        pet.add_task(task)
        st.success(f"Added '{task_title}' to {assign_to}'s tasks.")
    except ValueError as e:
        st.error(f"Could not add task: {e}")

# Task table — sorted by time
all_tasks = owner.get_all_tasks()
if all_tasks:
    st.subheader("Current tasks")

    # Filter controls
    col_f1, col_f2 = st.columns(2)
    with col_f1:
        filter_pet = st.selectbox("Filter by pet", ["All"] + pet_names, key="filter_pet")
    with col_f2:
        filter_status = st.selectbox("Filter by status", ["All", "Pending", "Complete"], key="filter_status")

    scheduler_preview = Scheduler(owner)
    status_arg = {"Pending": "pending", "Complete": "complete"}.get(filter_status)
    pet_arg = None if filter_pet == "All" else filter_pet
    filtered = scheduler_preview.filter_tasks(pet_name=pet_arg, status=status_arg)

    # Sort filtered tasks by start_time
    filtered_tasks = [t for _, t in filtered]
    sorted_filtered = scheduler_preview.sort_by_time(filtered_tasks)

    if sorted_filtered:
        rows = []
        for t in sorted_filtered:
            pet_name_label = next(
                (p.name for p in owner.get_pets() if t in p.get_tasks()), "?"
            )
            rows.append({
                "Pet": pet_name_label,
                "Task": t.title,
                "Type": t.task_type,
                "Start": t.start_time if t.start_time else "—",
                "Duration (min)": t.duration_minutes,
                "Priority": t.priority,
                "Frequency": t.frequency,
                "Status": "✓ Done" if t.is_complete else "Pending",
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

col_a, col_b = st.columns(2)
with col_a:
    if st.button("Generate schedule", type="primary"):
        scheduler = Scheduler(owner)
        plan = scheduler.generate_schedule()
        st.session_state.plan = plan
        st.session_state.scheduler = scheduler

with col_b:
    if st.button("Reset day (clear completions)"):
        owner.reset_day()
        st.session_state.pop("plan", None)
        st.session_state.pop("scheduler", None)
        st.success("All tasks reset for a new day.")
        st.rerun()

if "plan" in st.session_state:
    plan = st.session_state.plan
    scheduler = st.session_state.scheduler

    # --- Conflict warnings — shown prominently before the plan ---
    timed_tasks = [t for t in plan.scheduled_tasks if t.start_time]
    conflicts = scheduler.detect_conflicts(timed_tasks)
    if conflicts:
        st.warning(
            f"⚠️ **{len(conflicts)} scheduling conflict(s) detected.** "
            "Two or more tasks overlap in time. Review and adjust start times."
        )
        with st.expander("View conflict details"):
            for warning in conflicts:
                st.markdown(f"- {warning}")

    # --- Scheduled tasks sorted by start time ---
    st.subheader("Today's plan")
    if plan.scheduled_tasks:
        sorted_plan = scheduler.sort_by_time(plan.scheduled_tasks)
        for i, task in enumerate(sorted_plan, 1):
            time_str = f"@ {task.start_time} " if task.start_time else ""
            priority_color = {"high": "🔴", "medium": "🟡", "low": "🟢"}.get(task.priority, "⚪")
            done = task.is_complete
            label = f"~~{task.title}~~" if done else f"**{task.title}**"
            st.markdown(
                f"{priority_color} {i}. {label} {time_str}— "
                f"{task.duration_minutes} min · `{task.frequency}`"
                + (" ✓" if done else "")
            )
            if task.description and not done:
                st.caption(f"  {task.description}")
    else:
        st.warning("No tasks could be scheduled. Try adding tasks or increasing your available time.")

    # --- Metrics ---
    remaining = owner.get_available_time() - plan.total_duration
    col_m1, col_m2, col_m3 = st.columns(3)
    col_m1.metric("Scheduled", f"{plan.total_duration} min")
    col_m2.metric("Available", f"{owner.get_available_time()} min")
    col_m3.metric("Remaining", f"{remaining} min")

    # --- Skipped tasks ---
    if plan.skipped_tasks:
        with st.expander(f"⏭ Skipped tasks ({len(plan.skipped_tasks)}) — not enough time"):
            for task in plan.skipped_tasks:
                st.markdown(f"- **{task.title}** ({task.duration_minutes} min · `{task.priority}` priority)")

    # --- Reasoning ---
    with st.expander("How was this plan built?"):
        st.text(scheduler.explain_plan(plan))

    # --- Mark complete ---
    st.subheader("Mark tasks complete")
    task_titles = [t.title for t in plan.scheduled_tasks if not t.is_complete]
    if task_titles:
        done_title = st.selectbox("Select completed task", task_titles)
        if st.button("Mark complete"):
            scheduler.mark_task_complete(done_title)
            # Find the task to show next_due if recurring
            for t in owner.get_all_tasks():
                if t.title.lower() == done_title.lower() and t.next_due:
                    st.success(f"'{done_title}' done! Next due: {t.next_due}")
                    break
            else:
                st.success(f"'{done_title}' marked as done!")
            st.rerun()
    else:
        st.success("🎉 All scheduled tasks are complete for today!")

    # --- Progress summary ---
    with st.expander("Progress summary"):
        all_t = owner.get_all_tasks()
        done_count = sum(1 for t in all_t if t.is_complete)
        st.progress(done_count / len(all_t) if all_t else 0)
        st.text(scheduler.get_completion_summary())
