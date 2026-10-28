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

# --- Add a pet ---
st.subheader("Add a pet")
with st.form("add_pet", clear_on_submit=True):
    pet_name = st.text_input("Pet name")
    species = st.selectbox("Species", ["dog", "cat", "other"])
    age = st.number_input("Age (years)", min_value=0, max_value=40, value=1)
    if st.form_submit_button("Add pet"):
        try:
            owner.add_pet(Pet(pet_name.strip(), species, int(age)))
            st.success(f"Added {pet_name.strip()}!")
        except ValueError as err:
            st.error(str(err))

# --- Schedule a task ---
st.subheader("Schedule a task")
if not owner.pets:
    st.info("Add a pet first.")
else:
    with st.form("add_task", clear_on_submit=True):
        pet_choice = st.selectbox("Pet", [p.name for p in owner.pets])
        description = st.text_input("Task", value="Morning walk")
        task_time = st.time_input("Time")
        duration = st.number_input("Duration (minutes)", min_value=1, max_value=240, value=20)
        priority = st.selectbox("Priority", ["low", "medium", "high"], index=2)
        frequency = st.selectbox("Repeats", ["once", "daily", "weekly"])
        if st.form_submit_button("Add task"):
            owner.get_pet(pet_choice).add_task(
                Task(description, task_time.strftime("%H:%M"), int(duration), priority, frequency)
            )
            st.success(f"Scheduled '{description}' for {pet_choice}.")

# --- Today's schedule ---
st.subheader("Today's schedule")
todays = scheduler.get_todays_schedule()
if todays:
    st.table(
        [
            {"Time": t.time, "Pet": t.pet_name, "Task": t.description,
             "Minutes": t.duration_minutes, "Priority": t.priority, "Done": t.completed}
            for t in todays
        ]
    )
else:
    st.info("No tasks scheduled for today.")
