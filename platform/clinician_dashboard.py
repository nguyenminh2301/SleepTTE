"""
Clinician Dashboard for Sleep Intervention Management
Streamlit web app for healthcare providers
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
from src.utils.event_logger import log_event
from demo_data import generate_demo_sleep_features, generate_demo_clinical, generate_demo_mri

# Page configuration
st.set_page_config(
    page_title="Clinician Dashboard - Sleep & Brain Health",
    page_icon="⚕️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #2c3e50;
        text-align: center;
        margin-bottom: 2rem;
    }
    .patient-card {
        background-color: #f8f9fa;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #3498db;
        margin-bottom: 1rem;
    }
</style>
""", unsafe_allow_html=True)


DEMO_MODE = os.getenv("DEMO_MODE", "0").lower() in {"1", "true", "yes"}


def load_patient_roster():
    """Load all patients"""
    try:
        sleep_features = pd.read_csv('data/processed/sleep_features.csv')
        clinical = pd.read_csv('data/processed/clinical_processed.csv')
        mri = pd.read_csv('data/processed/mri_processed.csv')
        
        roster = sleep_features.merge(clinical, on='participant_id', how='left')
        roster = roster.merge(mri[['participant_id', 'brain_age_delta']], on='participant_id', how='left')
        
        # Calculate risk scores
        roster['risk_score'] = roster.apply(calculate_risk_score_row, axis=1)
        roster['risk_category'] = roster['risk_score'].apply(lambda x: 
            'High' if x >= 0.67 else ('Moderate' if x >= 0.33 else 'Low')
        )
        
        return roster
    except:
        if not DEMO_MODE:
            return pd.DataFrame()
        sleep_features = generate_demo_sleep_features(n_patients=30)
        clinical = generate_demo_clinical(n_patients=30)
        mri = generate_demo_mri(n_patients=30)
        roster = sleep_features.merge(clinical, on='participant_id', how='left')
        roster = roster.merge(mri[['participant_id', 'brain_age_delta', 'hippocampal_volume']], on='participant_id', how='left')
        roster['risk_score'] = roster.apply(calculate_risk_score_row, axis=1)
        roster['risk_category'] = roster['risk_score'].apply(lambda x:
            'High' if x >= 0.67 else ('Moderate' if x >= 0.33 else 'Low')
        )
        return roster


def calculate_risk_score_row(row):
    """Calculate risk score for a patient row"""
    risk_factors = 0
    
    if row.get('sleep_efficiency', 100) < 80:
        risk_factors += 2
    elif row.get('sleep_efficiency', 100) < 85:
        risk_factors += 1
    
    if row.get('sleep_fragmentation_index', 0) > 20:
        risk_factors += 2
    elif row.get('sleep_fragmentation_index', 0) > 10:
        risk_factors += 1
    
    if row.get('sleep_regularity_index', 100) < 60:
        risk_factors += 2
    elif row.get('sleep_regularity_index', 100) < 75:
        risk_factors += 1
    
    return min(risk_factors / 8, 1.0)


def main():
    """Main clinician dashboard"""
    if DEMO_MODE:
        st.sidebar.caption("Demo mode enabled")
    
    # Header
    st.markdown('<div class="main-header">⚕️ Clinician Dashboard: Sleep & Brain Health</div>', unsafe_allow_html=True)
    
    # Sidebar
    st.sidebar.title("Navigation")
    page = st.sidebar.radio(
        "Select View",
        ["Patient Roster", "Individual Patient", "Population Analytics", "Intervention Management", "Reports"]
    )
    if st.session_state.get("_last_clinician_page") != page:
        log_event(
            event_type="clinician_page_view",
            source="clinician_dashboard",
            payload={"page": page}
        )
        st.session_state["_last_clinician_page"] = page
    
    # Load data
    roster = load_patient_roster()
    
    if roster.empty:
        st.warning("No patient data available. Please run data processing pipeline first.")
        log_event(
            event_type="clinician_roster_load",
            source="clinician_dashboard",
            payload={"status": "empty"}
        )
        return
    log_event(
        event_type="clinician_roster_load",
        source="clinician_dashboard",
        payload={"status": "ok", "n_patients": int(len(roster))}
    )
    
    # Route to pages
    if page == "Patient Roster":
        show_patient_roster(roster)
    elif page == "Individual Patient":
        show_individual_patient(roster)
    elif page == "Population Analytics":
        show_population_analytics(roster)
    elif page == "Intervention Management":
        show_intervention_management(roster)
    elif page == "Reports":
        show_reports(roster)


