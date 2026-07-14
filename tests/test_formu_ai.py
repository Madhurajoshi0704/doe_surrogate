import os
import sqlite3
import pytest
import numpy as np
import pandas as pd

TEST_DB = "test_lims_experiments.db"
TEST_MODEL = "test_dual_models.pkl"

from src.database.lims_db import init_lims_db, get_lims_dataframe, run_custom_query, generate_ccd_matrix
from src.models.dual_modeling import DualModelingEngine, get_quadratic_features
from src.agent.lab_copilot import LabCopilotAgent

@pytest.fixture(scope="module", autouse=True)
def clean_test_files():
    """Wipe mock testing outputs after module is finished."""
    yield
    for f in [TEST_DB, TEST_MODEL]:
        if os.path.exists(f):
            os.remove(f)

def test_ccd_generation_and_seeding():
    # 1. Assert CCD produces 20 runs
    mat = generate_ccd_matrix()
    assert mat.shape == (20, 3)

    # 2. Assert LIMS db seeds table with 20 rows
    db_path = init_lims_db(TEST_DB)
    assert os.path.exists(db_path)
    
    df = get_lims_dataframe(TEST_DB)
    assert len(df) == 20
    assert 'SLES_pct' in df.columns
    assert 'viscosity_sec' in df.columns

def test_dual_modeling_engine():
    df = get_lims_dataframe(TEST_DB)
    engine = DualModelingEngine(model_path=TEST_MODEL)
    
    # Train
    metrics_df = engine.fit_and_evaluate(df)
    assert len(metrics_df) == 4 # 4 response variables
    assert "RSM R² (Train)" in metrics_df.columns
    assert "RF R² (Train)" in metrics_df.columns

    # Verify OLS features mapping
    X_raw = df[['SLES_pct', 'CAPB_pct', 'NaCl_pct']]
    X_poly = get_quadratic_features(X_raw)
    assert 'SLES_CAPB' in X_poly.columns # Interaction
    assert 'SLES_sq' in X_poly.columns   # Quadratic
    assert 'const' in X_poly.columns     # Intercept

    # Inference predictions test
    sample = {'SLES_pct': 11.5, 'CAPB_pct': 4.0, 'NaCl_pct': 2.0, 'water_pct': 82.5}
    rsm_preds = engine.predict("RSM", sample)
    rf_preds = engine.predict("RF", sample)
    
    assert rsm_preds['viscosity_sec'] > 0
    assert rf_preds['viscosity_sec'] > 0
    assert 4.0 <= rsm_preds['ph'] <= 8.5

    # Sensitivity generation
    sens = engine.get_sensitivity_data("SLES_pct", sample, points=5)
    assert len(sens) == 5
    assert "RSM_viscosity_sec" in sens.columns

    # Optimization target solver test
    best_in, best_out = engine.optimize_formulation(40.0, 6.0)
    assert best_in is not None
    assert abs(best_out['ph'] - 6.0) < 1.0

def test_agent_prompts_routing():
    agent = LabCopilotAgent()
    agent.engine = DualModelingEngine(model_path=TEST_MODEL)
    agent.engine.load_models()

    # Query Intent
    res_q = agent.process_prompt("Show experiments by Madhura")
    assert res_q["intent"] == "lims_query"
    assert len(res_q["records"]) > 0

    # Predict Intent
    res_p = agent.process_prompt("Predict viscosity for SLES 13.0 and Salt 2.5")
    assert res_p["intent"] == "predict"
    assert res_p["composition"]["SLES_pct"] == 13.0
    assert res_p["composition"]["NaCl_pct"] == 2.5
    assert "predicted_properties" in res_p

    # Design/Optimize Intent
    res_d = agent.process_prompt("Design shampoo with viscosity 45 and ph 6.2")
    assert res_d["intent"] == "design"
    assert res_d["predicted_properties"]["viscosity_sec"] > 0

def test_cost_optimization():
    from src.models.optimizer import CostPerformanceOptimizer
    opt = CostPerformanceOptimizer()
    opt.engine = DualModelingEngine(model_path=TEST_MODEL)
    opt.engine.load_models()
    
    # Run optimization
    inputs, cost, properties = opt.solve_constrained_minimum_cost(
        min_visc=20.0, max_visc=50.0, min_ph=5.5, max_ph=6.8, min_foam=110.0
    )
    
    assert inputs is not None
    assert cost > 0.0
    assert 20.0 <= properties['viscosity_sec'] <= 50.0
    assert properties['ph'] >= 5.3
    
    # Generate Pareto front
    pareto = opt.generate_pareto_front(min_visc=20.0, max_visc=50.0, min_ph=5.5, max_ph=6.8, points=5)
    assert not pareto.empty
    assert "Cost_100g" in pareto.columns
