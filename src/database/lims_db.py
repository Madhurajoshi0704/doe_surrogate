import os
import sqlite3
import numpy as np
import pandas as pd
from typing import Dict, Any, List, Tuple

DB_PATH = "lims_experiments.db"

def generate_ccd_matrix() -> np.ndarray:
    """
    Generate a 3-factor Central Composite Design (CCD) matrix.
    If pyDOE2 is available, use it. Otherwise, generate manually:
    - 8 factorial (cube) points: (+-1, +-1, +-1)
    - 6 axial (star) points: (+-alpha, 0, 0), (0, +-alpha, 0), (0, 0, +-alpha)
      with alpha = 1.682 (rotatable for 3 factors)
    - 6 center points: (0, 0, 0)
    Total = 20 runs.
    """
    try:
        import pyDOE2
        # ccdesign returns the coded matrix
        mat = pyDOE2.ccdesign(3, center=(6, 0)) # 6 center points
        # pyDOE2 center=(6,0) creates a CCD with 6 center runs
        return mat
    except ImportError:
        # Manual fallback generation of 3-factor CCD (alpha = 1.682)
        alpha = 1.682
        cube = []
        for x1 in [-1.0, 1.0]:
            for x2 in [-1.0, 1.0]:
                for x3 in [-1.0, 1.0]:
                    cube.append([x1, x2, x3])
        axial = [
            [-alpha, 0, 0], [alpha, 0, 0],
            [0, -alpha, 0], [0, alpha, 0],
            [0, 0, -alpha], [0, 0, alpha]
        ]
        centers = [[0.0, 0.0, 0.0] for _ in range(6)]
        return np.array(cube + axial + centers)

def scale_coded_to_actual(coded_matrix: np.ndarray) -> np.ndarray:
    """
    Scale coded factor coordinates [-1.682, +1.682] to real chemical bounds:
    - SLES %: Center=11.5, Range=[8.0, 15.0]  (Step factor: (15-8)/(2*1.682) = 2.08)
    - CAPB %: Center=4.0, Range=[2.0, 6.0]    (Step factor: (6-2)/(2*1.682) = 1.19)
    - NaCl %: Center=2.0, Range=[1.0, 3.0]    (Step factor: (3-1)/(2*1.682) = 0.595)
    """
    actual = np.zeros_like(coded_matrix)
    
    # SLES
    actual[:, 0] = 11.5 + coded_matrix[:, 0] * 2.08
    # CAPB
    actual[:, 1] = 4.0 + coded_matrix[:, 1] * 1.19
    # NaCl
    actual[:, 2] = 2.0 + coded_matrix[:, 2] * 0.595
    
    # Clip values to protect physical boundary constraints (> 0%)
    actual[:, 0] = np.clip(actual[:, 0], 5.0, 18.0)
    actual[:, 1] = np.clip(actual[:, 1], 1.0, 8.0)
    actual[:, 2] = np.clip(actual[:, 2], 0.1, 4.0)
    
    return np.round(actual, 3)

def init_lims_db(db_path: str = DB_PATH) -> str:
    """Initialize SQLite LIMS database tables representing laboratory notebooks."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS experiments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        batch_id TEXT UNIQUE NOT NULL,
        run_number INTEGER NOT NULL,
        date TEXT NOT NULL,
        operator TEXT NOT NULL,
        SLES_pct REAL NOT NULL,
        CAPB_pct REAL NOT NULL,
        NaCl_pct REAL NOT NULL,
        water_pct REAL NOT NULL,
        viscosity_sec REAL NOT NULL,
        foam_height_initial_mm REAL NOT NULL,
        foam_height_5min_mm REAL NOT NULL,
        ph REAL NOT NULL,
        clarity_score INTEGER NOT NULL,
        replicate_flag INTEGER NOT NULL,
        notes TEXT
    );
    """)
    
    conn.commit()
    
    # Check if table already contains seeded CCD data
    cursor.execute("SELECT COUNT(*) FROM experiments")
    if cursor.fetchone()[0] == 0:
        seed_ccd_experiments(conn)
        
    conn.close()
    return os.path.abspath(db_path)