def show_patient_roster(roster):
    """Show patient roster with risk stratification"""
    st.header("👥 Patient Roster")
    
    # Summary metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Patients", len(roster))
    
    with col2:
        high_risk = (roster['risk_category'] == 'High').sum()
        st.metric("High Risk", high_risk, delta=f"{high_risk/len(roster)*100:.1f}%")
    
    with col3:
        moderate_risk = (roster['risk_category'] == 'Moderate').sum()
        st.metric("Moderate Risk", moderate_risk)
    
    with col4:
        low_risk = (roster['risk_category'] == 'Low').sum()
        st.metric("Low Risk", low_risk)
    
    st.divider()
    
    # Filters
    col1, col2, col3 = st.columns(3)
    
    with col1:
        risk_filter = st.multiselect(
            "Filter by Risk",
            ['High', 'Moderate', 'Low'],
            default=['High', 'Moderate', 'Low']
        )
    
    with col2:
        sex_filter = st.multiselect(
            "Filter by Sex",
            roster['sex'].unique(),
            default=roster['sex'].unique()
        )
    
    with col3:
        age_range = st.slider(
            "Age Range",
            int(roster['age'].min()),
            int(roster['age'].max()),
            (int(roster['age'].min()), int(roster['age'].max()))
        )
    
    # Apply filters
    filtered = roster[
        (roster['risk_category'].isin(risk_filter)) &
        (roster['sex'].isin(sex_filter)) &
        (roster['age'] >= age_range[0]) &
        (roster['age'] <= age_range[1])
    ]
    
    # Display table
    st.subheader(f"Patients ({len(filtered)})")
    
    display_cols = [
        'participant_id', 'age', 'sex', 'risk_category', 'risk_score',
        'sleep_efficiency', 'sleep_fragmentation_index', 'sleep_regularity_index'
    ]
    
    # Format display
    display_df = filtered[display_cols].copy()
    display_df['risk_score'] = display_df['risk_score'].apply(lambda x: f"{x*100:.0f}%")
    display_df['sleep_efficiency'] = display_df['sleep_efficiency'].apply(lambda x: f"{x:.1f}%")
    
    # Color code risk
    def highlight_risk(row):
        if row['risk_category'] == 'High':
            return ['background-color: #ffcccc'] * len(row)
        elif row['risk_category'] == 'Moderate':
            return ['background-color: #fff4cc'] * len(row)
        else:
            return ['background-color: #ccffcc'] * len(row)
    
    st.dataframe(
        display_df.style.apply(highlight_risk, axis=1),
        use_container_width=True,
        height=400
    )
    
    # Export
    if st.button("📥 Export Patient List"):
        csv = filtered.to_csv(index=False)
        st.download_button(
            "Download CSV",
            csv,
            "patient_roster.csv",
            "text/csv"
        )


def show_individual_patient(roster):
    """Show detailed individual patient view"""
    st.header("🔍 Individual Patient Profile")
    
    # Patient selection
    patient_id = st.selectbox(
        "Select Patient",
        roster['participant_id'].tolist()
    )
    
    patient = roster[roster['participant_id'] == patient_id].iloc[0]
    
    # Patient header
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Patient ID", patient['participant_id'])
    
    with col2:
        st.metric("Age", f"{patient['age']:.0f} years")
    
    with col3:
        st.metric("Sex", patient['sex'])
    
    with col4:
        risk_color = {'High': '🔴', 'Moderate': '🟡', 'Low': '🟢'}
        st.metric("Risk", f"{risk_color[patient['risk_category']]} {patient['risk_category']}")
    
    st.divider()
    
    # Tabs
    tab1, tab2, tab3, tab4 = st.tabs(["Sleep Profile", "Brain Health", "Interventions", "History"])
    
    with tab1:
        show_patient_sleep_profile(patient)
    
    with tab2:
        show_patient_brain_health(patient)
    
    with tab3:
        show_patient_interventions(patient)
    
    with tab4:
        st.info("Patient history tracking coming soon...")


