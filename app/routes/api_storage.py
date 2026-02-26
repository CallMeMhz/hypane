"""Storage API routes."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.services import storage as storage_service

router = APIRouter(prefix="/api/storages", tags=["storages"])


class CreateStorageRequest(BaseModel):
    id: str
    data: dict | None = None


class UpdateStorageRequest(BaseModel):
    data: dict


class PatchStorageRequest(BaseModel):
    data: dict


@router.get("")
async def list_storages():
    """List all storages."""
    return await storage_service.list_storages()


@router.get("/{storage_id}")
async def get_storage(storage_id: str):
    """Get a storage by ID."""
    s = await storage_service.get_storage(storage_id)
    if not s:
        raise HTTPException(status_code=404, detail="Storage not found")
    return s


@router.post("")
async def create_storage(request: CreateStorageRequest):
    """Create a new storage."""
    if await storage_service.get_storage(request.id):
        raise HTTPException(status_code=409, detail="Storage already exists")
    return await storage_service.create_storage(request.id, request.data)


@router.put("/{storage_id}")
async def update_storage(storage_id: str, request: UpdateStorageRequest):
    """Update storage data (full replace)."""
    s = await storage_service.update_storage(storage_id, request.data)
    if not s:
        raise HTTPException(status_code=404, detail="Storage not found")
    return s


@router.patch("/{storage_id}")
async def patch_storage(storage_id: str, request: PatchStorageRequest):
    """Patch storage data (shallow merge)."""
    s = await storage_service.patch_storage(storage_id, request.data)
    if not s:
        raise HTTPException(status_code=404, detail="Storage not found")
    return s


@router.delete("/{storage_id}")
async def delete_storage(storage_id: str):
    """Delete a storage."""
    if not await storage_service.delete_storage(storage_id):
        raise HTTPException(status_code=404, detail="Storage not found")
    return {"success": True}
