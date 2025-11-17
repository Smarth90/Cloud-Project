import streamlit as st
import random
import google.generativeai as genai
import time
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
import io
import pandas as pd

# -----------------------
# Page setup
# -----------------------
st.set_page_config(
    page_title="FitForge AI",
    page_icon="💪",
    layout="centered"
)


# -----------------------
# Gemini setup
# -----------------------
genai.configure(api_key=st.secrets["AIzaSyB1xf9-26zZzCAYYmYuqT8-C8t240Vjc9Q"])

model = genai.GenerativeModel(
    "gemini-2.5-flash",
    system_instruction="""
    You are FitForge AI, a professional fitness assistant.
    Always format responses as polished Markdown:
    - Main heading with fitness level and goal
    - Make sure the output is always only relevant text and information and make it consise and in a tabular form
    - Weekly schedule as a table
    - Detailed daily workouts with sets, reps, and notes
    - Important Guidelines and Additional Tips
    Keep responses concise, structured, and user-friendly.
    """
)

# -----------------------
# Response generator
# -----------------------
def response_generator(prompt: str) -> str:
    try:
        response = model.generate_content(prompt, stream= True)
        full_response = ""
        for chunk in response:
            if hasattr(chunk, "text") and chunk.text:
                full_response += chunk.text
                yield chunk.text
        return full_response
    except Exception as e:
        error_message =  f"⚠️ Error generating response: {str(e)}"
        yield error_message
        return error_message

# -----------------------
# Render response
# -----------------------
def render_response(response_stream):
    full_response = "" 
    placeholder = st.empty()
    for chunk in response_stream:
        full_response += chunk
        placeholder.markdown(full_response, unsafe_allow_html=True)
    return full_response

# -----------------------
# PDF gen
# -----------------------

from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import io

def export_pdf(plan_text: str):
    buffer = io.BytesIO()
    
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=50,
        leftMargin=50,
        topMargin=50,
        bottomMargin=50
    )
    
   
    styles = getSampleStyleSheet()
    title_style = styles['Heading1']
    title_style.alignment = 1 
    normal_style = styles['Normal']
    normal_style.spaceAfter = 10
    bullet_style = ParagraphStyle(
        'Bullet',
        parent=normal_style,
        bulletIndent=10,
        leftIndent=20
    )
    
    elements = []
    
    
    elements.append(Paragraph("💪 FitForge AI - Workout & Diet Plan", title_style))
    elements.append(Spacer(1, 12))
    
    
    sections = plan_text.split("\n\n")
    
    for section in sections:
        section = section.strip()
        if not section:
            continue

        
        if "|" in section:
            lines = section.split("\n")
            table_data = [line.strip().split("|") for line in lines]
            table_data = [[cell.strip() for cell in row] for row in table_data]
            
            table = Table(table_data, hAlign='CENTER')
            table.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#4CAF50")),
                ('TEXTCOLOR', (0,0), (-1,0), colors.white),
                ('GRID', (0,0), (-1,-1), 0.5, colors.black),
                ('ALIGN', (0,0), (-1,-1), 'CENTER'),
                ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
                ('FONTNAME', (0,1), (-1,-1), 'Helvetica'),
                ('FONTSIZE', (0,0), (-1,-1), 10)
            ]))
            elements.append(table)
            elements.append(Spacer(1, 12))
        else:
            paragraph_text = section.replace("\n", "<br/>")
            elements.append(Paragraph(paragraph_text, normal_style))
            elements.append(Spacer(1, 12))
    
    doc.build(elements)
    buffer.seek(0)
    return buffer.getvalue()


