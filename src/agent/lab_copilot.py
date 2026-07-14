import re
from typing import Dict, Any, Tuple, List
from src.database.lims_db import run_custom_query
from src.models.dual_modeling import DualModelingEngine

class LabCopilotAgent:
    def __init__(self):
        self.engine = DualModelingEngine()
        self.engine.load_models()

    def process_prompt(self, prompt: str) -> Dict[str, Any]:
        """
        AI Agent interpreter:
        1. Identify intent (design/optimize, predict/simulate, or search LIMS database).
        2. Parse chemical ratios and parameters.
        3. Query LIMS database or compute predictions using DualModelingEngine.
        """
        p = prompt.lower().strip()
        
        # --- Intent 1: AI Formulation Design (Optimization) ---
        if "design" in p or "optimize" in p:
            visc_match = re.search(r'(?:viscosity|visc)\s*(?:of|around|==|value)?\s*(\d+(?:\.\d+)?)', p)
            ph_match = re.search(r'ph\s*(?:of|around|==|value)?\s*(\d+(?:\.\d+)?)', p)
            
            target_visc = float(visc_match.group(1)) if visc_match else 30.0
            target_ph = float(ph_match.group(1)) if ph_match else 6.0
            
            inputs, outputs = self.engine.optimize_formulation(target_visc, target_ph)
            
            return {
                "intent": "design",
                "message": f"FormuAI Agent has run a virtual OLS-RSM optimization trial targeting **{target_visc} seconds** efflux cup viscosity and **{target_ph}** pH. Proposed recipe:",
                "composition": inputs,
                "predicted_properties": outputs
            }
            
        # --- Intent 2: Run Virtual Simulation (Prediction) ---
        elif "predict" in p or "simulate" in p:
            sles_match = re.search(r'sles\s*(\d+(?:\.\d+)?)', p)
            capb_match = re.search(r'capb\s*(\d+(?:\.\d+)?)', p)
            nacl_match = re.search(r'(?:nacl|salt)\s*(\d+(?:\.\d+)?)', p)
            
            sles = float(sles_match.group(1)) if sles_match else 11.5
            capb = float(capb_match.group(1)) if capb_match else 4.0
            nacl = float(nacl_match.group(1)) if nacl_match else 2.0
            water = round(100.0 - (sles + capb + nacl), 3)
            
            inputs = {
                'SLES_pct': sles,
                'CAPB_pct': capb,
                'NaCl_pct': nacl,
                'water_pct': water
            }
            
            outputs = self.engine.predict("RSM", inputs)
            
            return {
                "intent": "predict",
                "message": f"Successfully simulated OLS-RSM properties for formulation SLES={sles}%, CAPB={capb}%, NaCl={nacl}%:",
                "composition": inputs,
                "predicted_properties": outputs
            }

        # --- Intent 3: Search LIMS/ELN Database ---
        else:
            query = """
                SELECT 
                    batch_id, run_number, operator, SLES_pct, CAPB_pct, NaCl_pct, 
                    viscosity_sec, ph, replicate_flag
                FROM experiments
            """
            conditions = []
            params = []
            
            # Check for operator search
            operator_match = re.search(r'by\s+([a-zA-Z\s\.]+)', p)
            if operator_match:
                name = operator_match.group(1).strip()
                if "madhura" in name:
                    conditions.append("operator LIKE ?")
                    params.append("%Madhura Joshi%")
                else:
                    conditions.append("operator LIKE ?")
                    params.append(f"%{name}%")
            
            # Check for physical metrics filters
            visc_match = re.search(r'(?:viscosity|visc)\s*>\s*(\d+)', p)
            if visc_match:
                conditions.append("viscosity_sec > ?")
                params.append(float(visc_match.group(1)))
                
            replicate_match = "replicate" in p
            if replicate_match:
                conditions.append("replicate_flag = 1")

            if conditions:
                query += " WHERE " + " AND ".join(conditions)
            
            query += " ORDER BY run_number ASC LIMIT 10"
            
            columns, results = run_custom_query(query, tuple(params))
            
            data_list = []
            for row in results:
                data_list.append(dict(zip(columns, row)))
                
            return {
                "intent": "lims_query",
                "message": f"Queried historical LIMS database. Found **{len(results)}** experimental trials matching criteria:",
                "sql_executed": query,
                "records": data_list
            }
