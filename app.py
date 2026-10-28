from datetime import date

import streamlit as st

from pawpal_system import Owner, Pet, Scheduler, Task

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")
st.title("🐾 PawPal+")
st.caption("Plan and track daily care for all of your pets.")

# --- App "memory": create the Owner once per session, then reuse it on every rerun ---
if "owner" not in st.session_state:
    st.session_state.owner = Owner("Jordan")
owner: Owner = st.session_state.owner
scheduler = Scheduler(owner)

owner.name = st.text_input("Owner name", value=owner.name)

# --- Add a pet -> Owner.add_pet ---
st.subheader("1. Add a pet")
with st.form("add_pet", clear_on_submit=True):
    c1, c2, c3 = st.columns([2, 1, 1])
    with c1:
        pet_name = st.text_input("Pet name")
    with c2:
        species = st.selectbox("Species", ["dog", "cat", "other"])
    with c3:
        age = st.number_input("Age", min_value=0, max_value=40, value=1)
    if st.form_submit_button("Add pet"):
        try:
            owner.add_pet(Pet(pet_name, species, int(age)))
            st.success(f"Added {pet_name.strip()} the {species}!")
        except ValueError as err:
            st.error(str(err))

if owner.pets:
    st.caption("Your pets: " + ", ".join(f"{p.name} ({p.species}, {len(p.tasks)} tasks)" for p in owner.pets))

# --- Schedule a task -> Pet.add_task ---
st.subheader("2. Schedule a task")
if not owner.pets:
    st.info("Add a pet first.")
else:
    with st.form("add_task", clear_on_submit=True):
        c1, c2 = st.columns(2)
        with c1:
            pet_choice = st.selectbox("Pet", [p.name for p in owner.pets])
            description = st.text_input("Task", value="Morning walk")
            task_date = st.date_input("Date", value=date.today())
            task_time = st.time_input("Time")
        with c2:
            duration = st.number_input("Duration (minutes)", min_value=1, max_value=240, value=20)
            priority = st.selectbox("Priority", ["low", "medium", "high"], index=2)
            frequency = st.selectbox("Repeats", ["once", "daily", "weekly"])
        if st.form_submit_button("Add task"):
            if not description.strip():
                st.error("Give the task a name.")
            else:
                task = Task(description.strip(), task_time.strftime("%H:%M"), int(duration),
                            priority, frequency, due_date=task_date)
                owner.get_pet(pet_choice).add_task(task)
                st.success(f"Scheduled '{task.description}' for {pet_choice} on {task_date:%b %d} at {task.time}.")

# --- Schedule view -> Scheduler.sort_by_time / filter_tasks / detect_conflicts ---
st.subheader("3. Schedule")
view_date = st.date_input("Show schedule for", value=date.today(), key="view_date")

# Mark complete first, so the table below already reflects the change on this run.
pending_today = scheduler.filter_tasks(scheduler.get_todays_schedule(view_date), completed=False)
if pending_today:
    labels = {f"{t.time} · {t.pet_name}: {t.description}": t for t in pending_today}
    c1, c2 = st.columns([3, 1])
    with c1:
        choice = st.selectbox("Mark a task complete", list(labels), key="complete_choice")
    with c2:
        if st.button("✅ Done"):
            task = labels[choice]
            follow_up = scheduler.mark_task_complete(task)
            msg = f"Completed '{task.description}' for {task.pet_name}."
            if follow_up:
                msg += f" Next {task.frequency} occurrence added for {follow_up.due_date:%a %b %d} at {follow_up.time}."
            st.success(msg)

c1, c2 = st.columns(2)
with c1:
    pet_filter = st.selectbox("Filter by pet", ["All pets"] + [p.name for p in owner.pets], key="pet_filter")
with c2:
    status_filter = st.selectbox("Filter by status", ["All", "To do", "Done"], key="status_filter")

day_tasks = scheduler.get_todays_schedule(view_date)  # already sorted by time
shown = scheduler.filter_tasks(
    day_tasks,
    pet_name=None if pet_filter == "All pets" else pet_filter,
    completed={"All": None, "To do": False, "Done": True}[status_filter],
)

conflicts = scheduler.detect_conflicts(day_tasks)
for warning in conflicts:
    st.warning(f"⚠️ {warning}. You might not be able to do both at once — consider moving one of them.")

if shown:
    if not conflicts:
        st.success(f"No scheduling conflicts. {len(shown)} task(s) shown, in time order.")
    priority_icon = {"high": "🔴 high", "medium": "🟡 medium", "low": "🟢 low"}
    st.table(
        [
            {
                "Time": t.time,
                "Pet": t.pet_name,
                "Task": t.description,
                "Minutes": t.duration_minutes,
                "Priority": priority_icon[t.priority],
                "Repeats": t.frequency,
                "Status": "✅ done" if t.completed else "⏳ to do",
            }
            for t in shown
        ]
    )
    done = len([t for t in day_tasks if t.completed])
    st.caption(f"{done} of {len(day_tasks)} task(s) done for {view_date:%A, %b %d}.")
elif day_tasks:
    st.info("No tasks match these filters.")
else:
    st.info("No tasks scheduled for this day.")
