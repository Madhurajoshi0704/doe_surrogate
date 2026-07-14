import numpy as np
import pandas as pd
from scipy.optimize import differential_evolution
from typing import Dict, Any, Tuple, List

from src.models.dual_modeling import DualModelingEngine

# Bulk active ingredient unit costs (INR per gram)
# SLES: 120 INR/kg = 0.12 INR/g
# CAPB: 150 INR/kg = 0.15 INR/g
# NaCl: 20 INR/kg = 0.02 INR/g
# Water: 0.00 INR/g
COSTS = {
    'SLES_pct': 0.12,
    'CAPB_pct': 0.15,
    'NaCl_pct': 0.02
}

def calculate_formulation_cost(sles: float, capb: float, nacl: float) -> float:
    """Calculate the cost of a 100g formulation batch in INR."""
    return (sles * COSTS['SLES_pct']) + (capb * COSTS['CAPB_pct']) + (nacl * COSTS['NaCl_pct'])

class CostPerformanceOptimizer:
    def __init__(self):
        self.engine = DualModelingEngine()
        self.engine.load_models()
        # Bounded limits matching our tested DOE CCD range
        self.bounds = [
            (5.0, 18.0),  # SLES %
            (1.0, 8.0),   # CAPB %
            (0.1, 4.0)    # NaCl %
        ]

    def solve_constrained_minimum_cost(
        self,
        min_visc: float,
        max_visc: float,
        min_ph: float,
        max_ph: float,
        min_foam: float
    ) -> Tuple[Dict[str, float], float, Dict[str, float]]:
        """
        Solves for the cheapest formulation meeting target physical specs
        using scipy.optimize.differential_evolution.
        """
        # Objective: minimize cost
        def objective(factors):
            sles, capb, nacl = factors
            return calculate_formulation_cost(sles, capb, nacl)
            
        # Non-linear constraints modeled as a penalty function for differential_evolution
        def penalty_objective(factors):
            sles, capb, nacl = factors
            cost = calculate_formulation_cost(sles, capb, nacl)
            
            inputs = {
                'SLES_pct': sles,
                'CAPB_pct': capb,
                'NaCl_pct': nacl,
                'water_pct': round(100.0 - (sles + capb + nacl), 3)
            }
            # Predict properties using RSM model
            preds = self.engine.predict("RSM", inputs)
            
            penalty = 0.0
            
            # Viscosity penalty
            if preds['viscosity_sec'] < min_visc:
                penalty += ((preds['viscosity_sec'] - min_visc) ** 2) * 50.0
            elif preds['viscosity_sec'] > max_visc:
                penalty += ((preds['viscosity_sec'] - max_visc) ** 2) * 50.0
                
            # pH penalty
            if preds['ph'] < min_ph:
                penalty += ((preds['ph'] - min_ph) ** 2) * 1000.0
            elif preds['ph'] > max_ph:
                penalty += ((preds['ph'] - max_ph) ** 2) * 1000.0
                
            # Foam height penalty
            if preds['foam_height_initial_mm'] < min_foam:
                penalty += ((preds['foam_height_initial_mm'] - min_foam) ** 2) * 10.0
                
            return cost + penalty

        # Solve
        res = differential_evolution(penalty_objective, self.bounds, seed=42)
        
        sles, capb, nacl = res.x
        water = round(100.0 - (sles + capb + nacl), 3)
        
        best_inputs = {
            'SLES_pct': round(sles, 3),
            'CAPB_pct': round(capb, 3),
            'NaCl_pct': round(nacl, 3),
            'water_pct': water
        }
        cost = calculate_formulation_cost(sles, capb, nacl)
        properties = self.engine.predict("RSM", best_inputs)
        
        return best_inputs, float(cost), properties

    def generate_pareto_front(
        self,
        min_visc: float,
        max_visc: float,
        min_ph: float,
        max_ph: float,
        points: int = 15
    ) -> pd.DataFrame:
        """
        Generates the Pareto front (Cost vs. Performance) using the epsilon-constraint method.
        Varies target foam height constraint and solves for minimum cost.
        """
        # Determine foam height boundaries by predicting midpoint values
        mid_inputs = {'SLES_pct': 11.5, 'CAPB_pct': 4.0, 'NaCl_pct': 2.0, 'water_pct': 82.5}
        mid_preds = self.engine.predict("RSM", mid_inputs)
        mid_foam = mid_preds['foam_height_initial_mm']
        
        # Grid range of target foam heights to solve (e.g. from low 80mm to high 160mm)
        foam_targets = np.linspace(mid_foam - 40.0, mid_foam + 30.0, points)
        
        pareto_records = []
        
        for target_foam in foam_targets:
            try:
                inputs, cost, properties = self.solve_constrained_minimum_cost(
                    min_visc, max_visc, min_ph, max_ph, target_foam
                )
                
                # Verify that the constraint was met within a small tolerance
                if properties['foam_height_initial_mm'] >= (target_foam - 5.0):
                    pareto_records.append({
                        "TargetFoam": round(target_foam, 1),
                        "ActualFoam": round(properties['foam_height_initial_mm'], 1),
                        "Cost_100g": round(cost, 3),
                        "SLES_pct": inputs['SLES_pct'],
                        "CAPB_pct": inputs['CAPB_pct'],
                        "NaCl_pct": inputs['NaCl_pct'],
                        "Viscosity": round(properties['viscosity_sec'], 1),
                        "pH": round(properties['ph'], 2)
                    })
            except Exception:
                continue
                
        df_pareto = pd.DataFrame(pareto_records)
        if not df_pareto.empty:
            # Sort by cost to render curve correctly
            df_pareto = df_pareto.sort_values(by="Cost_100g").reset_index(drop=True)
        return df_pareto
