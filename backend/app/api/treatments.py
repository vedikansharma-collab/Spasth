from fastapi import APIRouter
from app.services.treatment_service import TreatmentService
from app.schemas.estimate import TreatmentsResponse

router = APIRouter(prefix="/treatments", tags=["Treatments"])

@router.get("", response_model=TreatmentsResponse)
def get_treatment_metadata():
    """
    GET /api/treatments
    Fetches available canonical medical procedures, cities, room categories, and benchmark dataset.
    """
    benchmarks = TreatmentService._load_benchmarks()
    procedures = sorted(list(set(
        b.get("canonical_name") or b.get("procedure")
        for b in benchmarks
        if (b.get("canonical_name") or b.get("procedure"))
    )))
    cities = sorted(list(set(
        b.get("city")
        for b in benchmarks
        if b.get("city")
    )))

    return TreatmentsResponse(
        procedures=procedures if procedures else ["Appendectomy", "Cataract Surgery", "Knee Replacement", "C-Section", "Angioplasty"],
        cities=cities if cities else ["Pune", "Mumbai", "Nagpur"],
        room_categories=["Standard", "Deluxe"],
        benchmarks=benchmarks
    )
