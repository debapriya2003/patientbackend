import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from datetime import datetime, timedelta
from pymongo import MongoClient
import random
import bcrypt
import io

# ---------------------- MongoDB Setup ----------------------
client = MongoClient("mongodb+srv://tintin:tintin@cluster0.qot4y.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0")
db = client["elderly_health_monitor"]
vitals_collection = db["vitals"]
users_collection = db["users"]  # New collection for user auth

# ---------------------- Authentication Functions ----------------------

def hash_password(password):
    # Hash password with bcrypt
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt())

def check_password(password, hashed):
    # Check password against hashed version
    return bcrypt.checkpw(password.encode(), hashed)

def signup(username, password):
    if users_collection.find_one({"username": username}):
        return False, "Username already exists."
    hashed_pw = hash_password(password)
    users_collection.insert_one({"username": username, "password": hashed_pw})
    return True, "User registered successfully."

def login(username, password):
    user = users_collection.find_one({"username": username})
    if user and check_password(password, user["password"]):
        return True, "Login successful."
    return False, "Invalid username or password."

# ---------------------- Sample Data Generation ----------------------

def generate_sample_vitals():
    now = datetime.now()
    time_range = [now - timedelta(hours=i) for i in range(23, -1, -1)]
    heart_rate = np.random.normal(loc=75, scale=5, size=24).round(1)
    systolic = np.random.normal(loc=120, scale=10, size=24).round(1)
    diastolic = np.random.normal(loc=80, scale=5, size=24).round(1)
    spo2 = np.random.normal(loc=98, scale=1, size=24).round(1)
    temperature = np.random.normal(loc=98.6, scale=0.5, size=24).round(1)

    return pd.DataFrame({
        "Timestamp": time_range,
        "Heart Rate (BPM)": heart_rate,
        "Systolic BP (mmHg)": systolic,
        "Diastolic BP (mmHg)": diastolic,
        "SpO2 (%)": spo2,
        "Temperature (F)": temperature
    })

# ---------------------- Insert 50 Random Vitals ----------------------

def insert_random_data():
    now = datetime.now()
    for i in range(50):
        timestamp = now - timedelta(minutes=random.randint(0, 1440))
        record = {
            "Timestamp": timestamp,
            "Heart Rate (BPM)": round(np.random.normal(75, 5), 1),
            "Systolic BP (mmHg)": round(np.random.normal(120, 10), 1),
            "Diastolic BP (mmHg)": round(np.random.normal(80, 5), 1),
            "SpO2 (%)": round(np.random.normal(98, 1), 1),
            "Temperature (F)": round(np.random.normal(98.6, 0.5), 1)
        }
        vitals_collection.insert_one(record)

# ---------------------- Load Data ----------------------

def load_data():
    data = list(vitals_collection.find())
    if data:
        df = pd.DataFrame(data)
        df["Timestamp"] = pd.to_datetime(df["Timestamp"])
        return df.sort_values("Timestamp")
    return generate_sample_vitals()

# ---------------------- Static Data ----------------------

medical_conditions = {
    "Diabetes": 1,
    "Hypertension": 1,
    "Arthritis": 0,
    "Asthma": 0,
    "Heart Disease": 1,
    "Others": 0
}

medication_schedule = [
    {"Medicine": "Aspirin", "Dosage": "75mg", "Time": "8:00 AM"},
    {"Medicine": "Metformin", "Dosage": "500mg", "Time": "12:00 PM"},
    {"Medicine": "Atorvastatin", "Dosage": "10mg", "Time": "8:00 PM"}
]

patient_profile = {
    "Name": "John Doe",
    "Age": 72,
    "Gender": "Male",
    "Blood Group": "B+",
    "Allergies": "None",
    "Emergency Contact": "Jane Doe (+1234567890)",
    "Address": "123 Elderly Lane, Healthville",
    "Assigned Doctor": "Dr. Smith, General Medicine"
}

# ---------------------- Streamlit App ----------------------

st.set_page_config(page_title="Elderly Health Monitor", layout="wide")

# Initialize session state variables for login
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "username" not in st.session_state:
    st.session_state.username = ""

def logout():
    st.session_state.logged_in = False
    st.session_state.username = ""

def show_login():
    st.title("🔐 Login to Elderly Health Monitor")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    if st.button("Login"):
        success, msg = login(username, password)
        if success:
            st.session_state.logged_in = True
            st.session_state.username = username
            st.success(msg)
        else:
            st.error(msg)
    st.markdown("---")
    st.write("Don't have an account? Please sign up below.")

def show_signup():
    st.title("📝 Sign Up for Elderly Health Monitor")
    new_username = st.text_input("Choose a Username", key="signup_user")
    new_password = st.text_input("Choose a Password", type="password", key="signup_pass")
    confirm_password = st.text_input("Confirm Password", type="password", key="signup_confirm")
    if st.button("Sign Up"):
        if new_password != confirm_password:
            st.error("Passwords do not match.")
        elif len(new_password) < 6:
            st.error("Password should be at least 6 characters.")
        else:
            success, msg = signup(new_username, new_password)
            if success:
                st.success(msg + " Please login now.")
            else:
                st.error(msg)
    st.markdown("---")
    if st.button("Back to Login"):
        st.session_state.show_signup = False

