import unittest

from ai_assistant_ui.qwen_chat.governed_scope_registry import (
    canonical_master_data_entity_grain,
    canonical_scope_aliases,
    canonical_scope_aliases_for_entity_grain,
    entity_grain_for_report_name,
    listing_view_for_report_name,
    scope_id_for_canonical_alias,
    scope_id_for_entity_grain,
    scope_id_for_listing_view,
    scope_id_for_report_name,
    validate_family_scope_compatibility_registry,
    validate_governed_scope_access_model,
    validate_governed_scope_registry,
    validate_scope_clarification_registry,
    validate_scope_owner_registry,
    validate_scope_projection_registry,
)
from ai_assistant_ui.qwen_chat.metadata import (
    capability_business_family_ids,
    capability_contract_identity,
    capability_fresh_query_defaults,
    get_capability_spec,
    get_family_scope_compatibility_spec,
    load_governed_scope_registry,
)


class TestGovernedScopeRegistry(unittest.TestCase):
    def test_current_slice_a0_metadata_validates(self):
        results = [
            validate_governed_scope_registry(),
            validate_scope_owner_registry(),
            validate_family_scope_compatibility_registry(),
            validate_scope_projection_registry(),
            validate_scope_clarification_registry(),
            validate_governed_scope_access_model(),
        ]
        for result in results:
            self.assertEqual(
                result.status,
                "pass",
                f"{result.registry_name} must validate cleanly: {result.errors!r}",
            )

    def test_seed_scope_inventory_records_active_and_partial_truthfully(self):
        scopes = {
            str(item.get("scope_id") or "").strip(): item
            for item in (load_governed_scope_registry().get("scopes") or [])
            if isinstance(item, dict)
        }
        self.assertEqual(str(scopes["customer_master"].get("status") or "").strip(), "active")
        self.assertEqual(str(scopes["supplier_master"].get("status") or "").strip(), "active")
        self.assertEqual(str(scopes["item_master"].get("status") or "").strip(), "active")
        self.assertEqual(
            str(scopes["purchase_invoice"].get("support_state") or "").strip(),
            "active_broad",
        )
        self.assertEqual(
            str(scopes["payment_entry"].get("support_state") or "").strip(),
            "active_broad",
        )

    def test_purchase_invoice_listing_activation_is_explicit_in_compatibility_policy(self):
        listing_spec = get_family_scope_compatibility_spec("purchase_invoice", "transaction_listing")
        detail_spec = get_family_scope_compatibility_spec("purchase_invoice", "entity_detail")

        self.assertEqual(str(listing_spec.get("compatibility_level") or "").strip(), "full_consumption")
        self.assertIn("document_list", list(listing_spec.get("allowed_modes") or []))
        self.assertEqual(str(detail_spec.get("compatibility_level") or "").strip(), "full_consumption")

    def test_supplier_and_item_master_directory_support_is_explicit(self):
        supplier_lookup = get_family_scope_compatibility_spec("supplier_master", "master_data_lookup")
        item_lookup = get_family_scope_compatibility_spec("item_master", "master_data_lookup")
        supplier_detail = get_family_scope_compatibility_spec("supplier_master", "entity_detail")
        item_detail = get_family_scope_compatibility_spec("item_master", "entity_detail")

        self.assertEqual(str(supplier_lookup.get("compatibility_level") or "").strip(), "full_consumption")
        self.assertEqual(str(item_lookup.get("compatibility_level") or "").strip(), "full_consumption")
        self.assertEqual(str(supplier_detail.get("compatibility_level") or "").strip(), "full_consumption")
        self.assertEqual(str(item_detail.get("compatibility_level") or "").strip(), "full_consumption")
        self.assertIn("directory_list", list(supplier_lookup.get("allowed_modes") or []))
        self.assertIn("candidate_resolution", list(supplier_lookup.get("allowed_modes") or []))
        self.assertIn("directory_list", list(item_lookup.get("allowed_modes") or []))
        self.assertIn("candidate_resolution", list(item_lookup.get("allowed_modes") or []))

    def test_payment_entry_listing_is_explicitly_active_in_shared_scope_policy(self):
        listing_spec = get_family_scope_compatibility_spec("payment_entry", "transaction_listing")
        followup_spec = get_family_scope_compatibility_spec("payment_entry", "followup_boundary")

        self.assertEqual(str(listing_spec.get("compatibility_level") or "").strip(), "full_consumption")
        self.assertIn("document_list", list(listing_spec.get("allowed_modes") or []))
        self.assertEqual(str(followup_spec.get("compatibility_level") or "").strip(), "followup_only")
        self.assertIn("column_projection", list(followup_spec.get("allowed_modes") or []))

    def test_payment_entry_capability_alias_resolves_to_existing_collections_capability(self):
        capability = get_capability_spec("payment_entry_read")
        defaults = capability_fresh_query_defaults("payment_entry_read", intent_class="transaction_listing")

        self.assertEqual(str(capability.get("capability_id") or "").strip(), "collections_read")
        self.assertIn("payment_entry_read", list(capability.get("canonical_aliases") or []))
        self.assertEqual(defaults.get("default_report_name"), "Payment Entry List")
        self.assertEqual(capability_business_family_ids("payment_entry_read"), ["transaction_listing"])

    def test_payment_entry_contract_identity_uses_scope_aware_alias(self):
        self.assertEqual(
            capability_contract_identity("collections_read", scope_id="payment_entry"),
            "payment_entry_read",
        )
        self.assertEqual(
            capability_contract_identity("collections_read", report_name="Payment Entry List"),
            "payment_entry_read",
        )
        self.assertEqual(capability_contract_identity("collections_read"), "collections_read")
        self.assertEqual(capability_contract_identity("payment_entry_read"), "payment_entry_read")

    def test_governed_scope_registry_maps_active_reports_to_scope_and_grain(self):
        self.assertEqual(scope_id_for_report_name("Customer Master List"), "customer_master")
        self.assertEqual(entity_grain_for_report_name("Customer Master List"), "customer")
        self.assertEqual(scope_id_for_report_name("Supplier Master List"), "supplier_master")
        self.assertEqual(entity_grain_for_report_name("Supplier Master List"), "supplier")
        self.assertEqual(scope_id_for_report_name("Payment Entry List"), "payment_entry")
        self.assertEqual(listing_view_for_report_name("Payment Entry List"), "payment_entry")

    def test_canonical_scope_aliases_are_metadata_driven(self):
        self.assertEqual(scope_id_for_canonical_alias("product master"), "item_master")
        self.assertEqual(scope_id_for_canonical_alias("payment entry"), "payment_entry")
        self.assertEqual(scope_id_for_canonical_alias("supplier invoice"), "purchase_invoice")
        self.assertEqual(scope_id_for_entity_grain("product"), "item_master")
        self.assertEqual(canonical_master_data_entity_grain("product"), "item")
        self.assertIn("product_master", canonical_scope_aliases("item_master"))
        self.assertIn("product_master", canonical_scope_aliases_for_entity_grain("product"))
        self.assertEqual(scope_id_for_listing_view("Payment Entry List"), "payment_entry")
        self.assertEqual(scope_id_for_listing_view("purchase invoice"), "purchase_invoice")
        self.assertEqual(scope_id_for_listing_view("supplier invoice"), "purchase_invoice")


if __name__ == "__main__":
    unittest.main()