# -----------------------
# Format User Details
# -----------------------
def format_user_details(details: dict) -> str:
    user_info = details.get("UserInfo", {})
    workout = details.get("Workout", {})
    diet = details.get("Diet", {})

    formatted_prompt = (
        "👤 **User Info**\n"
        f"- Gender: {user_info.get('Gender', 'N/A')}\n"
        f"- Age: {user_info.get('Age', 'N/A')}\n"
        f"- Weight: {user_info.get('Weight', 'N/A')} kg\n"
        f"- Height: {user_info.get('Height', 'N/A')}\n\n"
        "💪 **Workout Preferences**\n"
        f"- Fitness Level: {workout.get('Fitness Level', 'N/A')}\n"
        f"- Goal: {workout.get('Goal', 'N/A')}\n"
        f"- Days per Week: {workout.get('Days per Week', 'N/A')}\n"
        f"- Duration: {workout.get('Duration', 'N/A')}\n"
        f"- Equipment: {workout.get('Equipment', 'N/A')}\n"
        f"- Workout Type: {', '.join(workout.get('Workout Type', []))}\n"
        f"- Rest Days: {', '.join(workout.get('Rest Days', []))}\n\n"
        "🥗 **Dietary Preferences**\n"
        f"- Diet: {diet.get('Diet', 'N/A')}\n"
        f"- Cuisine Preference: {diet.get('Cuisine Preference', 'N/A')}\n"
        f"- Allergies: {diet.get('Allergies', 'N/A')}\n"
        f"- Foods Disliked: {diet.get('Foods Disliked', 'N/A')}\n"
    )

    return formatted_prompt

# -----------------------
# Placeholders
# -----------------------
placeholders = [
    "Ask me for a workout plan...",
    "Type your fitness goal (e.g., weight loss, muscle gain)...",
    "Example: Suggest a 4-day weight loss workout",
    "Need a home workout? Just ask!",
    "Type an exercise you want to learn (e.g., deadlifts)",
    "Ask about meal plans or nutrition tips...",
    "Example: High-protein vegetarian breakfast ideas",
    "Type a food item to see its calories/macros",
    "Want a healthy recipe? Just ask!",
    "Example: What should I eat before workout?",
    "Check your progress: type 'track my workout'",
    "Need motivation? Ask me for a fitness quote 💪",
    "Type your current weight/goal to get advice",
    "Example: 3-day workout plan for beginners",
    "Ask me how to stay consistent!",
    "Ask about sleep, recovery, or stress management...",
    "Example: Best stretches after running",
    "Want a meditation tip? Just ask",
    "Type 'rest day advice' for recovery tips",
    "Example: How much water should I drink daily?",
]

# -----------------------
# Handling Session States
# -----------------------
if "placeholder" not in st.session_state:
    st.session_state.placeholder = random.choice(placeholders)

if "messages" not in st.session_state:
    st.session_state.messages = []

if "user_details" not in st.session_state:
    st.session_state.user_details = {}

if "user_info" not in st.session_state:
    st.session_state.user_info = {}

if "last_plan" not in st.session_state:
    st.session_state["last_plan"] = None

if "diet" not in st.session_state:
    st.session_state.diet = {}

if "wokout_preferences" not in st.session_state:
    st.session_state.workout_preferences = {}

if "page" not in st.session_state:
    st.session_state.page = None

if "progress_log" not in st.session_state:
        st.session_state.progress_log = []

# -----------------------
# Render past messages
# -----------------------
for message in st.session_state.messages:
    avatar = "💪" if message["role"] == "ai" else "🙂"
    with st.chat_message(message["role"], avatar=avatar):
        st.markdown(message["content"], unsafe_allow_html=True)

# -----------------------
# Handle user input
# -----------------------
def handle_prompt(prompt: str):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user", avatar="🙂"):
        st.markdown(prompt)

   
    with st.chat_message("ai", avatar="💪"):
         
        with st.spinner("Thinking..."):
            response_stream  = response_generator(prompt)
            full_response = render_response(response_stream)
        
    st.session_state.messages.append({"role": "ai", "content": full_response})
    return full_response

# -----------------------
# Show Home
# -----------------------
def show_home():
    st.title("💪 FitForge AI")
    st.subheader("Your Personal Fitness & Nutrition Assistant")
    st.markdown("Get **workouts, meal plans, and motivation** powered by AI 🚀")
    for message in st.session_state.messages:
        avatar = "💪" if message["role"] == "ai" else "🙂"
        with st.chat_message(message["role"], avatar=avatar):
            st.markdown(message["content"], unsafe_allow_html=True)


