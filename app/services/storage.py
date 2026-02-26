"""Storage service - CRUD operations for Storage."""

from app.models.storage import Storage


async def list_storages() -> list[dict]:
    """List all storages."""
    return [s.to_dict() for s in await Storage.list_all()]


async def get_storage(storage_id: str) -> dict | None:
    """Get a storage by ID."""
    s = await Storage.load(storage_id)
    return s.to_dict() if s else None


async def create_storage(storage_id: str, data: dict | None = None) -> dict:
    """Create a new storage."""
    s = Storage(id=storage_id, data=data or {})
    await s.save()
    return s.to_dict()


async def update_storage(storage_id: str, data: dict) -> dict | None:
    """Update storage data (full replace)."""
    s = await Storage.load(storage_id)
    if not s:
        return None
    s.data = data
    await s.save()
    return s.to_dict()


async def patch_storage(storage_id: str, patch: dict) -> dict | None:
    """Patch storage data (shallow merge)."""
    s = await Storage.load(storage_id)
    if not s:
        return None
    s.data.update(patch)
    await s.save()
    return s.to_dict()


async def delete_storage(storage_id: str) -> bool:
    """Delete a storage."""
    s = await Storage.load(storage_id)
    if not s:
        return False
    return await s.delete()


async def load_storages_for_context(storage_ids: list[str]) -> dict[str, dict]:
    """Load multiple storages and return as {id: data} dict for handler context."""
    storages = await Storage.load_many(storage_ids)
    return {sid: s.data for sid, s in storages.items()}


async def save_storages_from_context(storage_ids: list[str], context: dict[str, dict]) -> None:
    """Save modified storage data from handler context."""
    storages = await Storage.load_many(storage_ids)
    for sid in storage_ids:
        if sid in context and sid in storages:
            storages[sid].data = context[sid]
            await storages[sid].save()
