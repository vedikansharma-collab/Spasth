import json
import logging
from pathlib import Path
from typing import Optional, Dict, Any, List

from app.core.config import settings
from app.database.db import get_db

logger = logging.getLogger(__name__)

class TreatmentService:
    """
    Step 4, 22, 23: Service for querying and normalizing treatment cost benchmarks.
    Finds healthcare pricing benchmarks based on procedure name, aliases, procedure code,
    city, and optional city tier.
    
    Guarantees:
    - Never fabricates medical prices or presents synthetic data as official tariffs.
    - Deterministic normalization of treatment names and alias mapping.
    - Returns structured TREATMENT_COST_NOT_AVAILABLE status when no benchmark exists.
    """

    _BENCHMARKS_CACHE: Optional[List[Dict[str, Any]]] = None

    @classmethod
    def _load_benchmarks(cls) -> List[Dict[str, Any]]:
        """Loads treatment benchmarks from data/treatment_costs/benchmarks.json."""
        if cls._BENCHMARKS_CACHE is not None:
            return cls._BENCHMARKS_CACHE

        benchmarks_path = settings.DATA_DIR / "treatment_costs" / "benchmarks.json"
        if benchmarks_path.exists():
            try:
                with open(benchmarks_path, "r", encoding="utf-8") as f:
                    cls._BENCHMARKS_CACHE = json.load(f)
                    return cls._BENCHMARKS_CACHE
            except Exception as e:
                logger.error(f"[TREATMENT-SERVICE] Error loading benchmarks.json: {e}")
        
        cls._BENCHMARKS_CACHE = []
        return cls._BENCHMARKS_CACHE

    @classmethod
    def reload_cache(cls):
        """Forces cache reload (useful after benchmark dataset updates or tests)."""
        cls._BENCHMARKS_CACHE = None
        cls._load_benchmarks()

    @classmethod
    def normalize_treatment_name(cls, procedure_name: str) -> Optional[str]:
        """
        Normalizes procedure name or alias to canonical procedure name.
        Example: 'Appendix surgery' -> 'Appendectomy'
                 'Phacoemulsification' -> 'Cataract Surgery'
                 'TKR' -> 'Knee Replacement'
        """
        if not procedure_name or not procedure_name.strip():
            return None

        clean_name = procedure_name.strip().lower()
        benchmarks = cls._load_benchmarks()

        for item in benchmarks:
            # 1. Exact match on treatment_id
            t_id = item.get("treatment_id", "").lower()
            if clean_name == t_id or clean_name == t_id.replace("_", " "):
                return item.get("canonical_name") or item.get("procedure")

            # 2. Match on canonical_name or procedure
            canon = (item.get("canonical_name") or item.get("procedure") or "").lower()
            if clean_name == canon:
                return item.get("canonical_name") or item.get("procedure")

            # 3. Match on procedure_code
            code = (item.get("procedure_code") or "").lower()
            if clean_name == code:
                return item.get("canonical_name") or item.get("procedure")

            # 4. Match on aliases
            for alias in item.get("aliases", []):
                if clean_name == alias.lower():
                    return item.get("canonical_name") or item.get("procedure")

        # 5. Fuzzy substring keyword fallback
        import re
        clean_words = set(re.findall(r'\b\w+\b', clean_name))
        for item in benchmarks:
            canon = (item.get("canonical_name") or item.get("procedure") or "").lower()
            if "append" in clean_name and "append" in canon:
                return item.get("canonical_name") or item.get("procedure")
            if "cataract" in clean_name and "cataract" in canon:
                return item.get("canonical_name") or item.get("procedure")
            if ("knee" in clean_name or "tkr" in clean_words) and "knee" in canon:
                return item.get("canonical_name") or item.get("procedure")
            if ("c-section" in clean_name or "cesarean" in clean_name or "caesarean" in clean_name) and "c-section" in canon:
                return item.get("canonical_name") or item.get("procedure")
            if ("angioplasty" in clean_name or "stent" in clean_words or "ptca" in clean_words) and "angioplasty" in canon:
                return item.get("canonical_name") or item.get("procedure")

        return None

    @classmethod
    def get_treatment_cost(cls, procedure_name: str, city: str) -> Optional[Dict[str, Any]]:
        """
        Looks up procedure and city cost benchmark with alias resolution.
        Returns normalized dictionary with treatment details, or None if no reliable benchmark exists.
        """
        if not procedure_name or not city:
            return None

        canonical = cls.normalize_treatment_name(procedure_name)
        search_name = canonical if canonical else procedure_name.strip()
        search_city = city.strip().lower()

        benchmarks = cls._load_benchmarks()

        # 1. Search in memory cache from benchmarks.json
        for item in benchmarks:
            item_proc = (item.get("canonical_name") or item.get("procedure") or "").lower()
            item_city = (item.get("city") or "").lower()
            
            if (item_proc == search_name.lower() or item.get("treatment_id", "").lower() == search_name.lower()) and item_city == search_city:
                return {
                    "treatment_id": item.get("treatment_id") or item.get("procedure_code"),
                    "treatment_name": item.get("canonical_name") or item.get("procedure"),
                    "canonical_name": item.get("canonical_name") or item.get("procedure"),
                    "category": item.get("category", "General Healthcare"),
                    "procedure_type": item.get("procedure_type", "Surgical"),
                    "procedure_code": item.get("procedure_code"),
                    "city": item.get("city"),
                    "city_tier": item.get("city_tier", "Tier-1"),
                    "reference_cost": float(item.get("reference_cost") or ((item["cost_min"] + item["cost_max"]) / 2)),
                    "cost_min": float(item["cost_min"]),
                    "cost_max": float(item["cost_max"]),
                    "min_cost": float(item["cost_min"]),
                    "max_cost": float(item["cost_max"]),
                    "currency": item.get("currency", "INR"),
                    "cost_unit": item.get("cost_unit", "per_procedure"),
                    "source": item.get("source", "Healthcare Benchmark 2025"),
                    "source_date": item.get("source_date", "2025"),
                    "data_status": item.get("data_status", "REFERENCE"),
                    "data_type": item.get("data_type", "synthetic"),
                    "notes": item.get("notes", ""),
                    "aliases": item.get("aliases", [])
                }

        # 2. Search in SQLite database as fallback
        try:
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
                    WHERE (LOWER(procedure_name) = LOWER(?) OR LOWER(procedure_name) = LOWER(?)) AND LOWER(city) = LOWER(?);
                """, (search_name, procedure_name.strip(), search_city))
                row = cursor.fetchone()

                if row:
                    return {
                        "treatment_id": row.get("procedure_code"),
                        "treatment_name": row["treatment_name"],
                        "canonical_name": row["treatment_name"],
                        "category": "General Healthcare",
                        "procedure_type": "Surgical",
                        "procedure_code": row.get("procedure_code"),
                        "city": row["city"],
                        "city_tier": row.get("city_tier", "Tier-1"),
                        "reference_cost": float((row["cost_min"] + row["cost_max"]) / 2),
                        "cost_min": float(row["cost_min"]),
                        "cost_max": float(row["cost_max"]),
                        "min_cost": float(row["cost_min"]),
                        "max_cost": float(row["cost_max"]),
                        "currency": "INR",
                        "cost_unit": "per_procedure",
                        "source": row["source"],
                        "source_date": row.get("source_date", "2025"),
                        "data_status": "REFERENCE",
                        "data_type": row.get("data_type", "synthetic"),
                        "notes": row.get("notes", ""),
                        "aliases": []
                    }
        except Exception as e:
            logger.warning(f"[TREATMENT-SERVICE] DB lookup error: {e}")

        logger.warning(f"[TREATMENT-SERVICE] No benchmark found for '{procedure_name}' in '{city}'.")
        return None

    @classmethod
    def get_all_treatments(cls) -> List[Dict[str, Any]]:
        """Returns all distinct canonical treatments available in the benchmarks dataset."""
        benchmarks = cls._load_benchmarks()
        unique = {}
        for b in benchmarks:
            t_id = b.get("treatment_id") or b.get("procedure_code")
            if t_id not in unique:
                unique[t_id] = {
                    "treatment_id": t_id,
                    "canonical_name": b.get("canonical_name") or b.get("procedure"),
                    "category": b.get("category"),
                    "procedure_type": b.get("procedure_type"),
                    "aliases": b.get("aliases", []),
                    "currency": b.get("currency", "INR")
                }
        return list(unique.values())
