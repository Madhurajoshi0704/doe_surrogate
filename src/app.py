import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px

from src.database.lims_db import init_lims_db, get_lims_dataframe
from src.models.dual_modeling import DualModelingEngine
from src.agent.lab_copilot import LabCopilotAgent
from src.models.optimizer import CostPerformanceOptimizer

# Set Page Config
st.set_page_config(
    page_title="FormuAI — Formulation Surrogate Model Stack",
    page_icon="🔬",
    layout="wide"
)

# Injected CSS for premium feel
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;700&family=Space+Grotesk:wght@400;600&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Outfit', sans-serif;
    }
    
    h1, h2, h3, h4 {
        font-family: 'Space Grotesk', sans-serif;
        color: #0F172A;
    }
    
    .top-banner {
        background: linear-gradient(135deg, #0F172A 0%, #1E3A8A 50%, #059669 100%);
        padding: 2.5rem;
        border-radius: 16px;
        color: white;
        margin-bottom: 2rem;
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
    }
    
    .top-banner h1 {
        color: #F8FAFC !important;
        margin: 0;
        font-weight: 700;
        font-size: 2.3rem;
    }
    
    .top-banner p {
        color: #D1FAE5;
        font-size: 1.1rem;
        margin-top: 0.5rem;
    }
</style>
""", unsafe_allow_html=True)

# Cache singletons
@st.cache_resource
def load_application_resources():
    db_path = init_lims_db()
    engine = DualModelingEngine()
    engine.load_models()
    agent = LabCopilotAgent()
    optimizer = CostPerformanceOptimizer()
    return db_path, engine, agent, optimizer

db_path, engine, agent, optimizer = load_application_resources()

# Top Banner
st.markdown("""
<div class="top-banner">
    <h1>🔬 FormuAI</h1>
    <p>DOE-Validated Formulation Surrogate Model Stack (CCD + OLS-RSM vs. Random Forest ML)</p>
</div>
""", unsafe_allow_html=True)

# Sidebar
st.sidebar.image("https://img.icons8.com/color/96/chemistry.png", width=70)
st.sidebar.markdown("### **R&D Workflow Stack**")
tab_selection = st.sidebar.radio(
    "Choose Module:",
    ["📊 Model Validation & DOE Metrics", "🔬 Formulation Simulator", "📈 Sensitivity Curves", "💰 Cost-Performance Pareto Optimization", "💬 AI Lab Copilot (Copilot Studio)"]
)

st.sidebar.markdown("---")
st.sidebar.markdown("""
**System Status:**
- **DOE:** Central Composite (CCD)
- **Factors:** SLES, CAPB, NaCl
- **Runs Logged:** 20 records
""")

df = get_lims_dataframe(db_path)

# ----------------- MODULE 1: MODEL VALIDATION & DOE METRICS -----------------
if tab_selection == "📊 Model Validation & DOE Metrics":
    st.subheader("📊 DOE Design Space & Model Comparison Statistics")
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.markdown("#### **1. Central Composite Design Space (CCD) Coverage**")
        st.write("A 3D projection of the 20 experimental runs. Star points lie at the axial boundaries, factorial points represent the corners, and center points are clustered in the middle.")
        
        fig_3d = px.scatter_3d(
            df,
            x="SLES_pct",
            y="CAPB_pct",
            z="NaCl_pct",
            color="replicate_flag",
            symbol="replicate_flag",
            labels={'SLES_pct': 'SLES %', 'CAPB_pct': 'CAPB %', 'NaCl_pct': 'NaCl %'},
            color_discrete_map={0: "#0284C7", 1: "#10B981"},
            title="Factor Space Design Points"
        )
        fig_3d.update_layout(height=400, margin=dict(l=0, r=0, t=30, b=0))
        st.plotly_chart(fig_3d, use_container_width=True)
        
    with col2:
        st.markdown("#### **2. OLS-RSM vs. Random Forest Accuracy Comparison**")
        st.write("RSM uses a parametric quadratic polynomial (best for small datasets). Random Forest uses decision tree ensembles.")
        
        # Display comparison table
        st.dataframe(engine.metrics_df, hide_index=True)
        
        # Explain R2 vs Adj R2
        st.markdown("""
        > [!IMPORTANT]
        > **R&D Insights:** Classical RSM (quadratic regression) generally yields higher CV R² than Random Forest on small designs ($N=20$) because the physical behavior (like the viscosity salt-curve) matches a parabolic second-order equation. Machine Learning requires larger datasets to generalize effectively.
        """)

    st.markdown("---")
    st.markdown("#### **3. Experimental LIMS Notebook Log (SQLite Dataset)**")
    st.dataframe(df, hide_index=True)

# ----------------- MODULE 2: FORMULATION SIMULATION -----------------
elif tab_selection == "🔬 Formulation Simulator":
    st.subheader("🔬 AI-Driven Formulation Simulator")
    st.write("Vary SLES, CAPB, and Salt concentration. Run predictions instantly using either RSM or Random Forest models.")
    
    col_in, col_out = st.columns([1, 2])
    
    with col_in:
        st.markdown("### **Input Parameters**")
        sles = st.slider("Primary Surfactant (SLES %)", 8.0, 15.0, 11.5, 0.1)
        capb = st.slider("Co-Surfactant (CAPB %)", 2.0, 6.0, 4.0, 0.1)
        nacl = st.slider("Thickener (NaCl %)", 1.0, 3.0, 2.0, 0.1)
        
        water = round(100.0 - (sles + capb + nacl), 3)
        st.info(f"💧 **Water (Balance):** {water}% w/w")
        
        model_choice = st.radio("Predictive Model:", ["RSM (Classical Polynomial)", "Random Forest (Machine Learning)"])
        model_type = "RSM" if "RSM" in model_choice else "RF"
        
        inputs = {
            'SLES_pct': sles,
            'CAPB_pct': capb,
            'NaCl_pct': nacl,
            'water_pct': water
        }
        
    with col_out:
        st.markdown("### **Predicted Outputs**")
        preds = engine.predict(model_type, inputs)
        
        pcol1, pcol2 = st.columns(2)
        with pcol1:
            # Viscosity indicator
            fig_v = go.Figure(go.Indicator(
                mode="gauge+number",
                value=preds['viscosity_sec'],
                title={'text': "Viscosity (Efflux time sec)"},
                gauge={'axis': {'range': [0, 80]},
                       'bar': {'color': "#0284C7"},
                       'steps': [{'range': [0, 20], 'color': "#fee2e2"},
                                 {'range': [20, 55], 'color': "#dcfce7"},
                                 {'range': [55, 80], 'color': "#fee2e2"}]}
            ))
            fig_v.update_layout(height=200, margin=dict(l=10, r=10, t=40, b=10))
            st.plotly_chart(fig_v, use_container_width=True)
            
            # pH indicator
            fig_ph = go.Figure(go.Indicator(
                mode="gauge+number",
                value=preds['ph'],
                title={'text': "pH Level"},
                gauge={'axis': {'range': [3, 9]},
                       'bar': {'color': "#059669"},
                       'steps': [{'range': [3, 5.5], 'color': "#fef9c3"},
                                 {'range': [5.5, 7.0], 'color': "#dcfce7"},
                                 {'range': [7.0, 9], 'color': "#fee2e2"}]}
            ))
            fig_ph.update_layout(height=200, margin=dict(l=10, r=10, t=40, b=10))
            st.plotly_chart(fig_ph, use_container_width=True)
            
        with pcol2:
            # Foam height
            fig_f = go.Figure(go.Indicator(
                mode="gauge+number",
                value=preds['foam_height_initial_mm'],
                title={'text': "Initial Foam Height (mm)"},
                gauge={'axis': {'range': [0, 200]},
                       'bar': {'color': "#F59E0B"}}
            ))
            fig_f.update_layout(height=200, margin=dict(l=10, r=10, t=40, b=10))
            st.plotly_chart(fig_f, use_container_width=True)
            
            # Foam stability (5 min)
            fig_fs = go.Figure(go.Indicator(
                mode="gauge+number",
                value=preds['foam_height_5min_mm'],
                title={'text': "Foam Height after 5 min (mm)"},
                gauge={'axis': {'range': [0, 200]},
                       'bar': {'color': "#8B5CF6"}}
            ))
            fig_fs.update_layout(height=200, margin=dict(l=10, r=10, t=40, b=10))
            st.plotly_chart(fig_fs, use_container_width=True)

    # Optimization Block
    st.markdown("---")
    st.markdown("### 🧬 AI formulation Solver (Design search)")
    ocol1, ocol2 = st.columns(2)
    with ocol1:
        target_visc = st.number_input("Target Viscosity (Sec):", min_value=5.0, max_value=80.0, value=40.0, step=1.0)
    with ocol2:
        target_ph = st.number_input("Target pH:", min_value=4.5, max_value=8.0, value=6.0, step=0.1)
        
    if st.button("🧬 Solve Recipe"):
        opt_in, opt_out = engine.optimize_formulation(target_visc, target_ph)
        
        col_a, col_b = st.columns(2)
        with col_a:
            st.success("Proposed Chemical Formula:")
            tbl_in = pd.DataFrame([{
                "Primary Surfactant (SLES)": f"{opt_in['SLES_pct']}% w/w",
                "Co-Surfactant (CAPB)": f"{opt_in['CAPB_pct']}% w/w",
                "Thickener (NaCl)": f"{opt_in['NaCl_pct']}% w/w",
                "Water (Balance)": f"{opt_in['water_pct']}% w/w"
            }]).T
            tbl_in.columns = ["Value"]
            st.table(tbl_in)
            
        with col_b:
            st.info("Predicted Properties:")
            tbl_out = pd.DataFrame([{
                "Predicted Viscosity": f"{opt_out['viscosity_sec']:.1f} Sec (Target: {target_visc})",
                "Predicted pH": f"{opt_out['ph']:.2f} (Target: {target_ph})",
                "Predicted Initial Foam": f"{opt_out['foam_height_initial_mm']:.1f} mm",
                "Predicted 5-Min Foam": f"{opt_out['foam_height_5min_mm']:.1f} mm"
            }]).T
            tbl_out.columns = ["Value"]
            st.table(tbl_out)

# ----------------- MODULE 3: SENSITIVITY CURVES -----------------
elif tab_selection == "📈 Sensitivity Curves":
    st.subheader("📈 Ingredient Sensitivity Analysis")
    st.write("Understand which factor drives which physical response. Select a factor to vary while keeping other ingredients fixed at their midpoint values.")
    
    col_ctrl, col_chart = st.columns([1, 2])
    
    with col_ctrl:
        st.markdown("#### **Base Midpoint Settings**")
        sles_mid = st.slider("Fixed SLES %", 8.0, 15.0, 11.5)
        capb_mid = st.slider("Fixed CAPB %", 2.0, 6.0, 4.0)
        nacl_mid = st.slider("Fixed NaCl %", 1.0, 3.0, 2.0)
        
        selected_factor = st.selectbox("Factor to Vary:", ["SLES_pct", "CAPB_pct", "NaCl_pct"])
        selected_response = st.selectbox("Response to Chart:", ["viscosity_sec", "foam_height_initial_mm", "foam_height_5min_mm", "ph"])
        
        base_inputs = {
            'SLES_pct': sles_mid,
            'CAPB_pct': capb_mid,
            'NaCl_pct': nacl_mid,
            'water_pct': round(100.0 - (sles_mid + capb_mid + nacl_mid), 3)
        }
        
    with col_chart:
        # Generate curves
        sens_df = engine.get_sensitivity_data(selected_factor, base_inputs)
        
        # Plotly chart showing RSM vs RF predictions for the response
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=sens_df["FactorValue"],
            y=sens_df[f"RSM_{selected_response}"],
            mode="lines+markers",
            name="RSM (Quadratic Curve)",
            line=dict(color="#0284C7", width=3)
        ))
        fig.add_trace(go.Scatter(
            x=sens_df["FactorValue"],
            y=sens_df[f"RF_{selected_response}"],
            mode="lines",
            name="Random Forest (Decision Tree)",
            line=dict(color="#F59E0B", dash="dash", width=2)
        ))
        
        fig.update_layout(
            title=f"Sensitivity Curve: {selected_response} vs. {selected_factor}",
            xaxis_title=selected_factor,
            yaxis_title=selected_response,
            height=400
        )
        st.plotly_chart(fig, use_container_width=True)


# ----------------- MODULE 4: COST-PERFORMANCE OPTIMIZATION -----------------
elif tab_selection == "💰 Cost-Performance Pareto Optimization":
    st.subheader("💰 Multi-Objective Cost-Performance Optimization")
    st.write(
        "FMCG product design requires balancing performance attributes with formulation raw material costs. "
        "Every raw material adds to the unit cost (SLES=0.12 INR/g, CAPB=0.15 INR/g, NaCl=0.02 INR/g). "
        "This optimizer uses **scipy.optimize.differential_evolution** to search the design space for the "
        "lowest-cost formulation that satisfies your performance constraints."
    )
    
    col_opt_in, col_opt_out = st.columns([1, 2])
    
    with col_opt_in:
        st.markdown("#### **1. Target Performance Specifications**")
        min_visc_opt = st.slider("Min Viscosity Target (Sec)", 10.0, 40.0, 20.0)
        max_visc_opt = st.slider("Max Viscosity Target (Sec)", 40.0, 75.0, 50.0)
        min_ph_opt = st.slider("Min pH Target", 5.0, 6.2, 5.5, 0.1)
        max_ph_opt = st.slider("Max pH Target", 6.2, 7.5, 6.8, 0.1)
        min_foam_opt = st.slider("Min Initial Foam (mm)", 80.0, 160.0, 120.0)
        
        run_opt = st.button("💰 Solve Cheapest Formula")
        
    with col_opt_out:
        if run_opt:
            st.markdown("#### **2. Optimal Recipe & Cost Summary**")
            opt_inputs, cost, properties = optimizer.solve_constrained_minimum_cost(
                min_visc_opt, max_visc_opt, min_ph_opt, max_ph_opt, min_foam_opt
            )
            
            # Baseline midpoint cost calculation
            mid_cost = (11.5 * 0.12) + (4.0 * 0.15) + (2.0 * 0.02)
            cost_saving = ((mid_cost - cost) / mid_cost) * 100.0
            
            scol1, scol2 = st.columns(2)
            with scol1:
                st.success(f"**Optimal Batch Cost:** {cost:.3f} INR / 100g")
                st.metric("Cost Reduction vs. Baseline", f"{cost_saving:.1f}%")
                
                recipe_df = pd.DataFrame([{
                    "SLES % (Primary Surfactant)": f"{opt_inputs['SLES_pct']}% w/w",
                    "CAPB % (Co-Surfactant)": f"{opt_inputs['CAPB_pct']}% w/w",
                    "NaCl % (Electrolyte)": f"{opt_inputs['NaCl_pct']}% w/w",
                    "Water (Balance)": f"{opt_inputs['water_pct']}% w/w"
                }]).T
                recipe_df.columns = ["Formula Value"]
                st.table(recipe_df)
                
            with scol2:
                st.info("Predicted Properties for Optimized Formula:")
                properties_df = pd.DataFrame([{
                    "Viscosity (Efflux time)": f"{properties['viscosity_sec']:.1f} Sec (Target: {min_visc_opt}-{max_visc_opt})",
                    "pH Level": f"{properties['ph']:.2f} (Target: {min_ph_opt}-{max_ph_opt})",
                    "Initial Foam Height": f"{properties['foam_height_initial_mm']:.1f} mm (Target: > {min_foam_opt})",
                    "5-Min Foam Stability": f"{properties['foam_height_5min_mm']:.1f} mm"
                }]).T
                properties_df.columns = ["Simulation Output"]
                st.table(properties_df)

    st.markdown("---")
    st.markdown("#### **3. Cost-Performance Pareto Front (Trade-off Curve)**")
    st.write(
        "By varying the target foam height constraint, we map the **Pareto Front** — the boundary of "
        "mathematically optimal formulas where you cannot improve performance (foam height) without increasing cost."
    )
    
    if st.button("📈 Compute Pareto Front"):
        with st.spinner("Calculating optimal boundary points..."):
            pareto_df = optimizer.generate_pareto_front(min_visc_opt, max_visc_opt, min_ph_opt, max_ph_opt)
            
            if not pareto_df.empty:
                col_chart_p, col_table_p = st.columns([2, 1])
                
                with col_chart_p:
                    fig_p = px.line(
                        pareto_df,
                        x="Cost_100g",
                        y="ActualFoam",
                        markers=True,
                        labels={"Cost_100g": "Formulation Cost (INR per 100g batch)", "ActualFoam": "Initial Foam Height (mm)"},
                        title="R&D Pareto Front: Cost vs. Performance Trade-off"
                    )
                    # Style chart
                    fig_p.update_traces(line=dict(color="#059669", width=3), marker=dict(size=8, color="#0F172A"))
                    st.plotly_chart(fig_p, use_container_width=True)
                    
                with col_table_p:
                    st.markdown("**Key Trade-off Highlights:**")
                    st.write("Below are three distinct business choices extracted from the Pareto Front:")
                    
                    # Highlight 3 choices
                    budget_idx = 0
                    premium_idx = len(pareto_df) - 1
                    balanced_idx = len(pareto_df) // 2
                    
                    highlights = []
                    for idx, label in [(budget_idx, "Budget Option"), (balanced_idx, "Balanced Option"), (premium_idx, "Premium Performance")]:
                        row = pareto_df.iloc[idx]
                        highlights.append({
                            "Tier": label,
                            "Cost (INR)": f"{row['Cost_100g']:.3f}",
                            "Foam (mm)": f"{row['ActualFoam']:.1f}",
                            "SLES %": f"{row['SLES_pct']:.2f}%",
                            "CAPB %": f"{row['CAPB_pct']:.2f}%"
                        })
                    st.dataframe(pd.DataFrame(highlights), hide_index=True)
            else:
                st.error("No valid Pareto Front found matching viscosity/pH targets.")

# ----------------- MODULE 5: AI LAB COPILOT -----------------
else:
    st.subheader("💬 AI Lab Copilot Agent")
    st.write("Ask natural language queries to search the LIMS experiment database, predict properties, or optimize recipes.")
    
    if "messages" not in st.session_state:
        st.session_state.messages = [
            {"role": "assistant", "content": "Hello! I am your FormuAI R&D agent. You can ask me to: <br/>1. *'Show experiments by Madhura'*<br/>2. *'Predict properties for SLES 13 and Salt 2.2'*<br/>3. *'Design shampoo with viscosity 45 and ph 6.0'*" }
        ]
        
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"], unsafe_allow_html=True)
            
    if user_query := st.chat_input("Ask lab agent..."):
        with st.chat_message("user"):
            st.markdown(user_query)
        st.session_state.messages.append({"role": "user", "content": user_query})
        
        res = agent.process_prompt(user_query)
        
        with st.chat_message("assistant"):
            st.markdown(res["message"])
            if res["intent"] == "lims_query":
                st.code(res["sql_executed"], language="sql")
                if res["records"]:
                    st.dataframe(pd.DataFrame(res["records"]))
                else:
                    st.warning("No matching trials found in LIMS database.")
            elif res["intent"] in ["predict", "design"]:
                col_i, col_o = st.columns(2)
                with col_i:
                    st.markdown("**Formulation Recipe:**")
                    st.json(res["composition"])
                with col_o:
                    st.markdown("**Predicted Attributes:**")
                    st.json(res["predicted_properties"])
                    
            st.session_state.messages.append({"role": "assistant", "content": res["message"]})
