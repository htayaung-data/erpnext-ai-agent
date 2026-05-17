from __future__ import annotations

from typing import Any


_MASTER_DATA_LISTING_FAMILY_IDS = {
	"master_data_directory",
	"customer_master_list",
}


def is_master_data_listing_family(family_id: Any) -> bool:
	return str(family_id or "").strip() in _MASTER_DATA_LISTING_FAMILY_IDS


def is_master_data_surface_family(family_id: Any) -> bool:
	clean_family_id = str(family_id or "").strip()
	return clean_family_id == "master_data_lookup" or is_master_data_listing_family(clean_family_id)