# Control flow for showing signup/login
if "show_signup" not in st.session_state:
    st.session_state.show_signup = False

if not st.session_state.logged_in:
    if st.session_state.show_signup:
        show_signup()
    else:
        show_login()
        if st.button("Create a new account"):
            st.session_state.show_signup = True

else:
    # Logged in: show the main dashboard
    st.title(f"🩺 Elderly Patient Health Dashboard — Welcome {st.session_state.username}")
    st.button("Logout", on_click=logout)

    # Sidebar form for adding new vital record
    st.sidebar.header("Add New Vital Record")
    with st.sidebar.form("input_form"):
        hr = st.number_input("Heart Rate (BPM)", min_value=40.0, max_value=180.0, value=75.0)
        sys = st.number_input("Systolic BP (mmHg)", min_value=80.0, max_value=200.0, value=120.0)
        dia = st.number_input("Diastolic BP (mmHg)", min_value=50.0, max_value=130.0, value=80.0)
        spo2 = st.number_input("SpO2 (%)", min_value=80.0, max_value=100.0, value=98.0)
        temp = st.number_input("Temperature (F)", min_value=95.0, max_value=105.0, value=98.6)
        submitted = st.form_submit_button("Submit")
        if submitted:
            vitals_collection.insert_one({
                "Timestamp": datetime.now(),
                "Heart Rate (BPM)": hr,
                "Systolic BP (mmHg)": sys,
                "Diastolic BP (mmHg)": dia,
                "SpO2 (%)": spo2,
                "Temperature (F)": temp
            })
            st.success("Record added successfully.")

    if st.sidebar.button("Insert 50 Random Records"):
        insert_random_data()
        st.sidebar.success("Inserted 50 random data points.")

    # Load vitals data
    vitals_df = load_data()
    if vitals_df.empty:
        st.warning("No vitals data available.")
    else:
        latest_vital = vitals_df.iloc[-1]

        # Patient Profile
        st.header("👤 Patient Profile")
        for key, value in patient_profile.items():
            st.markdown(f"**{key}:** {value}")

        # Real-time Vitals Metrics
        st.header("🔴 Real-time Vitals")
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Heart Rate", f"{latest_vital['Heart Rate (BPM)']} BPM")
        col2.metric("Blood Pressure", f"{latest_vital['Systolic BP (mmHg)']}/{latest_vital['Diastolic BP (mmHg)']} mmHg")
        col3.metric("SpO2", f"{latest_vital['SpO2 (%)']} %")
        col4.metric("Temperature", f"{latest_vital['Temperature (F)']} °F")

        # Medical History
        st.header("📋 Medical History")
        condition_df = pd.DataFrame.from_dict(medical_conditions, orient='index', columns=['Has Condition'])
        condition_df = condition_df.reset_index().rename(columns={'index': 'Condition'})
        pie_fig = px.pie(condition_df[condition_df['Has Condition'] == 1], names='Condition', title='Existing Medical Conditions')
        st.plotly_chart(pie_fig, use_container_width=True)

        # Medication Schedule
        st.header("💊 Medication Schedule")
        med_df = pd.DataFrame(medication_schedule)
        st.table(med_df)

        # Vitals Trend Graphs
        st.header("📈 Vitals Trend (All Records)")
        fig1 = px.line(vitals_df, x='Timestamp', y='Heart Rate (BPM)', title='Heart Rate Over Time', markers=True)
        fig2 = px.line(vitals_df, x='Timestamp', y=['Systolic BP (mmHg)', 'Diastolic BP (mmHg)'],
                       title='Blood Pressure Over Time', markers=True)
        fig3 = px.line(vitals_df, x='Timestamp', y='SpO2 (%)', title='SpO2 Over Time', markers=True)
        fig4 = px.line(vitals_df, x='Timestamp', y='Temperature (F)', title='Body Temperature Over Time', markers=True)
        fig5 = px.bar(vitals_df, x='Timestamp', y='Heart Rate (BPM)', title='Heart Rate Distribution')
        fig6 = px.area(vitals_df, x='Timestamp', y='Temperature (F)', title='Temperature Area Chart')

        st.plotly_chart(fig1, use_container_width=True)
        st.plotly_chart(fig2, use_container_width=True)
        st.plotly_chart(fig3, use_container_width=True)
        st.plotly_chart(fig4, use_container_width=True)
        st.plotly_chart(fig5, use_container_width=True)
        st.plotly_chart(fig6, use_container_width=True)

        # Download Data
        csv = vitals_df.to_csv(index=False).encode()
        st.download_button(label="📥 Download Vitals Data as CSV", data=csv, file_name='vitals_data.csv', mime='text/csv')