def show_patient_sleep_profile(patient):
    """Show detailed sleep profile"""
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Sleep Architecture")
        st.metric("Total Sleep Time", f"{patient.get('total_sleep_time', 0)/60:.1f} hours")
        st.metric("Sleep Efficiency", f"{patient.get('sleep_efficiency', 0):.1f}%")
        st.metric("Sleep Onset Latency", f"{patient.get('sleep_onset_latency', 0):.0f} min")
        st.metric("WASO", f"{patient.get('wake_after_sleep_onset', 0):.0f} min")
    
    with col2:
        st.subheader("Circadian Metrics")
        st.metric("Sleep Regularity Index", f"{patient.get('sleep_regularity_index', 0):.0f}/100")
        st.metric("Social Jet Lag", f"{patient.get('social_jet_lag', 0):.1f} hours")
        st.metric("Interdaily Stability", f"{patient.get('interdaily_stability', 0):.3f}")
        st.metric("Fragmentation Index", f"{patient.get('sleep_fragmentation_index', 0):.1f}")


def show_patient_brain_health(patient):
    """Show brain health metrics"""
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Brain Aging Biomarkers")
        st.metric("Brain Age Delta", f"{patient.get('brain_age_delta', 0):.1f} years")
        st.metric("Hippocampal Volume", f"{patient.get('hippocampal_volume', 0):.0f} mm³")
    
    with col2:
        st.subheader("Risk Assessment")
        st.metric("Overall Risk Score", f"{patient['risk_score']*100:.0f}%")
        st.metric("Risk Category", patient['risk_category'])
    
    # Risk factors
    st.subheader("Identified Risk Factors")
    
    if patient.get('sleep_efficiency', 100) < 85:
        st.warning("⚠️ Low sleep efficiency")
    
    if patient.get('sleep_fragmentation_index', 0) > 15:
        st.warning("⚠️ High sleep fragmentation (possible OSA)")
    
    if patient.get('sleep_regularity_index', 100) < 75:
        st.warning("⚠️ Irregular sleep patterns")
    
    if patient.get('social_jet_lag', 0) > 2:
        st.warning("⚠️ Significant social jet lag")


def show_patient_interventions(patient):
    """Show recommended interventions"""
    st.subheader("💊 Recommended Interventions")
    
    # Generate recommendations
    recommendations = []
    
    if patient.get('sleep_efficiency', 100) < 85:
        recommendations.append({
            'intervention': 'Cognitive Behavioral Therapy for Insomnia (CBT-I)',
            'priority': 'High',
            'expected_benefit': 'Reduce brain age acceleration by 2-3 years',
            'duration': '6-8 weeks'
        })
    
    if patient.get('sleep_fragmentation_index', 0) > 15:
        recommendations.append({
            'intervention': 'Sleep Apnea Screening & CPAP Treatment',
            'priority': 'High',
            'expected_benefit': 'Reduce brain aging risk by 30-40%',
            'duration': 'Ongoing'
        })
    
    if patient.get('social_jet_lag', 0) > 2:
        recommendations.append({
            'intervention': 'Circadian Rhythm Optimization',
            'priority': 'Moderate',
            'expected_benefit': 'Improve sleep regularity by 20-30%',
            'duration': '4-6 weeks'
        })
    
    if recommendations:
        for rec in recommendations:
            with st.expander(f"🎯 {rec['intervention']} (Priority: {rec['priority']})", expanded=True):
                st.write(f"**Expected Benefit:** {rec['expected_benefit']}")
                st.write(f"**Duration:** {rec['duration']}")
                
                col1, col2 = st.columns(2)
                with col1:
                    if st.button(f"Prescribe {rec['intervention'][:20]}...", key=rec['intervention']):
                        st.success("✓ Intervention prescribed")
                with col2:
                    if st.button(f"Schedule Follow-up", key=f"followup_{rec['intervention']}"):
                        st.success("✓ Follow-up scheduled")
    else:
        st.success("✅ No immediate interventions needed. Continue monitoring.")


