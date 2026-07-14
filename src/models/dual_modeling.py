import os
import pickle
import numpy as np
import pandas as pd
import statsmodels.api as sm
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import KFold
from typing import Dict, Any, Tuple, List

MODEL_PATH = "dual_models.pkl"

def get_quadratic_features(X: pd.DataFrame) -> pd.DataFrame:
    """
    Generate quadratic and interaction terms for a 3-factor dataset.
    Given columns [x1, x2, x3], creates:
    - Linear: x1, x2, x3
    - Interaction: x1_x2, x1_x3, x2_x3
    - Quadratic: x1_sq, x2_sq, x3_sq
    - Intercept: const (always 1)
    """
    cols = list(X.columns)
    df_poly = X.copy()
    
    # 1. Interaction terms
    df_poly['SLES_CAPB'] = X[cols[0]] * X[cols[1]]
    df_poly['SLES_NaCl'] = X[cols[0]] * X[cols[2]]
    df_poly['CAPB_NaCl'] = X[cols[1]] * X[cols[2]]
    
    # 2. Quadratic terms
    df_poly['SLES_sq'] = X[cols[0]] ** 2
    df_poly['CAPB_sq'] = X[cols[1]] ** 2
    df_poly['NaCl_sq'] = X[cols[2]] ** 2
    
    # 3. Intercept
    df_poly = sm.add_constant(df_poly, has_constant='add')
    return df_poly

