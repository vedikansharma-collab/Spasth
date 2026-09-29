from fastapi import APIRouter
from app.database.db import get_db
from app.schemas.estimate import TreatmentsResponse

router = APIRouter(prefix="/treatments", tags=["Treatments"])

@router.get("", response_model=TreatmentsResponse)
def get_treatment_metadata():
    """
    GET /api/treatments
    Fetches available medical procedures, cities, and room categories in the cost dataset.
    """
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT DISTINCT procedure_name FROM treatment_costs ORDER BY procedure_name ASC;")
        procedures = [row["procedure_name"] for row in cursor.fetchall()]

        cursor.execute("SELECT DISTINCT city FROM treatment_costs ORDER BY city ASC;")
        cities = [row["city"] for row in cursor.fetchall()]

    return TreatmentsResponse(
        procedures=procedures if procedures else ["Appendectomy", "Cataract Surgery", "Knee Replacement", "C-Section", "Angioplasty"],
        cities=cities if cities else ["Pune", "Mumbai", "Nagpur"],
        room_categories=["Standard", "Deluxe"]
    )
