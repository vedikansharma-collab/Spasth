import logging
from typing import Optional, Dict, Any
from app.database.db import get_db

logger = logging.getLogger(__name__)

class TreatmentService:
    """
    Step 4 & 5: Service for querying treatment cost benchmarks.
    Finds healthcare pricing benchmarks based on procedure name, city, and optional city tier.
    Guarantees synthetic/demo data is explicitly marked and never invented.
    """

    @staticmethod
    def get_treatment_cost(procedure_name: str, city: str) -> Optional[Dict[str, Any]]:
        """
        Looks up procedure and city cost benchmark.
        Returns dictionary with treatment details, or None if no reliable benchmark exists.
        """
        if not procedure_name or not city:
            return None

        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT 
                    procedure_name AS treatment_name,
                    procedure_code,
                    city,
                    city_tier,
                    min_cost AS cost_min,
                    max_cost AS cost_max,
                    source,
                    source_date,
                    notes,
                    data_type
                FROM treatment_costs 
                WHERE LOWER(procedure_name) = LOWER(?) AND LOWER(city) = LOWER(?);
            """, (procedure_name.strip(), city.strip()))
            row = cursor.fetchone()

            if row:
                return {
                    "treatment_name": row["treatment_name"],
                    "procedure_code": row.get("procedure_code"),
                    "city": row["city"],
                    "city_tier": row.get("city_tier", "Tier-1"),
                    "cost_min": float(row["cost_min"]),
                    "cost_max": float(row["cost_max"]),
                    "source": row["source"],
                    "source_date": row.get("source_date", "2025"),
                    "notes": row.get("notes", ""),
                    "data_type": row.get("data_type", "synthetic")
                }

        logger.warning(f"[TREATMENT-SERVICE] No benchmark found for '{procedure_name}' in '{city}'.")
        return None
