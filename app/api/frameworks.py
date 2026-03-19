from fastapi import APIRouter, HTTPException

from app.frameworks import FRAMEWORK_REGISTRY
from app.schemas.framework import FrameworkListItem, FrameworkControls, ControlSchema

router = APIRouter(prefix="/frameworks", tags=["frameworks"])


@router.get("", response_model=list[FrameworkListItem])
async def list_frameworks():
    result = []
    for fw in FRAMEWORK_REGISTRY.values():
        result.append(FrameworkListItem(
            id=fw.id,
            name=fw.name,
            version=fw.version,
            control_count=len(fw.controls),
            families=fw.get_families(),
        ))
    return result


@router.get("/{framework_id}/controls", response_model=FrameworkControls)
async def get_framework_controls(framework_id: str):
    fw = FRAMEWORK_REGISTRY.get(framework_id)
    if not fw:
        raise HTTPException(status_code=404, detail=f"Framework '{framework_id}' not found")

    return FrameworkControls(
        id=fw.id,
        name=fw.name,
        version=fw.version,
        controls=[
            ControlSchema(
                id=c.id,
                name=c.name,
                description=c.description,
                family=c.family,
                weight=c.weight,
            )
            for c in fw.controls
        ],
    )