# -----------------------
# Show Profile
# -----------------------
def show_profile_page():
    st.title("👤 Profile Settings")
    st.markdown("View or edit your user, workout, and diet details below:")

    user_info = st.session_state.user_details.get("UserInfo", {})
    workout = st.session_state.user_details.get("Workout", {})
    diet = st.session_state.user_details.get("Diet", {})
    # User info
    with st.form("user_info_form"):
        st.subheader("User Info")
        gender = st.selectbox("Gender", ["Male","Female"], index=0 if user_info.get("Gender", "Male") == "Male" else 1)
        age = st.number_input("Age", 16, 100, value = user_info.get("Age", 25))
        weight = st.number_input("Weight (kg)", 40, 200, value= user_info.get("Weight", 70))
        height_ft = st.number_input("Height (ft)", 4, 8, value=int(user_info.get("Height","5 ft 7 in").split()[0]))
        height_in = st.number_input("Height (in)", 0, 11, value=int(user_info.get("Height","5 ft 7 in").split()[2]))
        save_user_info = st.form_submit_button("Save User Info")
        if save_user_info:
            st.session_state.user_details["UserInfo"] = {
                "Gender": gender,
                "Age": age,
                "Weight": weight,
                "Height": f"{height_ft} ft {height_in} in"
            }
            st.success("✅ User info saved!")

    # Workout settings
    with st.form("workout_form"):
        st.subheader("Workout Preferences")
        fitness_level = st.selectbox("Fitness Level", ["Beginner","Intermediate","Advanced"], index=["Beginner","Intermediate","Advanced"].index(workout.get("Fitness Level","Beginner")))
        goal = st.selectbox("Goal", ["Weight Loss","Muscle Gain","General Fitness"], index=["Weight Loss","Muscle Gain","General Fitness"].index(workout.get("Goal","Weight Loss")))
        days = st.selectbox("Days per Week", ["2-3","4-5","6-7"], index=["2-3","4-5","6-7"].index(workout.get("Days per Week","2-3")))
        duration = st.selectbox("Workout Duration", ["30 min","45 min","60 min"], index=["30 min","45 min","60 min"].index(workout.get("Duration","30 min")))
        equipment = st.selectbox("Equipment", ["Full Gym","Limited Gym","No Equipment"], index=["Full Gym","Limited Gym","No Equipment"].index(workout.get("Equipment","Full Gym")))
        workout_type = st.multiselect("Workout Type", ["Cardio", "Strength Training", "HIIT", "Yoga", "Pilates", "CrossFit"], default=workout.get("Workout Type",[]))
        rest_days = st.multiselect("Rest Days", ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"], default=workout.get("Rest Days",[]))
        save_workout = st.form_submit_button("Save Workout Preferences")
        if save_workout:
            st.session_state.user_details["Workout"] = {
                "Fitness Level": fitness_level,
                "Goal": goal,
                "Days per Week": days,
                "Duration": duration,
                "Equipment": equipment,
                "Workout Type": workout_type,
                "Rest Days": rest_days
            }
            st.success("✅ Workout preferences saved!")

    # Diet settings
    with st.form("diet_form"):
        st.subheader("Diet Preferences")
        diet_choice = st.selectbox("Diet", ["Vegetarian","Non-Vegetarian","Vegan","Keto","Paleo","Intermittent Fasting"], index=["Vegetarian","Non-Vegetarian","Vegan","Keto","Paleo","Intermittent Fasting"].index(diet.get("Diet","Vegetarian")))
        cuisine = st.selectbox("Cuisine Preference", ["Indian","American","Mediterranean","Asian","Middle Eastern","No Preference"], index=["Indian","American","Mediterranean","Asian","Middle Eastern","No Preference"].index(diet.get("Cuisine Preference","Indian")))
        allergies = st.text_input("Allergies (comma-separated)", value=diet.get("Allergies",""))
        dislikes = st.text_area("Foods you dislike", value=diet.get("Foods Disliked",""))
        save_diet = st.form_submit_button("Save Diet Preferences")
        if save_diet:
            st.session_state.user_details["Diet"] = {
                "Diet": diet_choice,
                "Cuisine Preference": cuisine,
                "Allergies": allergies,
                "Foods Disliked": dislikes
            }
            st.success("✅ Diet preferences saved!")

# -----------------------
# Chat input
# -----------------------
if prompt := st.chat_input(st.session_state.placeholder, key="user_input"):
    handle_prompt(prompt)


# -----------------------
# Sidebar Headers
# -----------------------


st.sidebar.header("FitForge AI Dashboard")

col1_1, col2_2 = st.sidebar.columns(2)
with col1_1:
    if st.button("🏠 Home Page", key = "Sidebar Home button"):
        st.session_state.page = "Home"
with col2_2:
    if st.button("👤 Profile "):
        st.session_state.page = "Profile"
    



st.sidebar.markdown("---")

# -----------------------
# Sidebar Expanders
# -----------------------

with st.sidebar.expander("ℹ️ User info and Information"):
    with st.form("user_information"):
        st.subheader("ℹ️ User info")
        gender = st.selectbox("Gender", ["Male", "Female"])
        age = st.number_input("Age: ", min_value = 16, max_value= 100, step = 1)
        weight = st.number_input("Weight (kgs): ")
        col1, col2 = st.columns(2)
        with col1:
            height_feet = st.number_input("Height (ft)", min_value=4, max_value=8, step=1)
        with col2:
            height_inches = st.number_input("Height (in)", min_value=0, max_value=11, step=1)
        submit_user_info = st.form_submit_button("Save Preferences")

with st.sidebar.expander("💪 Workout Settings"):
    with st.form("workout_details"):
        st.subheader("💪 Workout Settings")
        workout_type = st.multiselect(
            "Preferred Workout Types",
            ["Cardio", "Strength Training", "HIIT", "Yoga", "Pilates", "CrossFit"]
        )
        rest_days = st.multiselect(
            "Preferred Rest Days",
            ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        )
        fitness_level = st.selectbox("Fitness Level", ["Beginner", "Intermediate", "Advanced"])
        goal = st.selectbox("Goal", ["Weight Loss", "Muscle Gain", "General Fitness", "Strength Training", "Endurance"])
        days = st.selectbox("Days per Week", ["2-3", "4-5", "6-7"])
        duration = st.selectbox("Workout Duration", ["30 min", "45 min", "60 min", "90 min+"])
        equipment = st.selectbox("Equipment", ["Full Gym", "Limited Gym", "No Equipment"])
        submit_workout_preferences = st.form_submit_button("Save Preferences")

with st.sidebar.expander("🥗 Dietary Preferences"):
    with st.form("diet_preferences"):
        st.subheader("🥗 Dietary Preferences")
        diet = st.selectbox(
            "Dietary Choice:",
            ["Vegetarian", "Non-Vegetarian", "Vegan", "Keto", "Paleo", "Intermittent Fasting"]
        )
        country = st.selectbox(
            "Cuisine Preference:",
            ["Indian", "American", "Mediterranean", "Asian", "Middle Eastern", "No Preference"]
        )
        allergies = st.text_input(
            "Food Allergies (comma-separated):",
            placeholder="e.g. peanuts, dairy, gluten"
        )
        dislikes = st.text_area(
            "Foods You Dislike:",
            placeholder="e.g. broccoli, eggplant"
        )
        submit_diet = st.form_submit_button("Save Preferences")

# -----------------------
# Sidebar buttons
# -----------------------

col1, col2 = st.sidebar.columns(2)
with col1:
    generate_button = st.button("✨ Generate Plan")

if generate_button:
    clean_prompt = format_user_details(st.session_state.user_details)
    full_plan = handle_prompt(f"Give me a workout and diet plan for:\n\n{clean_prompt}")
    st.session_state["last_plan"] = full_plan
    st.session_state["pdf_bytes"] = export_pdf(full_plan)

with col2:
    st.download_button(
        label="📄 Download Plan",
        data=st.session_state.get("pdf_bytes", b""),  # Always use session_state bytes
        file_name="workout_diet_plan.pdf",
        mime="application/pdf",
        disabled=st.session_state.get("pdf_bytes") is None,
        key=f"download_plan_{time.time()}"  # dynamic key forces Streamlit to refresh
    )
# -----------------------
# Chat log Section
# -----------------------




# -----------------------
# User settings section
# -----------------------
st.sidebar.markdown("---")
col111, col222 = st.sidebar.columns(2)
with col111:
    progress_tracker_button = st.button("🛤️ Progress Tracker")
    
with col222:
    progress_check_button = st.button("📈 Progress Report")

if progress_check_button:
    st.session_state.page = "Progress"

if progress_tracker_button:
    st.session_state.page =  "Tracker"

if st.session_state.page == "Home" or st.session_state.page is None:
    show_home()

elif st.session_state.page == "Profile":
    show_profile_page()

elif st.session_state.page == "Progress":
    st.title("📈 Progress Report")
    st.info("Progress so Far!")
    show_progress = st.button("Show Progress")
    if show_progress:
        if st.session_state.progress_log:
            st.subheader("📊 Progress Log")
            st.table(st.session_state.progress_log)

            try:
                df = pd.DataFrame(st.session_state.progress_log)
                st.line_chart(df[["Workout (min)", "Calories Burned"]])
                st.write(st.session_state.progress_log["Notes"])
                st.subheader("📊 PR Progress Over Time")
                st.line_chart(df[["Bench PR", "Squat PR", "Deadlift PR"]])
            except Exception as e:
                st.error(f"Chart error: {e}")
        
        else:
            st.warning("⚠️ No progress tracked yet!")


# -----------------------
# Progress Tracker Page
# -----------------------
elif st.session_state.page == "Tracker":
    st.title("🛤️ Track Progress")
    st.info("You can track your progress here!")
   

    Day_Number = st.number_input("Day Number:", min_value=1, step=1)

    with st.form("progress_form"):
        workout_minutes = st.number_input("Workout Duration (min):", min_value=0, step=5)
        calories_burned = st.number_input("Calories Burned:", min_value=0, step=10)
        workout_routine = st.text_area("Additional Notes")
        st.subheader("Personal Records:")
        bench_pr = st.number_input("Bench Press Max 1RM: ", min_value= 0 )
        squat_pr = st.number_input("Squat Max 1RM: ",  min_value= 0)
        dead_pr = st.number_input("Deadlift Pr 1RM: ", min_value= 0)
        submit_tracker = st.form_submit_button("Save Progress")

        if submit_tracker:
            st.session_state.progress_log.append({
                "Day": int(Day_Number),
                "Workout (min)": int(workout_minutes),
                "Calories Burned": int(calories_burned),
                "Notes": workout_routine,
                "Bench PR": bench_pr,
                "Squat PR": squat_pr,
                "Deadlift PR": dead_pr,
                "Timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
            })
            st.success(f"✅ Progress saved for Day {int(Day_Number)}!")

        

# -----------------------
# Saving preferences
# -----------------------

if submit_diet:
    with st.spinner("💾 Saving..."):
        st.session_state.diet = {
            "Diet": diet,
            "Cuisine Preference": country,
            "Allergies": allergies if allergies else "None",
            "Foods Disliked": dislikes if dislikes else "None"
        }
        st.session_state.user_details["Diet"] = st.session_state.diet
        time.sleep(1)
        st.success("✅ Diet Preferences Saved!")

if submit_user_info:
    with st.spinner("💾 Saving..."):
        st.session_state.user_info = {
            "Gender": gender,
            "Age": age,
            "Weight": int(weight),
            "Height": f"{height_feet} ft {height_inches} in"
        }
        st.session_state.user_details["UserInfo"] = st.session_state.user_info
        time.sleep(1)
        st.success("✅ User details saved!")


if submit_workout_preferences:
    if not st.session_state.user_info:  
        st.error("⚠️ Please save user details first!")
    else:
        with st.spinner("💾 Saving..."):
            st.session_state.workout_preferences = {
                "Fitness Level": fitness_level,
                "Goal": goal,
                "Days per Week": days,
                "Duration": duration,
                "Equipment": equipment,
                "Workout Type": workout_type if workout_type else [],
                "Rest Days": rest_days if rest_days else []
            }
            st.session_state.user_details["Workout"] = st.session_state.workout_preferences
            time.sleep(1)
            st.success("✅ Workout preferences saved!")



# -----------------------
# Footer
# -----------------------
st.markdown("---")
st.caption("🚀 Built with Streamlit + Gemini | © 2025 FitForge AI")
