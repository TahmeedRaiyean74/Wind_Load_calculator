import streamlit as st
import pandas as pd
import numpy as np

# Page Configuration
st.set_page_config(
    page_title="Wind Load Generator | BNBC 2020 & ASCE 7",
    page_icon="⚡",
    layout="wide"
)

st.title("⚡ Automated Wind Load Calculator & Generator")
st.markdown("**BNBC 2020 / ASCE 7 Compliant** — Compute design wind pressures, gust effect factors, and story forces programmatically.")

# Sidebar Inputs for Building Parameters
st.sidebar.header("Building & Site Parameters")

code_standard = st.sidebar.selectbox("Design Standard", ["BNBC 2020", "ASCE 7-16"])
V = st.sidebar.number_input("Basic Wind Speed, V (m/s)", min_value=20.0, max_value=100.0, value=43.0, step=1.0)
terrain_cat = st.sidebar.selectbox("Terrain Category", ["Category A (Urban/Suburban)", "Category B (Open Terrain)", "Category C (Flat, Open Country)"])
importance_factor = st.sidebar.selectbox("Importance Category (Occupancy)", ["Category I (Low Risk) - 0.87", "Category II (Standard) - 1.00", "Category III/IV (High Risk) - 1.15"])

# Extract numeric value for importance factor
I_val = float(importance_factor.split("-")[-1].strip())

st.sidebar.header("Structure Geometry")
num_stories = st.sidebar.slider("Number of Stories", min_value=1, max_value=40, value=10)
story_height = st.sidebar.number_input("Typical Story Height (m)", min_value=2.5, max_value=6.0, value=3.0)
bldg_width = st.sidebar.number_input("Building Width (B in m)", min_value=5.0, max_value=100.0, value=20.0)
bldg_depth = st.sidebar.number_input("Building Depth (L in m)", min_value=5.0, max_value=100.0, value=30.0)

# Main Calculation Logic
if st.button("Generate Wind Load Profile", type="primary"):
    
    # Generate height profile
    heights = [i * story_height for i in range(1, num_stories + 1)]
    
    # Terrain coefficients approximation based on category
    if "A" in terrain_cat:
        alpha, zg = 9.5, 365
    elif "B" in terrain_cat:
        alpha, zg = 7.0, 274
    else:
        alpha, zg = 11.5, 500

    # Pressure calculations (Simplified exposure coefficient Kz and Velocity Pressure qz)
    # qz = 0.613 * Kz * Kzt * Kd * Ke * V^2 (N/m^2)
    Kd = 0.85 # Directionality factor
    Kzt = 1.0 # Topographic factor
    
    qz_list = []
    forces_list = []
    
    for z in heights:
        # Limit z to zg
        z_eff = max(4.5, min(z, zg))
        Kz = 2.01 * (z_eff / zg)**(2 / alpha)
        qz = 0.613 * Kz * Kzt * Kd * V**2 * I_val # N/m^2
        qz_kpa = qz / 1000.0 # Convert to kN/m2
        
        # Gust effect factor (G ~ 0.85 for rigid structures)
        G = 0.85
        # Net pressure coefficient (Cp) ~ 0.8 (windward) - 0.5 (leeward) = 1.3 combined approx
        Cp = 1.3
        
        # Design wind pressure p = qz * G * Cp (kN/m2)
        p = qz_kpa * G * Cp 
        
        # Tributary area force per story (approximate uniform width)
        story_force = p * bldg_width * story_height # kN
        
        qz_list.append(round(qz_kpa, 3))
        forces_list.append(round(story_force, 2))

    # Construct DataFrame
    df_results = pd.DataFrame({
        "Story": [f"Story {i}" for i in range(1, num_stories + 1)],
        "Height (m)": heights,
        "Velocity Pressure qz (kN/m²)": qz_list,
        "Story Shear Force (kN)": forces_list
    })

    st.success("Wind load analysis completed successfully!")
    
    # Display metrics
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Base Shear", f"{sum(forces_list):,.2f} kN")
    col2.metric("Max Story Force", f"{max(forces_list):,.2f} kN")
    col3.metric("Roof Height", f"{heights[-1]} m")

    # Display Table
    st.subheader("Story-by-Story Wind Load Distribution")
    st.dataframe(df_results, use_container_width=True)

    # Plot chart
    st.subheader("Wind Force Distribution Across Building Height")
    chart_data = pd.DataFrame({
        "Force (kN)": forces_list,
        "Height (m)": heights
    })
    st.line_chart(chart_data, x="Force (kN)", y="Height (m)")

    # CSV Download
    csv = df_results.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="Download Wind Load Report (CSV)",
        data=csv,
        file_name='wind_load_profile_report.csv',
        mime='text/csv',
    )