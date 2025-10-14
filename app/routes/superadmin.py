from fastapi import APIRouter, Depends
from app.deps import require_roles
from app.models.models import RoleEnum

router = APIRouter(prefix="/superadmin", tags=["SuperAdmin"])

@router.get("/dashboard")
def superadmin_dashboard(user=Depends(require_roles(RoleEnum.SUPER_ADMIN))):
    return {"message": "Super Admin Dashboard - full system access"}
