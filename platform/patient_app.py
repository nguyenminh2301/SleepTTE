"""
Patient-Facing Sleep Monitoring Application
Streamlit web app for sleep tracking and personalized brain health insights
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from pathlib import Path
import os
import sys
sys.path.append(str(Path(__file__).parent.parent))

from src.data.utils import load_config
from src.utils.event_logger import log_event
from demo_data import generate_demo_sleep_features
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
DEMO_MODE = os.getenv("DEMO_MODE", "0").lower() in {"1", "true", "yes"}

# Page configuration
st.set_page_config(
    page_title="Sleep & Brain Health Monitor",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #1f77b4;
    }
    .risk-high {
        color: #d62728;
        font-weight: bold;
    }
    .risk-moderate {
        color: #ff7f0e;
        font-weight: bold;
    }
    .risk-low {
        color: #2ca02c;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)


def load_patient_data(patient_id):
    """Load patient sleep and brain health data"""
    # In production, load from secure database
    # For demo, load from processed files
    try:
        sleep_features = pd.read_csv('data/processed/sleep_features.csv')
        patient_sleep = sleep_features[sleep_features['participant_id'] == patient_id].iloc[0]
        return patient_sleep.to_dict()
    except:
        if not DEMO_MODE:
            return None
        demo_df = generate_demo_sleep_features(n_patients=30)
        match = demo_df[demo_df["participant_id"] == patient_id]
        if match.empty:
            return demo_df.iloc[0].to_dict()
        return match.iloc[0].to_dict()


def calculate_risk_score(patient_data):
    """Calculate personalized brain aging risk score"""
    # Simplified risk calculation
    # In production, use trained model
    
    risk_factors = 0
    
    # Sleep efficiency
    if patient_data.get('sleep_efficiency', 100) < 80:
        risk_factors += 2
    elif patient_data.get('sleep_efficiency', 100) < 85:
        risk_factors += 1
    
    # Sleep fragmentation
    if patient_data.get('sleep_fragmentation_index', 0) > 20:
        risk_factors += 2
    elif patient_data.get('sleep_fragmentation_index', 0) > 10:
        risk_factors += 1
    
    # Circadian regularity
    if patient_data.get('sleep_regularity_index', 100) < 60:
        risk_factors += 2
    elif patient_data.get('sleep_regularity_index', 100) < 75:
        risk_factors += 1
    
    # Social jet lag
    if patient_data.get('social_jet_lag', 0) > 3:
        risk_factors += 2
    elif patient_data.get('social_jet_lag', 0) > 2:
        risk_factors += 1
    
    # Normalize to 0-1 scale
    risk_score = min(risk_factors / 8, 1.0)
    
    return risk_score


def get_risk_category(risk_score):
    """Categorize risk level"""
    if risk_score >= 0.67:
        return "High", "risk-high", "#d62728"
    elif risk_score >= 0.33:
        return "Moderate", "risk-moderate", "#ff7f0e"
    else:
        return "Low", "risk-low", "#2ca02c"


def plot_sleep_quality_gauge(sleep_efficiency):
    """Create gauge chart for sleep quality"""
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=sleep_efficiency,
        title={'text': "Sleep Efficiency"},
        gauge={
            'axis': {'range': [None, 100]},
            'bar': {'color': "darkblue"},
            'steps': [
                {'range': [0, 70], 'color': "lightcoral"},
                {'range': [70, 85], 'color': "lightyellow"},
                {'range': [85, 100], 'color': "lightgreen"}
            ],
            'threshold': {
                'line': {'color': "red", 'width': 4},
                'thickness': 0.75,
                'value': 85
            }
        }
    ))
    
    fig.update_layout(height=300)
    return fig


def plot_circadian_rhythm(patient_data):
    """Plot circadian rhythm metrics"""
    metrics = {
        'Interdaily Stability': patient_data.get('interdaily_stability', 0.5),
        'Relative Amplitude': patient_data.get('relative_amplitude', 0.7),
        'Sleep Regularity Index': patient_data.get('sleep_regularity_index', 75) / 100
    }
    
    fig = go.Figure(data=[
        go.Bar(
            x=list(metrics.values()),
            y=list(metrics.keys()),
            orientation='h',
            marker=dict(color='steelblue')
        )
    ])
    
    fig.update_layout(
        title="Circadian Health Metrics",
        xaxis_title="Score",
        height=300,
        template="plotly_white"
    )
    
    return fig


def main():
    """Main application"""
    if DEMO_MODE:
        st.sidebar.caption("Demo mode enabled")
    
    # Header
    st.markdown('<div class="main-header">🧠 Sleep & Brain Health Monitor</div>', unsafe_allow_html=True)
    
    # Sidebar - Patient Selection
    st.sidebar.title("Patient Portal")
    
    # In production, use authentication
    patient_id = st.sidebar.text_input("Patient ID", value="P0001")
    
    if st.sidebar.button("Load My Data"):
        patient_data = load_patient_data(patient_id)
        
        if patient_data:
            st.session_state['patient_data'] = patient_data
            st.sidebar.success(f"✓ Data loaded for {patient_id}")
            log_event(
                event_type="patient_data_loaded",
                source="patient_app",
                user_id=patient_id,
                payload={"status": "success"}
            )
        else:
            st.sidebar.error("Patient data not found")
            log_event(
                event_type="patient_data_loaded",
                source="patient_app",
                user_id=patient_id,
                payload={"status": "not_found"}
            )
    
    # Navigation
    page = st.sidebar.radio(
        "Navigation",
        ["Dashboard", "Sleep Report", "Brain Health", "Interventions", "Resources"]
    )
    if st.session_state.get("_last_patient_page") != page:
        log_event(
            event_type="patient_page_view",
            source="patient_app",
            user_id=patient_id,
            payload={"page": page}
        )
        st.session_state["_last_patient_page"] = page
    
    # Main content
    if 'patient_data' not in st.session_state:
        st.info("👈 Please enter your Patient ID and click 'Load My Data' to begin")
        return
    
    patient_data = st.session_state['patient_data']
    
    if page == "Dashboard":
        show_dashboard(patient_data)
    elif page == "Sleep Report":
        show_sleep_report(patient_data)
    elif page == "Brain Health":
        show_brain_health(patient_data)
    elif page == "Interventions":
        show_interventions(patient_data)
    elif page == "Resources":
        show_resources()


def show_dashboard(patient_data):
    """Show main dashboard"""
    st.header("📊 Your Sleep & Brain Health Dashboard")
    
    # Calculate risk score
    risk_score = calculate_risk_score(patient_data)
    risk_category, risk_class, risk_color = get_risk_category(risk_score)
    
    # Top metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "Brain Aging Risk",
            f"{risk_category}",
            f"{risk_score*100:.0f}%"
        )
    
    with col2:
        st.metric(
            "Sleep Efficiency",
            f"{patient_data.get('sleep_efficiency', 0):.1f}%",
            delta=f"{patient_data.get('sleep_efficiency', 0) - 85:.1f}%" if patient_data.get('sleep_efficiency', 0) < 85 else "Good"
        )
    
    with col3:
        st.metric(
            "Total Sleep Time",
            f"{patient_data.get('total_sleep_time', 0)/60:.1f} hrs"
        )
    
    with col4:
        st.metric(
            "Sleep Regularity",
            f"{patient_data.get('sleep_regularity_index', 0):.0f}/100"
        )
    
    st.divider()
    
    # Visualizations
    col1, col2 = st.columns(2)
    
    with col1:
        st.plotly_chart(
            plot_sleep_quality_gauge(patient_data.get('sleep_efficiency', 0)),
            use_container_width=True
        )
    
    with col2:
        st.plotly_chart(
            plot_circadian_rhythm(patient_data),
            use_container_width=True
        )
    
    # Recommendations
    st.subheader("🎯 Personalized Recommendations")
    
    if patient_data.get('sleep_efficiency', 100) < 85:
        st.warning("⚠️ **Low Sleep Efficiency Detected**\n\nConsider cognitive behavioral therapy for insomnia (CBT-I) to improve sleep quality.")
    
    if patient_data.get('sleep_fragmentation_index', 0) > 15:
        st.warning("⚠️ **High Sleep Fragmentation**\n\nConsult with your clinician about potential sleep apnea screening.")
    
    if patient_data.get('social_jet_lag', 0) > 2:
        st.info("💡 **Irregular Sleep Schedule**\n\nTry to maintain consistent sleep and wake times, even on weekends.")


def show_sleep_report(patient_data):
    """Show detailed sleep report"""
    st.header("😴 Detailed Sleep Report")
    
    # Sleep architecture
    st.subheader("Sleep Architecture")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Total Sleep Time", f"{patient_data.get('total_sleep_time', 0)/60:.1f} hours")
        st.metric("Sleep Efficiency", f"{patient_data.get('sleep_efficiency', 0):.1f}%")
    
    with col2:
        st.metric("Sleep Onset Latency", f"{patient_data.get('sleep_onset_latency', 0):.0f} min")
        st.metric("WASO", f"{patient_data.get('wake_after_sleep_onset', 0):.0f} min")
    
    with col3:
        st.metric("Number of Awakenings", f"{patient_data.get('number_of_awakenings', 0):.0f}")
        st.metric("Fragmentation Index", f"{patient_data.get('sleep_fragmentation_index', 0):.1f}")
    
    st.divider()
    
    # Circadian metrics
    st.subheader("Circadian Rhythm Analysis")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.metric("Interdaily Stability", f"{patient_data.get('interdaily_stability', 0):.3f}")
        st.caption("Higher is better (0-1 scale)")
    
    with col2:
        st.metric("Intradaily Variability", f"{patient_data.get('intradaily_variability', 0):.3f}")
        st.caption("Lower is better")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.metric("Relative Amplitude", f"{patient_data.get('relative_amplitude', 0):.3f}")
        st.caption("Difference between day and night activity")
    
    with col2:
        st.metric("Social Jet Lag", f"{patient_data.get('social_jet_lag', 0):.1f} hours")
        st.caption("Weekday vs. weekend sleep timing difference")


def show_brain_health(patient_data):
    """Show brain health insights"""
    st.header("🧠 Brain Health Insights")
    
    st.info("**How Sleep Affects Your Brain**\n\nQuality sleep is essential for brain health and cognitive function. Poor sleep patterns can accelerate brain aging and increase dementia risk.")
    
    # Risk factors
    st.subheader("Your Risk Profile")
    
    risk_score = calculate_risk_score(patient_data)
    risk_category, _, risk_color = get_risk_category(risk_score)
    
    st.markdown(f"**Overall Brain Aging Risk:** <span style='color:{risk_color}; font-size:1.5rem;'>{risk_category}</span>", unsafe_allow_html=True)
    
    # Protective factors
    st.subheader("✅ Protective Factors")
    
    if patient_data.get('sleep_efficiency', 0) >= 85:
        st.success("✓ Good sleep efficiency")
    
    if patient_data.get('sleep_regularity_index', 0) >= 75:
        st.success("✓ Regular sleep schedule")
    
    if patient_data.get('social_jet_lag', 0) < 2:
        st.success("✓ Consistent sleep timing")
    
    # Risk factors
    st.subheader("⚠️ Risk Factors")
    
    if patient_data.get('sleep_efficiency', 100) < 85:
        st.warning("⚠ Low sleep efficiency")
    
    if patient_data.get('sleep_fragmentation_index', 0) > 15:
        st.warning("⚠ High sleep fragmentation")
    
    if patient_data.get('sleep_regularity_index', 100) < 75:
        st.warning("⚠ Irregular sleep patterns")


def show_interventions(patient_data):
    """Show intervention recommendations"""
    st.header("💊 Personalized Interventions")
    
    st.info("Based on your sleep patterns, here are evidence-based interventions that may benefit your brain health:")
    
    # Recommend interventions based on patient data
    if patient_data.get('sleep_efficiency', 100) < 85:
        with st.expander("🎯 Cognitive Behavioral Therapy for Insomnia (CBT-I)", expanded=True):
            st.markdown("""
            **What is it?** A structured program to improve sleep quality without medication.
            
            **Expected Benefits:**
            - Reduce brain age acceleration by 2-3 years
            - Improve sleep efficiency by 10-15%
            - Better cognitive function
            
            **Duration:** 6-8 weeks
            
            **Next Steps:** Discuss with your clinician to enroll in our digital CBT-I program.
            """)
    
    if patient_data.get('sleep_fragmentation_index', 0) > 15:
        with st.expander("😷 Sleep Apnea Screening & Treatment"):
            st.markdown("""
            **Why recommended?** Your sleep fragmentation suggests possible sleep apnea.
            
            **Expected Benefits:**
            - Reduce brain aging risk by 30-40%
            - Improve sleep quality
            - Better daytime alertness
            
            **Next Steps:** Schedule a sleep study with your clinician.
            """)
    
    if patient_data.get('social_jet_lag', 0) > 2:
        with st.expander("⏰ Circadian Rhythm Optimization"):
            st.markdown("""
            **What is it?** Maintaining consistent sleep-wake times.
            
            **Expected Benefits:**
            - Improve sleep regularity by 20-30%
            - Better circadian alignment
            - Reduced brain aging risk
            
            **Tips:**
            - Keep consistent bedtime and wake time (even weekends)
            - Get morning sunlight exposure
            - Avoid bright lights before bed
            """)


def show_resources():
    """Show educational resources"""
    st.header("📚 Educational Resources")
    
    st.subheader("Understanding Sleep & Brain Health")
    
    with st.expander("Why Sleep Matters for Your Brain"):
        st.markdown("""
        Sleep plays a critical role in brain health:
        
        - **Memory Consolidation:** Sleep helps transfer information from short-term to long-term memory
        - **Waste Clearance:** The glymphatic system clears toxic proteins during sleep
        - **Brain Plasticity:** Sleep supports neural connections and learning
        - **Cognitive Function:** Quality sleep improves attention, decision-making, and creativity
        """)
    
    with st.expander("Sleep Hygiene Tips"):
        st.markdown("""
        **Create a Sleep-Friendly Environment:**
        - Keep bedroom cool (60-67°F / 15-19°C)
        - Use blackout curtains or eye mask
        - Minimize noise or use white noise
        - Reserve bed for sleep only
        
        **Establish a Routine:**
        - Consistent sleep and wake times
        - Relaxing pre-bed routine
        - Avoid screens 1 hour before bed
        - Limit caffeine after 2 PM
        """)
    
    with st.expander("When to Seek Help"):
        st.markdown("""
        Consult your clinician if you experience:
        - Chronic difficulty falling or staying asleep
        - Loud snoring or gasping during sleep
        - Excessive daytime sleepiness
        - Significant changes in sleep patterns
        - Concerns about memory or cognitive function
        """)


if __name__ == "__main__":
    main()