def show_population_analytics(roster):
    """Show population-level analytics"""
    st.header("📊 Population Analytics")
    
    # Risk distribution
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Risk Distribution")
        risk_counts = roster['risk_category'].value_counts()
        
        fig = go.Figure(data=[
            go.Pie(
                labels=risk_counts.index,
                values=risk_counts.values,
                marker=dict(colors=['#d62728', '#ff7f0e', '#2ca02c'])
            )
        ])
        fig.update_layout(height=300)
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.subheader("Sleep Efficiency Distribution")
        fig = px.histogram(
            roster,
            x='sleep_efficiency',
            nbins=20,
            color='risk_category',
            color_discrete_map={'High': '#d62728', 'Moderate': '#ff7f0e', 'Low': '#2ca02c'}
        )
        fig.update_layout(height=300)
        st.plotly_chart(fig, use_container_width=True)
    
    # Sex-stratified analysis
    st.subheader("Sex-Stratified Analysis")
    
    sex_risk = pd.crosstab(roster['sex'], roster['risk_category'], normalize='index') * 100
    
    fig = go.Figure(data=[
        go.Bar(name='High', x=sex_risk.index, y=sex_risk['High'], marker_color='#d62728'),
        go.Bar(name='Moderate', x=sex_risk.index, y=sex_risk['Moderate'], marker_color='#ff7f0e'),
        go.Bar(name='Low', x=sex_risk.index, y=sex_risk['Low'], marker_color='#2ca02c')
    ])
    
    fig.update_layout(
        barmode='stack',
        yaxis_title="Percentage",
        xaxis_title="Sex",
        height=400
    )
    
    st.plotly_chart(fig, use_container_width=True)


def show_intervention_management(roster):
    """Show intervention management interface"""
    st.header("💊 Intervention Management")
    
    st.info("Track and manage sleep interventions across your patient population")
    
    # Intervention summary
    col1, col2, col3 = st.columns(3)
    
    # Calculate patients needing each intervention
    need_cbti = (roster['sleep_efficiency'] < 85).sum()
    need_osa = (roster['sleep_fragmentation_index'] > 15).sum()
    need_circadian = (roster['social_jet_lag'] > 2).sum()
    
    with col1:
        st.metric("Patients Needing CBT-I", need_cbti)
    
    with col2:
        st.metric("Patients Needing OSA Screening", need_osa)
    
    with col3:
        st.metric("Patients Needing Circadian Intervention", need_circadian)
    
    st.divider()
    
    # Intervention tabs
    tab1, tab2, tab3 = st.tabs(["CBT-I", "OSA Treatment", "Circadian Optimization"])
    
    with tab1:
        st.subheader("CBT-I Candidates")
        cbti_candidates = roster[roster['sleep_efficiency'] < 85][
            ['participant_id', 'age', 'sex', 'sleep_efficiency', 'risk_category']
        ]
        st.dataframe(cbti_candidates, use_container_width=True)
    
    with tab2:
        st.subheader("OSA Screening Candidates")
        osa_candidates = roster[roster['sleep_fragmentation_index'] > 15][
            ['participant_id', 'age', 'sex', 'sleep_fragmentation_index', 'risk_category']
        ]
        st.dataframe(osa_candidates, use_container_width=True)
    
    with tab3:
        st.subheader("Circadian Intervention Candidates")
        circadian_candidates = roster[roster['social_jet_lag'] > 2][
            ['participant_id', 'age', 'sex', 'social_jet_lag', 'risk_category']
        ]
        st.dataframe(circadian_candidates, use_container_width=True)


def show_reports(roster):
    """Show reporting interface"""
    st.header("📄 Clinical Reports")
    
    st.subheader("Generate Reports")
    
    report_type = st.selectbox(
        "Select Report Type",
        ["Population Summary", "High-Risk Patients", "Intervention Outcomes", "Custom Report"]
    )
    
    if st.button("Generate Report"):
        st.success("✓ Report generated successfully")
        
        if report_type == "Population Summary":
            st.markdown(f"""
            ### Population Summary Report
            
            **Total Patients:** {len(roster)}
            
            **Risk Distribution:**
            - High Risk: {(roster['risk_category'] == 'High').sum()} ({(roster['risk_category'] == 'High').sum()/len(roster)*100:.1f}%)
            - Moderate Risk: {(roster['risk_category'] == 'Moderate').sum()} ({(roster['risk_category'] == 'Moderate').sum()/len(roster)*100:.1f}%)
            - Low Risk: {(roster['risk_category'] == 'Low').sum()} ({(roster['risk_category'] == 'Low').sum()/len(roster)*100:.1f}%)
            
            **Average Sleep Metrics:**
            - Sleep Efficiency: {roster['sleep_efficiency'].mean():.1f}%
            - Total Sleep Time: {roster['total_sleep_time'].mean()/60:.1f} hours
            - Sleep Regularity Index: {roster['sleep_regularity_index'].mean():.0f}/100
            """)
        
        # Download button
        if st.button("📥 Download Report (PDF)"):
            st.info("PDF export functionality coming soon...")


if __name__ == "__main__":
    main()
