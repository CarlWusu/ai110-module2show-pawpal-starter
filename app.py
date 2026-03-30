import streamlit as st
from pawpal_system import Owner, Pet, Task, Scheduler

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")

st.title("🐾 PawPal+")

# ---------------------------------------------------------------------------
# Session state initialisation
# Streamlit re-runs the entire script on every interaction.
# We store the Owner object in st.session_state so it survives re-runs.
# ---------------------------------------------------------------------------
if "owner" not in st.session_state:
    st.session_state.owner = None   # set once the user submits the setup form

# ---------------------------------------------------------------------------
# Step 1 — Owner & Pet Setup
# ---------------------------------------------------------------------------
st.header("1. Who's using PawPal+?")

with st.form("setup_form"):
    owner_name = st.text_input("Your name", value="Jordan")
    available_time = st.number_input(
        "How many minutes do you have available today?",
        min_value=10, max_value=480, value=90, step=5,
    )
    pet_name = st.text_input("Pet name", value="Mochi")
    species = st.selectbox("Species", ["dog", "cat", "rabbit", "bird", "other"])
    age = st.number_input("Pet age (years)", min_value=0, max_value=30, value=3)
    breed = st.text_input("Breed (optional)", value="")
    submitted = st.form_submit_button("Save owner & pet")

if submitted:
    # Build a fresh Owner with one Pet each time the form is saved.
    owner = Owner(name=owner_name, available_minutes_per_day=int(available_time))
    pet = Pet(name=pet_name, species=species, age=int(age), breed=breed)
    owner.add_pet(pet)
    st.session_state.owner = owner
    st.success(f"Saved! Welcome, {owner_name}. {pet_name} is ready.")

# Guard — nothing below this runs until an owner exists in session state.
if st.session_state.owner is None:
    st.info("Fill in the form above to get started.")
    st.stop()

owner: Owner = st.session_state.owner

# ---------------------------------------------------------------------------
# Step 2 — Add Another Pet
# ---------------------------------------------------------------------------
st.divider()
st.header("2. Manage pets")

# Show all current pets
pets = owner.get_pets()
if pets:
    st.write(f"**{owner.name}'s pets:** " + ", ".join(f"{p.name} ({p.species})" for p in pets))

with st.expander("Add another pet"):
    with st.form("add_pet_form"):
        new_pet_name = st.text_input("Pet name")
        new_species = st.selectbox("Species", ["dog", "cat", "rabbit", "bird", "other"], key="new_species")
        new_age = st.number_input("Age (years)", min_value=0, max_value=30, value=1, key="new_age")
        new_breed = st.text_input("Breed (optional)", key="new_breed")
        add_pet_submitted = st.form_submit_button("Add pet")

    if add_pet_submitted:
        if new_pet_name.strip() == "":
            st.error("Pet name cannot be empty.")
        elif owner.get_pet(new_pet_name):
            st.error(f"A pet named '{new_pet_name}' already exists.")
        else:
            # owner.add_pet() appends the new Pet to the owner's internal list.
            # Because owner lives in st.session_state, the change persists across re-runs.
            new_pet = Pet(name=new_pet_name.strip(), species=new_species, age=int(new_age), breed=new_breed)
            owner.add_pet(new_pet)
            st.success(f"Added {new_pet_name} to your pets!")
            st.rerun()

# ---------------------------------------------------------------------------
# Step 3 — Add Tasks
# ---------------------------------------------------------------------------
st.divider()
st.header("3. Add care tasks")

# Show which pet(s) are available to assign tasks to.
pet_names = [p.name for p in owner.get_pets()]

with st.form("task_form"):
    col1, col2, col3 = st.columns(3)
    with col1:
        task_title = st.text_input("Task title", value="Morning walk")
    with col2:
        duration = st.number_input("Duration (min)", min_value=1, max_value=240, value=20)
    with col3:
        priority = st.selectbox("Priority", ["high", "medium", "low"])

    col4, col5 = st.columns(2)
    with col4:
        task_type = st.selectbox("Task type", ["walk", "feeding", "medication", "grooming", "enrichment", "general"])
    with col5:
        frequency = st.selectbox("Frequency", ["daily", "weekly", "as-needed"])

    description = st.text_input("Description (optional)", value="")
    assign_to = st.selectbox("Assign to pet", pet_names)
    add_task = st.form_submit_button("Add task")

if add_task:
    task = Task(
        title=task_title,
        duration_minutes=int(duration),
        priority=priority,
        task_type=task_type,
        frequency=frequency,
        description=description,
    )
    pet = owner.get_pet(assign_to)
    pet.add_task(task)
    st.success(f"Added '{task_title}' to {assign_to}'s tasks.")

# Display current tasks
all_tasks = owner.get_all_tasks()
if all_tasks:
    st.subheader("Current tasks")
    st.table([
        {
            "Pet": next(p.name for p in owner.get_pets() if task in p.get_tasks()),
            "Task": t.title,
            "Type": t.task_type,
            "Duration (min)": t.duration_minutes,
            "Priority": t.priority,
            "Frequency": t.frequency,
            "Done": "✓" if t.is_complete else "",
        }
        for t in all_tasks
    ])
else:
    st.info("No tasks yet — add one above.")

# ---------------------------------------------------------------------------
# Step 3 — Generate Schedule
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
        st.success("All tasks reset for a new day.")

if "plan" in st.session_state:
    plan = st.session_state.plan
    scheduler = st.session_state.scheduler

    st.subheader("Today's plan")
    if plan.scheduled_tasks:
        for i, task in enumerate(plan.scheduled_tasks, 1):
            st.markdown(f"**{i}. {task.title}** — {task.duration_minutes} min · `{task.priority}` · {task.frequency}")
            if task.description:
                st.caption(task.description)
    else:
        st.warning("No tasks could be scheduled. Try adding tasks or increasing your available time.")

    st.metric("Total time scheduled", f"{plan.total_duration} min", f"of {owner.get_available_time()} min available")

    if plan.skipped_tasks:
        with st.expander(f"Skipped tasks ({len(plan.skipped_tasks)})"):
            for task in plan.skipped_tasks:
                st.markdown(f"- **{task.title}** ({task.duration_minutes} min) — not enough time remaining")

    with st.expander("Reasoning"):
        st.text(scheduler.explain_plan(plan))

    st.subheader("Mark tasks complete")
    task_titles = [t.title for t in plan.scheduled_tasks if not t.is_complete]
    if task_titles:
        done_title = st.selectbox("Select completed task", task_titles)
        if st.button("Mark complete"):
            scheduler.mark_task_complete(done_title)
            st.success(f"'{done_title}' marked as done!")
            st.rerun()
    else:
        st.success("All scheduled tasks are complete!")

    with st.expander("Progress summary"):
        st.text(scheduler.get_completion_summary())
