from fastapi import APIRouter, Depends, Request

from app.models.poi import POIRequest, POIResponse
from app.services.enrichment import EnrichmentService

router = APIRouter()


def get_service(request: Request) -> EnrichmentService:
    return request.app.state.enrichment_service


@router.post("/poi-details", response_model=POIResponse)
async def poi_details(payload: POIRequest, service: EnrichmentService = Depends(get_service)):
    document = await service.get_poi_details(payload)
    return POIResponse(**document.model_dump())


@router.get("/health", include_in_schema=False)
async def healthcheck():
    return {"status": "ok"}
