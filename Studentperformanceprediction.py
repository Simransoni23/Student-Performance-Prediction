import streamlit as st
import pandas as pd
import numpy as np
import os
import joblib
import re
import matplotlib.pyplot as plt
import sqlite3
import datetime
import time


from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, confusion_matrix, ConfusionMatrixDisplay

import sqlite3
import datetime

# ---------------- DATABASE SETUP ----------------

DB_PATH = "student_app.db"

def get_connection():
    return sqlite3.connect(DB_PATH, check_same_thread=False)

conn = get_connection()
cursor = conn.cursor()

#----------------------Create tables---------------------------------
#user table
cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL
)
""")

#prediction history table
cursor.execute("""
CREATE TABLE IF NOT EXISTS predictions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL,
    study_hours INTEGER,
    attendance INTEGER,
    sleep_hours INTEGER,
    predicted_grade TEXT,
    timestamp TEXT
)
""")

conn.commit()

# Dataset upload table
cursor.execute("""
CREATE TABLE IF NOT EXISTS datasets (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    filename TEXT,
    upload_time TEXT
)
""")

conn.commit()

# ---------------- PAGE CONFIGURATION ----------------
st.set_page_config(
    page_title="🎓 Student Performance Prediction",
    page_icon="📊",
    layout="wide"
)

MODEL_PATH = "outputs/student_model.pkl"

# ---------------- TITLE ----------------
st.title("🎓 Student Performance Prediction")
st.caption("Machine Learning Interactive Dashboard")

# ---------------- TRAIN MODEL ----------------
def train_and_save_model(df):
    X = df.drop("Grade", axis=1)
    y = df["Grade"]

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=32
    )

    model = RandomForestClassifier()
    model.fit(X_train, y_train)

    # Save model
    os.makedirs("outputs", exist_ok=True)
    joblib.dump(model, MODEL_PATH)

    # Accuracy
    y_pred = model.predict(X_test)
    acc = accuracy_score(y_test, y_pred)

    return model, acc, X_test, y_test, y_pred

# ---------------- SESSION ----------------
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.username = ""


# ---------------- VALIDATION FUNCTIONS ----------------

def validate_username(username):

    if username.strip() == "":
        return "Username cannot be empty"

    if len(username) < 4:
        return "Username must be at least 4 characters"

    if not re.match("^[A-Za-z0-9_]+$", username):
        return "Username can contain only letters, numbers and underscore"

    return None


def validate_password(password):

    if password.strip() == "":
        return "Password cannot be empty"

    if len(password) < 6:
        return "Password must be at least 6 characters"

    if not re.search("[A-Z]", password):
        return "Password must contain at least one uppercase letter"

    if not re.search("[a-z]", password):
        return "Password must contain at least one lowercase letter"

    if not re.search("[0-9]", password):
        return "Password must contain at least one number"

    return None


# ---------------- REGISTER FUNCTION ----------------

def register_user(username, password):

    try:
        cursor.execute(
            "INSERT INTO users(username, password) VALUES (?, ?)",
            (username, password)
        )

        conn.commit()
        return True

    except sqlite3.IntegrityError:
        return False


# ---------------- LOGIN FUNCTION ----------------

# ---------------- RESET PASSWORD FUNCTION ----------------

def reset_password(username, new_password):

    cursor.execute(
        "SELECT * FROM users WHERE username=?",
        (username,)
    )

    user = cursor.fetchone()

    if user:

        cursor.execute(
            "UPDATE users SET password=? WHERE username=?",
            (new_password, username)
        )

        conn.commit()

        return True

    return False

def login_user(username, password):

    if username.strip() == "" or password.strip() == "":
        return None

    cursor.execute(
        "SELECT * FROM users WHERE username=? AND password=?",
        (username, password)
    )

    user = cursor.fetchone()

    return user

# ---------------- LOGIN PAGE ----------------

if not st.session_state.logged_in:

    st.subheader("🔐 Student Login System")

    tab1, tab2, tab3 = st.tabs(["Login", "Register", "Forget Password"])

    # ---------------- LOGIN TAB ----------------

    with tab1:

        user = st.text_input("Username")
        pwd = st.text_input("Password", type="password")

        if st.button("Login"):

            if user.strip() == "" or pwd.strip() == "":
                st.warning("⚠️ Please fill all fields")

            else:

                if login_user(user, pwd):

                    st.session_state.logged_in = True
                    st.session_state.username = user

                    st.success("✅ Login successful")
                    st.rerun()

                else:
                    st.error("❌ Invalid username or password")

    # ---------------- REGISTER TAB ----------------

    with tab2:

      success_placeholder = st.empty()

      with st.form("register_form", clear_on_submit=True):

        new_user = st.text_input("New Username")

        new_pwd = st.text_input(
            "New Password",
            type="password"
        )

        confirm_pwd = st.text_input(
            "Confirm Password",
            type="password"
        )

        register_btn = st.form_submit_button("Register")

        if register_btn:

            # Username validation
            username_error = validate_username(new_user)

            if username_error:
                st.error(f"❌ {username_error}")

            else:

                # Password validation
                password_error = validate_password(new_pwd)

                if password_error:
                    st.error(f"❌ {password_error}")

                elif new_pwd != confirm_pwd:
                    st.error("❌ Passwords do not match")

                else:

                    if register_user(new_user, new_pwd):

                        success_placeholder.success(
                            "✅ Registered successfully"
                        )
                        #show for 2 seconds
                        time.sleep(2)
                        #remove message
                        success_placeholder.empty()

                    else:
                        st.error("❌ Username already exists")
 
    # ---------------- FORGOT PASSWORD TAB ----------------

    with tab3:

       #st.subheader("🔑 Reset Password")
       reset_placeholder = st.empty()

       with st.form("forgot_password_form", clear_on_submit=True):

        forgot_user = st.text_input("Enter Username")

        new_pass = st.text_input(
            "New Password",
            type="password"
        )

        confirm_new_pass = st.text_input(
            "Confirm New Password",
            type="password"
        )

        reset_btn = st.form_submit_button("Reset Password")

        if reset_btn:

            # Username validation
            username_error = validate_username(forgot_user)

            if username_error:
                st.error(f"❌ {username_error}")

            else:

                # Password validation
                password_error = validate_password(new_pass)

                if password_error:
                    st.error(f"❌ {password_error}")

                elif new_pass != confirm_new_pass:
                    st.error("❌ Passwords do not match")

                else:

                    if reset_password(forgot_user, new_pass):

                        reset_placeholder.success("✅ Password reset successful")
                        #show for 2 seconds
                        time.sleep(2)
                        #remove message
                        reset_placeholder.empty()
                    else:
                        st.error("❌ Username not found")

    st.stop()

# ---------------- SIDEBAR ----------------
st.sidebar.header("⚙️ Navigation")

page = st.sidebar.radio(
    "Go to",
    ["Home", "Dataset Overview", "Predict Student Performance", "Prediction History"]
)

st.sidebar.write(f"👤 Logged in as: {st.session_state.username}")

if st.sidebar.button("Logout"):
    st.session_state.logged_in = False
    st.rerun()

# ---------------- HOME ----------------
if page == "Home":
    
    st.info("👈 Upload dataset and train model from Dataset Overview")


# ---------------- DATASET OVERVIEW ----------------

elif page == "Dataset Overview":

    st.subheader("📂 Dataset Explorer")


    # ---------------- REFRESH BUTTON ----------------

    if st.button("🔄 Refresh Dataset Page"):

        st.rerun()


    # ---------------- FILE UPLOADER ----------------

    uploaded_file = st.file_uploader(
        "Upload CSV file",
        type=["csv"]
    )


    # ---------------- UPLOAD PROCESS ----------------

    if uploaded_file is not None:

        df = pd.read_csv(uploaded_file)


        os.makedirs("uploaded_datasets", exist_ok=True)

        file_path = os.path.join(
            "uploaded_datasets",
            uploaded_file.name
        )

        with open(file_path, "wb") as f:
            f.write(uploaded_file.getbuffer())


        cursor.execute("""
        INSERT INTO datasets(filename, upload_time)
        VALUES (?, ?)
        """, (

            uploaded_file.name,

            datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        ))

        conn.commit()


        st.success("✅ Dataset uploaded successfully")

        st.subheader("📄 Uploaded File Preview")

        st.dataframe(df.head(), use_container_width=True)


        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric("Rows", df.shape[0])

        with col2:
            st.metric("Columns", df.shape[1])

        with col3:
            st.metric("Missing Values", df.isnull().sum().sum())


        st.write("🧾 Columns:", df.columns.tolist())


        # ---------------- TRAIN MODEL ----------------

        if st.button("🚀 Train Model"):

            model, acc, X_test, y_test, y_pred = train_and_save_model(df)

            st.success("✅ Model trained successfully")

            st.metric("Accuracy", f"{acc * 100:.2f}%")


            # Confusion Matrix
            fig, ax = plt.subplots()

            cm = confusion_matrix(y_test, y_pred)

            ConfusionMatrixDisplay(cm).plot(ax=ax)

            st.pyplot(fig)


            # Download Model
            with open(MODEL_PATH, "rb") as file:

                st.download_button(
                    "⬇ Download Model",
                    file,
                    file_name="student_model.pkl",
                    mime="application/octet-stream"
                )


    # ---------------- STORED DATASETS ----------------

    st.markdown("---")
    st.subheader("💾 Stored Datasets")

    cursor.execute("""
    SELECT id, filename, upload_time
    FROM datasets
    ORDER BY id DESC
    """)

    dataset_rows = cursor.fetchall()


    if dataset_rows:

        dataset_df = pd.DataFrame(

            dataset_rows,

            columns=["ID", "Filename", "Upload Time"]
        )

        st.dataframe(dataset_df, use_container_width=True)


        # ---------------- OPEN DATASET ----------------

        st.subheader("📖 Open Stored Dataset")

        selected_dataset = st.selectbox(
            "Select Dataset",
            dataset_df["Filename"]
        )


        file_path = os.path.join(
            "uploaded_datasets",
            selected_dataset
        )


        if os.path.exists(file_path):

            open_df = pd.read_csv(file_path)

            st.subheader("📄 Dataset Preview")

            st.dataframe(open_df, use_container_width=True)

            col1, col2, col3 = st.columns(3)

            with col1:
                st.metric("Rows", open_df.shape[0])

            with col2:
                st.metric("Columns", open_df.shape[1])

            with col3:
                st.metric("Missing Values", open_df.isnull().sum().sum())

            st.write("🧾 Columns:", open_df.columns.tolist())


        # ---------------- DELETE DATASET ----------------

        st.subheader("🗑 Delete Dataset")

        dataset_id = st.number_input(
            "Enter Dataset ID",
            min_value=1,
            step=1
        )


        if st.button("Delete Dataset"):

            cursor.execute(
                "DELETE FROM datasets WHERE id=?",
                (dataset_id,)
            )

            conn.commit()

            st.success("✅ Dataset deleted successfully")

            st.rerun()


    else:

        st.info("No datasets stored yet.")


# ---------------- PREDICTION ------------------------------------

elif page == "Predict Student Performance":

    st.subheader("🎯 Predict Student Performance")

    # CHECK MODEL EXISTS
    if not os.path.exists(MODEL_PATH):

        st.error("❌ No trained model found.")
        st.info(
            "👉 First upload dataset and train model from Dataset Overview"
        )

    else:

        # LOAD MODEL
        model = joblib.load(MODEL_PATH)

        st.write("Enter student details:")

#----------Refresh Button-----------------------
        if st.button("♻ Refresh"):
        
           st.session_state.study_hours = 0
           st.session_state.attendance = 0
           st.session_state.sleep_hours = 0

           st.rerun()

        # ---------------- GRADE CRITERIA ----------------

        st.info("""
        📘 Grade Prediction Criteria

        ✅ Grade A
        • Study Hours → 8 to 24 hrs
        • Attendance → 85% to 100%
        • Sleep Hours → 6 to 8 hrs

        ✅ Grade B
        • Study Hours → 5 to 7 hrs
        • Attendance → 70% to 84%
        • Sleep Hours → 5 to 8 hrs

        ✅ Grade C
        • Study Hours → 0 to 4 hrs
        • Attendance → Below 70%
        • Sleep Hours → Less than 5 hrs
        """)

        # ---------------- USER INPUTS ---------------------

    study_hours = st.number_input(
       "📚 Study Hours",
       min_value=0,
       max_value=24,
       step=1,
       key="study_hours",
       help="Study hours cannot be greater than 24"
    )

# VALIDATION MESSAGE
    if study_hours >= 24:

       st.warning(
         "⚠ Study hours cannot be greater than 24"
     )


    attendance = st.number_input(
      "📝 Attendance (%)",
      min_value=0,
      max_value=100,
      step=1,
      key="attendance",
      help="Attendance cannot be greater than 100%"
    )

# VALIDATION MESSAGE
    if attendance >= 100:

      st.warning(
        "⚠ Attendance cannot be greater than 100%"
      )


    sleep_hours = st.number_input(
      "😴 Sleep Hours",
      min_value=0,
      max_value=24,
      step=1,
      key="sleep_hours",
      help="Sleep hours cannot be greater than 24"
    )

# VALIDATION MESSAGE
    if sleep_hours >= 24:

      st.warning(
        "⚠ Sleep hours cannot be greater than 24"
      )

        # ---------------- INPUT DATAFRAME ----------------

    input_df = pd.DataFrame({

            "StudyHours": [study_hours],

            "Attendance": [attendance],

            "SleepHours": [sleep_hours]
        })

        # ---------------- PREDICT BUTTON ----------------

    if st.button("🔮 Predict"):

            # ---------------- VARIABLES ----------------

            score = 0

            grade_info = ""

            study_status = ""
            attendance_status = ""
            sleep_status = ""

            improvement_tips = []

            # ---------------- STUDY HOURS ANALYSIS ----------------

            if study_hours >= 8:

                score += 1

                study_status = "Excellent"

            elif study_hours >= 5:

                study_status = "Average"

                improvement_tips.append(
                    "📚 Increase study hours for Grade A"
                )

            else:

                study_status = "Poor"

                improvement_tips.append(
                    "📚 Study at least 5-8 hours daily"
                )

            # ---------------- ATTENDANCE ANALYSIS ----------------

            if attendance >= 85:

                score += 1

                attendance_status = "Excellent"

            elif attendance >= 70:

                attendance_status = "Average"

                improvement_tips.append(
                    "📝 Improve attendance above 85%"
                )

            else:

                attendance_status = "Poor"

                improvement_tips.append(
                    "📝 Attendance is very low"
                )

            # ---------------- SLEEP HOURS ANALYSIS ----------------

            if 6 <= sleep_hours <= 8:

                score += 1

                sleep_status = "Excellent"

            elif 5 <= sleep_hours < 6:

                sleep_status = "Average"

                improvement_tips.append(
                    "😴 Sleep at least 6-8 hours"
                )

            else:

                sleep_status = "Poor"

                improvement_tips.append(
                    "😴 Maintain proper sleep routine"
                )

            # ---------------- FINAL GRADE ----------------

            if score == 3:

                grade_info = "A"

            elif score == 2:

                grade_info = "B"

            else:

                grade_info = "C"

            # ---------------- MODEL PREDICTION ----------------

            pred = model.predict(input_df)[0]

            # ---------------- CURRENT TIME ----------------

            current_time = datetime.datetime.now().strftime(
                "%Y-%m-%d %H:%M:%S"
            )

            # ---------------- SAVE HISTORY ----------------

            cursor.execute("""
            INSERT INTO predictions
            (
                username,
                study_hours,
                attendance,
                sleep_hours,
                predicted_grade,
                timestamp
            )

            VALUES (?, ?, ?, ?, ?, ?)
            """, (

                st.session_state.username,

                int(study_hours),

                int(attendance),

                int(sleep_hours),

                grade_info,

                current_time
            ))

            conn.commit()

            # ---------------- RESULT ----------------

            st.success(
                f"🎯 Predicted Grade: {grade_info}"
            )

            st.info(
                f"⭐ Performance Score: {score}/3"
            )

            # ---------------- PERFORMANCE ANALYSIS ----------------

            st.subheader("📊 Performance Analysis")

            col1, col2, col3 = st.columns(3)

            with col1:

                st.metric(
                    "📚 Study Hours",
                    study_status
                )

            with col2:

                st.metric(
                    "📝 Attendance",
                    attendance_status
                )

            with col3:

                st.metric(
                    "😴 Sleep Hours",
                    sleep_status
                )

            # ---------------- PERFORMANCE MESSAGE ----------------

            if grade_info == "A":

                st.balloons()

                st.success("""
                🌟 Excellent Performance

                ✔ Outstanding consistency
                ✔ Excellent attendance
                ✔ Healthy lifestyle
                """)

            elif grade_info == "B":

                st.info("""
                👍 Good Performance

                ✔ Student is performing well
                ✔ Minor improvements needed
                """)

            else:

                st.warning("""
                ⚠ Needs Improvement

                ✔ Student performance is below average
                ✔ Focus more on consistency
                """)

            # ---------------- IMPROVEMENT SUGGESTIONS ----------------

            st.subheader("💡 Improvement Suggestions")

            if len(improvement_tips) == 0:

                st.success(
                    "✅ Excellent performance, no major improvements needed"
                )

            else:

                for tip in improvement_tips:

                    st.write(tip)

          
# ---------------- HISTORY ----------------
if page == "Prediction History":
    st.subheader("📜 Your Prediction History")

    cursor.execute("""
        SELECT study_hours, attendance, sleep_hours, predicted_grade, timestamp
        FROM predictions
        WHERE username=?
        ORDER BY id DESC
    """, (st.session_state.username,))

    rows = cursor.fetchall()

    if rows:
        history_df = pd.DataFrame(rows, columns=[
            "Study Hours",
            "Attendance",
            "Sleep Hours",
            "Predicted Grade",
            "Time"
        ])
        st.dataframe(history_df, use_container_width=True)
    else:
        st.info("No prediction history found.")

# ---------------- FOOTER ----------------
st.markdown("---")
st.caption("Developed by Simran Soni | Student Performance ML Project")