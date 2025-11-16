import os
import time
import streamlit as st
import pandas as pd
import plotly.express as px
from streamlit_autorefresh import st_autorefresh

# --- 1. Configuration and Setup ---

# Set wide layout and a clean title
st.set_page_config(
    page_title="Professional Energy Dashboard",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Constants
CSV_FILE = "energy_log.csv"
API_ENDPOINT = "https://api.example.com/device/control" # Fictional API Endpoint for demonstration

# Initialize session state for device control persistence
if 'device_status' not in st.session_state:
    st.session_state.device_status = 'OFF'
if 'last_api_call' not in st.session_state:
    st.session_state.last_api_call = time.time()

# --- 2. API Simulation Function ---

def control_device_api(new_state: str) -> bool:
    """
    Simulates calling an external API (e.g., a REST endpoint)
    to change the device state.

    Args:
        new_state: The target state ('ON' or 'OFF').

    Returns:
        True if the API call was successful, False otherwise.
    """
    # In a real application, you would use 'requests.post' here:
    # try:
    #     response = requests.post(API_ENDPOINT, json={"state": new_state})
    #     response.raise_for_status()
    #     st.session_state.device_status = new_state
    #     return True
    # except Exception:
    #     return False

    # Simulation Logic
    st.session_state.device_status = new_state
    st.session_state.last_api_call = time.time()
    return True # Always simulate success for the demo

# --- 3. Data Loading (Cached for performance) ---

@st.cache_data(ttl=5) # TTL will be updated by the sidebar slider, but 5 is a safe default
def load_data(refresh_interval):
    """Loads and preprocesses the energy log data."""
    if not os.path.exists(CSV_FILE):
        # Return an empty DataFrame structure if the file doesn't exist
        return pd.DataFrame(columns=[
            "Timestamp", "Voltage (V)", "Current (A)", "Power (W)", "Energy (kWh)", "Status"
        ])

    try:
        df = pd.read_csv(CSV_FILE)

        # Basic data validation and type conversion
        df["Timestamp"] = pd.to_datetime(df["Timestamp"], errors="coerce", infer_datetime_format=True)
        df = df.dropna(subset=["Timestamp"])
       
        # Ensure numeric types for core columns
        numeric_cols = ["Voltage (V)", "Current (A)", "Power (W)", "Energy (kWh)"]
        for col in numeric_cols:
             df[col] = pd.to_numeric(df[col], errors='coerce')

        # Sort by timestamp and drop duplicates
        df = df.drop_duplicates(subset=["Timestamp"], keep='last').sort_values("Timestamp").reset_index(drop=True)

        return df
    except Exception as e:
        st.error(f"Error loading or parsing CSV data: {e}")
        return pd.DataFrame(columns=[
            "Timestamp", "Voltage (V)", "Current (A)", "Power (W)", "Energy (kWh)", "Status"
        ])

# --- 4. Sidebar Controls and Auto-refresh ---

with st.sidebar:
    st.header("Dashboard Settings")
    # Using a key helps ensure state stability with autorefresh
    refresh_interval = st.slider("Auto-refresh interval (seconds)", 2, 30, 5, key="refresh_slider")
    st.info(f"Data refresh every **{refresh_interval} seconds**.")
   
    # NEW: Cost Input for BDT/kWh
    st.markdown("---")
    st.subheader("Billing Configuration")
    # Defaulting to a realistic BDT rate (e.g., 7.5 BDT/kWh)
    cost_per_kwh = st.number_input(
        "Energy Cost per Unit (BDT/kWh)",
        min_value=0.01,
        value=7.50,
        step=0.1,
        format="%.2f",
        help="Enter the Bangladesh Taka (BDT) cost for 1 kilowatt-hour (kWh)."
    )
    # Store the cost in session state for easy access in the main body
    st.session_state.cost_per_kwh = cost_per_kwh
    st.markdown("---")

# Auto-refresh trigger
st_autorefresh(interval=refresh_interval * 1000, key="auto_refresh_trigger")


# --- 5. Device Control UI ---

st.title("⚡ Smart Energy Monitoring Dashboard")

col_control, col_status = st.columns([1, 4])

with col_control:
    current_status = st.session_state.device_status
    is_on = current_status == 'ON'
   
    # Custom button appearance based on state
    button_label = f"Turn {'OFF' if is_on else 'ON'} Device"
    button_style = "primary" if not is_on else "secondary"

    # Action handler for the button
    def handle_toggle():
        # Determine the target state
        new_state = 'OFF' if is_on else 'ON'
       
        # Call the simulated API
        success = control_device_api(new_state)
       
        # Show a toast notification for feedback
        if success:
            st.toast(f"API Success: Device switched to {new_state}!", icon='✅')
        else:
            st.toast("API Error: Failed to change device state.", icon='❌')
   
    # Display the prominent control button
    st.button(
        button_label,
        on_click=handle_toggle,
        type=button_style,
        use_container_width=True,
        help=f"Calls the control API to switch the device {'OFF' if is_on else 'ON'}."
    )

with col_status:
    # Display status with colors
    if is_on:
        st.success(f"**DEVICE ONLINE** | Last Action: {time.strftime('%H:%M:%S', time.localtime(st.session_state.last_api_call))}")
    else:
        st.error(f"**DEVICE OFFLINE** | Last Action: {time.strftime('%H:%M:%S', time.localtime(st.session_state.last_api_call))}")

st.markdown("---")

# --- 6. Data Loading and Visualization ---
df = load_data(refresh_interval)

if df.empty or len(df) < 2:
    st.info("Waiting for data or not enough data points (min 2 required) to plot historical charts. Ensure 'energy_log.csv' is being written.")
else:
   
    # 6.1. Real-Time Metrics Display
    latest = df.iloc[-1]
   
    st.subheader("Real-Time Metrics")
   
    col1, col2, col3, col4 = st.columns(4)
   
    # Calculate delta for Power and Energy (change from the second-to-last reading)
    power_delta = df['Power (W)'].iloc[-1] - df['Power (W)'].iloc[-2]
    energy_delta = df['Energy (kWh)'].iloc[-1] - df['Energy (kWh)'].iloc[-2]

    # Metrics with delta indicators for change
    col1.metric("Voltage (V)", f"{latest['Voltage (V)']:.1f}")
    col2.metric("Current (A)", f"{latest['Current (A)']:.3f}")
    col3.metric("Power (W)", f"{latest['Power (W)']:.1f}", delta=f"{power_delta:.1f} W")
    col4.metric("Energy (kWh)", f"{latest['Energy (kWh)']:.3f}", delta=f"{energy_delta:.3f} kWh")

    st.markdown("---")

    # 6.2. Time Series Plots (Using dark theme for professional look)
    st.subheader("Historical Trends")

    # Power Chart (Primary focus)
    fig_power = px.line(df, x="Timestamp", y="Power (W)",
                        title="Power Consumption Over Time (W)",
                        labels={"Power (W)": "Power (W)", "Timestamp": "Time"},
                        template="plotly_dark", # Sleek dark theme
                        line_shape='spline' # Smoother line
                       )
    fig_power.update_traces(line=dict(width=3, color='#4CAF50')) # Green line for emphasis
    fig_power.update_layout(hovermode="x unified")
    st.plotly_chart(fig_power, use_container_width=True)

    col_a, col_b = st.columns(2)
    with col_a:
        # Voltage Chart
        fig_voltage = px.line(df, x="Timestamp", y="Voltage (V)",
                              title="Voltage Stability Trend (V)",
                              template="plotly_dark",
                              line_shape='spline'
                             )
        fig_voltage.update_traces(line=dict(width=2, color='#2196F3')) # Blue line
        fig_voltage.update_layout(hovermode="x unified")
        st.plotly_chart(fig_voltage, use_container_width=True)
   
    with col_b:
        # Current Chart
        fig_current = px.line(df, x="Timestamp", y="Current (A)",
                              title="Current Load Trend (A)",
                              template="plotly_dark",
                              line_shape='spline'
                             )
        fig_current.update_traces(line=dict(width=2, color='#FF9800')) # Orange line
        fig_current.update_layout(hovermode="x unified")
        st.plotly_chart(fig_current, use_container_width=True)

    st.markdown("---")

    # 6.3. Consumption Summary and Data Table
    st.subheader("Consumption Summary")
   
    total_energy = df["Energy (kWh)"].max()
    max_power = df["Power (W)"].max()

    # Retrieve cost per kWh from session state (set in the sidebar)
    current_cost_per_kwh = st.session_state.get('cost_per_kwh', 7.50)
    total_cost_bdt = total_energy * current_cost_per_kwh
   
    # Expanded columns to accommodate the new cost metric
    col_summary_1, col_summary_2, col_summary_3 = st.columns(3)
   
    col_summary_1.metric("Total Accumulated Energy (kWh)", f"{total_energy:.3f} kWh")
    col_summary_2.metric("Peak Power Recorded (W)", f"{max_power:.1f} W")
    # NEW: Display Total Cost in BDT
    col_summary_3.metric("Estimated Total Cost (BDT)", f"৳ {total_cost_bdt:,.2f}")
   
    st.markdown("### Recent Data Log")
    st.dataframe(df.tail(10), use_container_width=True, hide_index=True)