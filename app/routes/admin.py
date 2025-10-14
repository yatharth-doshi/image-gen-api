from fastapi import APIRouter, Depends
from app.deps import require_roles
from app.models.models import RoleEnum

router = APIRouter(prefix="/admin", tags=["Admin"])

@router.get("/dashboard")
def admin_dashboard(user=Depends(require_roles(RoleEnum.ADMIN, RoleEnum.SUPER_ADMIN))):
    return {"message": f"{user.role.value} Dashboard - view images and prompts"}