class DualModelingEngine:
    def __init__(self, model_path: str = MODEL_PATH):
        self.model_path = model_path
        self.input_cols = ['SLES_pct', 'CAPB_pct', 'NaCl_pct']
        self.output_cols = ['viscosity_sec', 'foam_height_initial_mm', 'foam_height_5min_mm', 'ph']
        
        # Store models
        self.rsm_models = {}   # Dict containing statsmodels OLS Results
        self.rf_models = {}    # Dict containing trained RandomForestRegressor models
        self.metrics_df = None  # Comparison table

    def fit_and_evaluate(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Fits classical Response Surface Methodology (RSM) OLS models
        and modern Random Forest Regressors, comparing accuracy scores.
        """
        comparison_records = []
        kf = KFold(n_splits=5, shuffle=True, random_state=42)
        
        X_raw = df[self.input_cols]
        X_rsm = get_quadratic_features(X_raw)
        
        for col in self.output_cols:
            y = df[col]
            
            # --- 1. Classical RSM Fit ---
            rsm_model = sm.OLS(y, X_rsm).fit()
            self.rsm_models[col] = rsm_model
            
            # Cross-validated RSM metrics
            rsm_cv_preds = np.zeros(len(y))
            for train_idx, val_idx in kf.split(X_raw):
                X_train_cv, X_val_cv = X_rsm.iloc[train_idx], X_rsm.iloc[val_idx]
                y_train_cv = y.iloc[train_idx]
                
                cv_model = sm.OLS(y_train_cv, X_train_cv).fit()
                rsm_cv_preds[val_idx] = cv_model.predict(X_val_cv)
                
            rsm_rmse_cv = np.sqrt(np.mean((y - rsm_cv_preds) ** 2))
            
            # --- 2. Random Forest Fit ---
            rf = RandomForestRegressor(n_estimators=60, max_depth=8, random_state=42)
            rf.fit(X_raw, y)
            self.rf_models[col] = rf
            
            # Cross-validated Random Forest metrics
            rf_cv_preds = np.zeros(len(y))
            for train_idx, val_idx in kf.split(X_raw):
                X_train_cv, X_val_cv = X_raw.iloc[train_idx], X_raw.iloc[val_idx]
                y_train_cv, y_val_cv = y.iloc[train_idx], y.iloc[val_idx]
                
                cv_rf = RandomForestRegressor(n_estimators=60, max_depth=8, random_state=42)
                cv_rf.fit(X_train_cv, y_train_cv)
                rf_cv_preds[val_idx] = cv_rf.predict(X_val_cv)
                
            rf_rmse_cv = np.sqrt(np.mean((y - rf_cv_preds) ** 2))
            
            # Calculate CV R-squared for both
            rsm_cv_r2 = float(1 - (np.sum((y - rsm_cv_preds)**2) / np.sum((y - y.mean())**2)))
            rf_cv_r2 = float(1 - (np.sum((y - rf_cv_preds)**2) / np.sum((y - y.mean())**2)))
            
            comparison_records.append({
                "Response Variable": col,
                "RSM R² (Train)": round(float(rsm_model.rsquared), 3),
                "RSM R² (Adj)": round(float(rsm_model.rsquared_adj), 3),
                "RSM R² (5-Fold CV)": round(rsm_cv_r2, 3),
                "RSM RMSE (5-Fold CV)": round(rsm_rmse_cv, 2),
                "RF R² (Train)": round(float(rf.score(X_raw, y)), 3),
                "RF R² (5-Fold CV)": round(rf_cv_r2, 3),
                "RF RMSE (5-Fold CV)": round(rf_rmse_cv, 2)
            })
            
        self.metrics_df = pd.DataFrame(comparison_records)
        
        # Serialize models & metrics
        with open(self.model_path, "wb") as f:
            pickle.dump((self.rsm_models, self.rf_models, self.metrics_df), f)
            
        return self.metrics_df

    def load_models(self):
        """Load trained models from disk."""
        if not os.path.exists(self.model_path):
            from src.database.lims_db import get_lims_dataframe, init_lims_db
            db_path = "lims_experiments.db"
            if not os.path.exists(db_path):
                init_lims_db(db_path)
            df = get_lims_dataframe(db_path)
            self.fit_and_evaluate(df)
            
        with open(self.model_path, "rb") as f:
            self.rsm_models, self.rf_models, self.metrics_df = pickle.load(f)

    def predict(self, model_type: str, inputs: Dict[str, float]) -> Dict[str, float]:
        """
        Run virtual simulation predictions using either 'RSM' or 'RF' models.
        """
        if not self.rf_models:
            self.load_models()
            
        raw_df = pd.DataFrame([inputs])[self.input_cols]
        predictions = {}
        
        if model_type == "RSM":
            X_poly = get_quadratic_features(raw_df)
            for col in self.output_cols:
                predictions[col] = float(self.rsm_models[col].predict(X_poly)[0])
        else:
            for col in self.output_cols:
                predictions[col] = float(self.rf_models[col].predict(raw_df)[0])
                
        return predictions

    def get_sensitivity_data(self, factor: str, base_inputs: Dict[str, float], points: int = 20) -> pd.DataFrame:
        """
        Generates sensitivity curves demonstrating the response variable shift
        as a single factor is varied across its chemical bounds.
        """
        if not self.rf_models:
            self.load_models()
            
        bounds = {
            'SLES_pct': (5.0, 18.0),
            'CAPB_pct': (1.0, 8.0),
            'NaCl_pct': (0.1, 4.0)
        }
        
        low, high = bounds[factor]
        values = np.linspace(low, high, points)
        
        records = []
        for val in values:
            temp_inputs = base_inputs.copy()
            temp_inputs[factor] = val
            # Adjust water balance dynamically
            other_sum = sum(v for k, v in temp_inputs.items() if k in self.input_cols and k != factor)
            temp_inputs['water_pct'] = round(100.0 - (other_sum + val), 3)
            
            rsm_preds = self.predict("RSM", temp_inputs)
            rf_preds = self.predict("RF", temp_inputs)
            
            record = {
                "FactorValue": val,
                "SLES_pct": temp_inputs['SLES_pct'],
                "CAPB_pct": temp_inputs['CAPB_pct'],
                "NaCl_pct": temp_inputs['NaCl_pct']
            }
            # Append model predictions
            for col in self.output_cols:
                record[f"RSM_{col}"] = rsm_preds[col]
                record[f"RF_{col}"] = rf_preds[col]
                
            records.append(record)
            
        return pd.DataFrame(records)

    def optimize_formulation(self, target_viscosity: float, target_ph: float) -> Tuple[Dict[str, float], Dict[str, float]]:
        """
        AI target formulation solver using random search iterations.
        """
        best_inputs = None
        best_predictions = None
        min_loss = float('inf')

        for _ in range(2500):
            sles = round(np.random.uniform(8.0, 15.0), 2)
            capb = round(np.random.uniform(2.0, 6.0), 2)
            nacl = round(np.random.uniform(1.0, 3.0), 2)
            water = round(100.0 - (sles + capb + nacl), 3)
            
            candidate_inputs = {
                'SLES_pct': sles,
                'CAPB_pct': capb,
                'NaCl_pct': nacl,
                'water_pct': water
            }
            
            # Predict using RSM model
            preds = self.predict("RSM", candidate_inputs)
            
            # Normalize objective loss function
            loss = (((preds['viscosity_sec'] - target_viscosity) / 50.0) ** 2) + \
                   (((preds['ph'] - target_ph) / 2.0) ** 2)
            
            if loss < min_loss:
                min_loss = loss
                best_inputs = candidate_inputs
                best_predictions = preds

        return best_inputs, best_predictions