def seed_ccd_experiments(conn: sqlite3.Connection):
    """Seed the database with physical measurements computed from a simulated CCD system."""
    cursor = conn.cursor()
    coded = generate_ccd_matrix()
    actual = scale_coded_to_actual(coded)
    
    for idx, (row_coded, row_actual) in enumerate(zip(coded, actual)):
        sles, capb, nacl = row_actual
        water = round(100.0 - (sles + capb + nacl), 3)
        
        # Check if this is a center point replicate
        is_replicate = 1 if np.all(np.abs(row_coded) < 0.01) else 0
        
        # Simulate physical measurements based on formulations (Quadratic RSM equations + random noise)
        
        # 1. Viscosity (efflux cup time in seconds)
        # Salt viscosity curve: peaks around 2.0% salt, over-salting reduces viscosity. SLES increases it.
        visc_base = 25.0 + (sles - 11.5) * 4.0 + (capb - 4.0) * 1.5 - ((nacl - 2.0) ** 2) * 40.0
        viscosity_sec = max(5.0, round(visc_base + np.random.normal(0, 1.5), 1))
        
        # 2. Foam heights: driven by primary and co-surfactants
        foam_init = 100.0 + (sles - 11.5) * 12.0 + (capb - 4.0) * 5.0
        foam_height_initial_mm = max(30.0, round(foam_init + np.random.normal(0, 3.0), 1))
        
        # Foam decay after 5 min (stability indicator)
        foam_decay = foam_height_initial_mm * (0.92 - (nacl - 2.0) * 0.04) # High salt degrades stability slightly
        foam_height_5min_mm = max(10.0, round(foam_decay + np.random.normal(0, 2.0), 1))
        
        # 3. pH: SLES & CAPB buffer around 6.2. Add a tiny noise.
        ph = max(4.0, min(8.5, round(6.2 + (sles * 0.02) - (capb * 0.05) + np.random.normal(0, 0.15), 2)))
        
        # 4. Clarity: Scale 1-5. High salt or high temp makes it cloudy.
        clarity = 5 if nacl < 2.5 else (4 if nacl < 3.2 else 3)
        
        batch_id = f"B-SHAMPOO-CCD-{idx+1:02d}"
        date_str = "2026-07-14"
        operator = "Madhura Joshi"
        notes = "Center point replicate" if is_replicate else "CCD Factorial/Axial point"
        
        cursor.execute("""
            INSERT INTO experiments (
                batch_id, run_number, date, operator, SLES_pct, CAPB_pct, NaCl_pct, water_pct,
                viscosity_sec, foam_height_initial_mm, foam_height_5min_mm, ph, clarity_score,
                replicate_flag, notes
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            batch_id, idx+1, date_str, operator, sles, capb, nacl, water,
            viscosity_sec, foam_height_initial_mm, foam_height_5min_mm, ph, clarity,
            is_replicate, notes
        ))
        
    conn.commit()

def get_lims_dataframe(db_path: str = DB_PATH) -> pd.DataFrame:
    """Retrieve full database table as a Pandas DataFrame."""
    conn = sqlite3.connect(db_path)
    df = pd.read_sql_query("SELECT * FROM experiments", conn)
    conn.close()
    return df

def run_custom_query(query: str, params: Tuple = (), db_path: str = DB_PATH) -> List[Tuple]:
    """Execute raw SQL statements (for Agent SQL capability)."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    try:
        cursor.execute(query, params)
        results = cursor.fetchall()
        columns = [col[0] for col in cursor.description] if cursor.description else []
        return columns, results
    except Exception as e:
        return ["Error"], [(str(e),)]
    finally:
        conn.close()
