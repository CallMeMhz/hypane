"""Storage service - CRUD operations for Storage."""

from app.models.storage import Storage


def list_storages() -> list[dict]:
    """List all storages."""
    return [s.to_dict() for s in Storage.list_all()]


def get_storage(storage_id: str) -> dict | None:
    """Get a storage by ID."""
    s = Storage.load(storage_id)
    return s.to_dict() if s else None


def create_storage(storage_id: str, data: dict | None = None) -> dict:
    """Create a new storage."""
    s = Storage(id=storage_id, data=data or {})
    s.save()
    return s.to_dict()


def update_storage(storage_id: str, data: dict) -> dict | None:
    """Update storage data (full replace)."""
    s = Storage.load(storage_id)
    if not s:
        return None
    s.data = data
    s.save()
    return s.to_dict()


def patch_storage(storage_id: str, patch: dict) -> dict | None:
    """Patch storage data (shallow merge)."""
    s = Storage.load(storage_id)
    if not s:
        return None
    s.data.update(patch)
    s.save()
    return s.to_dict()


def delete_storage(storage_id: str) -> bool:
    """Delete a storage."""
    s = Storage.load(storage_id)
    if not s:
        return False
    return s.delete()


def load_storages_for_context(storage_ids: list[str]) -> dict[str, dict]:
    """Load multiple storages and return as {id: data} dict for handler context."""
    storages = Storage.load_many(storage_ids)
    return {sid: s.data for sid, s in storages.items()}


def save_storages_from_context(storage_ids: list[str], context: dict[str, dict]) -> None:
    """Save modified storage data from handler context."""
    storages = Storage.load_many(storage_ids)
    for sid in storage_ids:
        if sid in context and sid in storages:
            storages[sid].data = context[sid]
            storages[sid].save()
