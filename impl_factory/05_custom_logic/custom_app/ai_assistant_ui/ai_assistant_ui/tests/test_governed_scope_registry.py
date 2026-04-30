import unittest

from ai_assistant_ui.qwen_chat.governed_scope_registry import (
    active_listing_view_aliases,
    canonical_listing_view_alias_phrases,
    canonical_master_data_entity_grain,
    canonical_scope_alias_phrases,
    canonical_scope_aliases,
    canonical_scope_aliases_for_entity_grain,
    entity_detail_scope_activation,
    entity_detail_runtime_policy,
    entity_reference_resolution_activation,
    entity_grain_for_report_name,
    governed_scope_runtime_policy,
    list_active_entity_detail_scope_activations,
    listing_view_for_report_name,
    master_data_scope_activation,
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
    get_scope_projection_spec,
    load_capability_registry,
    load_family_scope_compatibility_registry,
    load_governed_scope_registry,
    load_report_registry,
    load_scope_owner_registry,
    list_scope_clarification_specs_for_scope,
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
        self.assertEqual(str(scopes["purchase_receipt"].get("status") or "").strip(), "active")
        self.assertEqual(
            str(scopes["purchase_receipt"].get("support_state") or "").strip(),
            "active_reference",
        )
        authority = scopes["purchase_receipt"].get("approved_source_authority") or {}
        self.assertEqual(str(authority.get("source_kind") or "").strip(), "report")
        self.assertEqual(str(authority.get("authority_status") or "").strip(), "approved")
        self.assertEqual(str(authority.get("report_name") or "").strip(), "Purchase Receipt List")
        self.assertEqual(str(authority.get("capability_id") or "").strip(), "purchase_receipt_read")

    def test_purchase_receipt_listing_is_active_but_detail_is_not_promoted(self):
        owners = {
            str(item.get("scope_id") or "").strip(): item
            for item in (load_scope_owner_registry().get("entries") or [])
            if isinstance(item, dict)
        }
        owner = owners.get("purchase_receipt") or {}

        self.assertEqual(str(owner.get("primary_owner_family") or "").strip(), "transaction_listing")
        self.assertIn("entity_detail", list(owner.get("secondary_compatible_families") or []))
        self.assertIn("master_data_lookup", list(owner.get("prohibited_families") or []))
        self.assertEqual(scope_id_for_canonical_alias("purchase receipt"), "purchase_receipt")
        self.assertEqual(scope_id_for_canonical_alias("goods receipt"), "purchase_receipt")
        self.assertEqual(scope_id_for_listing_view("purchase receipt"), "purchase_receipt")
        self.assertEqual(scope_id_for_listing_view("goods receipts"), "purchase_receipt")
        self.assertEqual(scope_id_for_report_name("Purchase Receipt List"), "purchase_receipt")
        policy = governed_scope_runtime_policy("purchase_receipt", "transaction_listing")
        self.assertEqual(policy.get("scope_id"), "purchase_receipt")
        self.assertEqual(policy.get("family_id"), "transaction_listing")
        self.assertEqual(policy.get("report_name"), "Purchase Receipt List")
        self.assertEqual(policy.get("capability_id"), "purchase_receipt_read")
        self.assertTrue(policy.get("can_execute"))
        self.assertTrue(policy.get("has_projection_policy"))
        self.assertIn("Purchase Receipt", list(policy.get("allowed_dimensions") or []))
        self.assertIn("Grand Total", list(policy.get("allowed_metrics") or []))
        self.assertIn("purchase_receipt", active_listing_view_aliases())
        self.assertFalse(entity_detail_runtime_policy("purchase_receipt"))

    def test_purchase_invoice_listing_activation_is_explicit_in_compatibility_policy(self):
        listing_spec = get_family_scope_compatibility_spec("purchase_invoice", "transaction_listing")
        detail_spec = get_family_scope_compatibility_spec("purchase_invoice", "entity_detail")

        self.assertEqual(str(listing_spec.get("compatibility_level") or "").strip(), "full_consumption")
        self.assertIn("document_list", list(listing_spec.get("allowed_modes") or []))
        self.assertEqual(str(detail_spec.get("compatibility_level") or "").strip(), "full_consumption")

    def test_e2_5_procurement_scope_parity_matrix_is_explicit(self):
        expected = {
            "purchase_invoice": {
                "report": "Purchase Invoice List",
                "capability": "purchase_invoice_read",
                "detail_active": True,
                "detail_projection": True,
            },
            "purchase_order": {
                "report": "Purchase Order List",
                "capability": "purchase_order_read",
                "detail_active": True,
                "detail_projection": True,
            },
            "purchase_receipt": {
                "report": "Purchase Receipt List",
                "capability": "purchase_receipt_read",
                "detail_active": False,
                "detail_projection": False,
            },
        }

        for scope_id, policy in expected.items():
            listing_spec = get_family_scope_compatibility_spec(scope_id, "transaction_listing")
            followup_spec = get_family_scope_compatibility_spec(scope_id, "followup_boundary")
            listing_projection = get_scope_projection_spec(scope_id, "transaction_listing")
            detail_spec = get_family_scope_compatibility_spec(scope_id, "entity_detail")
            detail_projection = get_scope_projection_spec(scope_id, "entity_detail")
            runtime_policy = governed_scope_runtime_policy(scope_id, "transaction_listing")

            self.assertEqual(runtime_policy.get("report_name"), policy["report"])
            self.assertEqual(runtime_policy.get("capability_id"), policy["capability"])
            self.assertEqual(str(listing_spec.get("compatibility_level") or "").strip(), "full_consumption")
            self.assertIn("document_list", list(listing_spec.get("allowed_modes") or []))
            self.assertEqual(str(followup_spec.get("compatibility_level") or "").strip(), "followup_only")
            self.assertTrue(bool(listing_projection))
            self.assertEqual(bool(detail_spec), policy["detail_active"])
            self.assertEqual(bool(detail_projection), policy["detail_projection"])
            self.assertEqual(bool(entity_detail_runtime_policy(scope_id)), policy["detail_active"])

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

    def test_purchase_receipt_capability_is_active_transaction_listing_contract(self):
        capability = get_capability_spec("purchase_receipt_read")
        defaults = capability_fresh_query_defaults("purchase_receipt_read", intent_class="transaction_listing")

        self.assertEqual(str(capability.get("capability_id") or "").strip(), "purchase_receipt_read")
        self.assertEqual(defaults.get("default_report_name"), "Purchase Receipt List")
        self.assertEqual(defaults.get("default_dimensions"), ["Purchase Receipt", "Supplier", "Status"])
        self.assertEqual(defaults.get("default_metrics"), ["Grand Total", "Quantity"])
        self.assertEqual(capability_business_family_ids("purchase_receipt_read"), ["transaction_listing"])

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

    def test_e3_1_payment_entry_ownership_reuses_mature_collections_execution_capability(self):
        scopes = {
            str(item.get("scope_id") or "").strip(): item
            for item in (load_governed_scope_registry().get("scopes") or [])
            if isinstance(item, dict)
        }
        owners = {
            str(item.get("scope_id") or "").strip(): item
            for item in (load_scope_owner_registry().get("entries") or [])
            if isinstance(item, dict)
        }
        capabilities = {
            str(item.get("capability_id") or "").strip(): item
            for item in (load_capability_registry().get("capabilities") or [])
            if isinstance(item, dict)
        }
        reports = {
            str(item.get("report_name") or "").strip(): item
            for item in (load_report_registry().get("reports") or [])
            if isinstance(item, dict)
        }

        scope = scopes["payment_entry"]
        owner = owners["payment_entry"]
        capability = capabilities["collections_read"]
        report = reports["Payment Entry List"]

        self.assertEqual(scope.get("scope_class"), "financial_operation")
        self.assertEqual(scope.get("primary_owner_family"), "transaction_listing")
        self.assertEqual(scope.get("approved_source_authority", {}).get("capability_id"), "collections_read")
        self.assertEqual(owner.get("primary_owner_family"), "transaction_listing")
        self.assertNotIn("entity_detail", list(owner.get("secondary_compatible_families") or []))
        self.assertNotIn("payment_entry_read", capabilities)
        self.assertIn("payment_entry_read", list(capability.get("canonical_aliases") or []))
        self.assertEqual((capability.get("scope_capability_aliases") or {}).get("payment_entry"), "payment_entry_read")
        self.assertEqual(report.get("grounding_mode"), "direct_query")
        self.assertEqual((report.get("direct_query") or {}).get("doctype"), "Payment Entry")
        self.assertEqual(capability_contract_identity("collections_read", scope_id="payment_entry"), "payment_entry_read")

    def test_phase_f_package3_payment_entry_ambiguity_coverage_is_shared_and_typed(self):
        specs = {
            str(item.get("family_id") or "").strip(): item
            for item in list_scope_clarification_specs_for_scope("payment_entry")
            if isinstance(item, dict)
        }

        self.assertEqual(set(specs), {"transaction_listing", "followup_boundary", "clarification"})
        self.assertEqual(
            set(specs["transaction_listing"].get("supported_ambiguity_classes") or []),
            {"time_scope", "projection_request", "document_reference"},
        )
        self.assertEqual(
            set(specs["followup_boundary"].get("supported_ambiguity_classes") or []),
            {"followup_scope", "projection_request", "time_scope"},
        )
        self.assertEqual(
            set(specs["clarification"].get("supported_ambiguity_classes") or []),
            {"unsupported_route"},
        )
        self.assertEqual(
            specs["transaction_listing"].get("clarification_template_group"),
            "transaction_listing_clarification",
        )
        self.assertEqual(
            specs["followup_boundary"].get("clarification_template_group"),
            "followup_boundary_clarification",
        )
        self.assertEqual(
            specs["clarification"].get("clarification_template_group"),
            "unsupported_scope_clarification",
        )

    def test_phase_g_checkpoint_completed_scope_packages_have_single_registry_authority(self):
        completed_scope_expectations = {
            "customer_master": {
                "scope_class": "master_data",
                "primary_owner_family": "master_data_lookup",
                "family_levels": {
                    "master_data_lookup": "full_consumption",
                    "entity_detail": "full_consumption",
                    "followup_boundary": "followup_only",
                    "clarification": "clarification_only",
                },
            },
            "supplier_master": {
                "scope_class": "master_data",
                "primary_owner_family": "master_data_lookup",
                "family_levels": {
                    "master_data_lookup": "full_consumption",
                    "entity_detail": "full_consumption",
                    "followup_boundary": "followup_only",
                    "clarification": "clarification_only",
                },
            },
            "item_master": {
                "scope_class": "master_data",
                "primary_owner_family": "master_data_lookup",
                "family_levels": {
                    "master_data_lookup": "full_consumption",
                    "entity_detail": "full_consumption",
                    "followup_boundary": "followup_only",
                    "clarification": "clarification_only",
                },
            },
            "sales_invoice": {
                "scope_class": "document",
                "primary_owner_family": "transaction_listing",
                "family_levels": {
                    "transaction_listing": "full_consumption",
                    "entity_detail": "full_consumption",
                    "followup_boundary": "followup_only",
                    "clarification": "clarification_only",
                },
            },
            "sales_order": {
                "scope_class": "document",
                "primary_owner_family": "transaction_listing",
                "family_levels": {
                    "transaction_listing": "full_consumption",
                    "entity_detail": "full_consumption",
                    "followup_boundary": "followup_only",
                    "clarification": "clarification_only",
                },
            },
            "delivery_note": {
                "scope_class": "document",
                "primary_owner_family": "transaction_listing",
                "family_levels": {
                    "transaction_listing": "full_consumption",
                    "entity_detail": "full_consumption",
                    "followup_boundary": "followup_only",
                    "clarification": "clarification_only",
                },
            },
            "purchase_order": {
                "scope_class": "document",
                "primary_owner_family": "transaction_listing",
                "family_levels": {
                    "transaction_listing": "full_consumption",
                    "entity_detail": "full_consumption",
                    "followup_boundary": "followup_only",
                    "clarification": "clarification_only",
                },
            },
            "purchase_invoice": {
                "scope_class": "document",
                "primary_owner_family": "transaction_listing",
                "family_levels": {
                    "transaction_listing": "full_consumption",
                    "entity_detail": "full_consumption",
                    "followup_boundary": "followup_only",
                    "clarification": "clarification_only",
                },
            },
            "purchase_receipt": {
                "scope_class": "document",
                "primary_owner_family": "transaction_listing",
                "family_levels": {
                    "transaction_listing": "full_consumption",
                    "followup_boundary": "followup_only",
                    "clarification": "clarification_only",
                },
            },
            "payment_entry": {
                "scope_class": "financial_operation",
                "primary_owner_family": "transaction_listing",
                "family_levels": {
                    "transaction_listing": "full_consumption",
                    "followup_boundary": "followup_only",
                    "clarification": "clarification_only",
                },
            },
        }
        scopes = {
            str(item.get("scope_id") or "").strip(): item
            for item in (load_governed_scope_registry().get("scopes") or [])
            if isinstance(item, dict)
        }
        owners = {
            str(item.get("scope_id") or "").strip(): item
            for item in (load_scope_owner_registry().get("entries") or [])
            if isinstance(item, dict)
        }

        for scope_id, expected in completed_scope_expectations.items():
            with self.subTest(scope_id=scope_id):
                scope = scopes.get(scope_id) or {}
                owner = owners.get(scope_id) or {}
                authority = scope.get("approved_source_authority")

                self.assertEqual(str(scope.get("status") or "").strip(), "active")
                self.assertEqual(str(scope.get("scope_class") or "").strip(), expected["scope_class"])
                self.assertEqual(
                    str(scope.get("primary_owner_family") or "").strip(),
                    expected["primary_owner_family"],
                )
                self.assertEqual(
                    str(owner.get("primary_owner_family") or "").strip(),
                    expected["primary_owner_family"],
                )
                self.assertIsInstance(authority, dict)
                self.assertEqual(str(authority.get("authority_status") or "").strip(), "approved")
                self.assertEqual(str(authority.get("source_kind") or "").strip(), "report")
                self.assertTrue(str(authority.get("report_name") or "").strip())
                self.assertTrue(str(authority.get("capability_id") or "").strip())
                self.assertNotIn(
                    "approved_source_authorities",
                    scope,
                    "A completed governed scope must have one approved authority object, not a parallel authority list.",
                )

                for family_id, compatibility_level in expected["family_levels"].items():
                    family_spec = get_family_scope_compatibility_spec(scope_id, family_id)
                    runtime_policy = governed_scope_runtime_policy(scope_id, family_id)

                    self.assertEqual(
                        str(family_spec.get("compatibility_level") or "").strip(),
                        compatibility_level,
                    )
                    self.assertEqual(runtime_policy.get("scope_id"), scope_id)
                    self.assertEqual(runtime_policy.get("family_id"), family_id)
                    self.assertEqual(runtime_policy.get("compatibility_level"), compatibility_level)
                    if compatibility_level == "full_consumption":
                        self.assertTrue(runtime_policy.get("can_execute"))
                    if compatibility_level == "followup_only":
                        self.assertFalse(runtime_policy.get("can_execute"))
                        self.assertTrue(runtime_policy.get("can_followup"))

        forbidden_scope_ids = {
            "customer_lifecycle",
            "document_event",
            "event_lifecycle",
            "lifecycle_event",
        }
        forbidden_scope_classes = {
            "event",
            "events",
            "lifecycle",
            "event_lifecycle",
            "document_event",
            "customer_lifecycle",
        }
        active_event_like_scopes = [
            scope_id
            for scope_id, scope in scopes.items()
            if str(scope.get("status") or "").strip() == "active"
            and str(scope.get("scope_class") or "").strip() in forbidden_scope_classes
        ]

        self.assertFalse(forbidden_scope_ids.intersection(scopes))
        self.assertEqual(active_event_like_scopes, [])

    def test_phase_g_specialized_path_alignment_has_no_hidden_family_authority(self):
        owners = {
            str(item.get("scope_id") or "").strip(): item
            for item in (load_scope_owner_registry().get("entries") or [])
            if isinstance(item, dict)
        }
        family_entries = [
            item
            for item in (load_family_scope_compatibility_registry().get("entries") or [])
            if isinstance(item, dict)
        ]

        for entry in family_entries:
            scope_id = str(entry.get("scope_id") or "").strip()
            family_id = str(entry.get("family_id") or "").strip()
            compatibility_level = str(entry.get("compatibility_level") or "").strip()
            if not scope_id or not family_id or compatibility_level == "not_allowed":
                continue

            with self.subTest(scope_id=scope_id, family_id=family_id):
                owner = owners.get(scope_id) or {}
                primary_owner = str(owner.get("primary_owner_family") or "").strip()
                secondary_families = set(owner.get("secondary_compatible_families") or [])
                prohibited_families = set(owner.get("prohibited_families") or [])
                runtime_policy = governed_scope_runtime_policy(scope_id, family_id)

                self.assertNotIn(family_id, prohibited_families)
                if family_id != primary_owner:
                    self.assertIn(family_id, secondary_families)
                self.assertEqual(runtime_policy.get("scope_id"), scope_id)
                self.assertEqual(runtime_policy.get("family_id"), family_id)
                self.assertEqual(runtime_policy.get("compatibility_level"), compatibility_level)
                if compatibility_level in {"full_consumption", "projection_only"}:
                    self.assertTrue(runtime_policy.get("can_execute"))
                if compatibility_level == "followup_only":
                    self.assertFalse(runtime_policy.get("can_execute"))
                    self.assertTrue(runtime_policy.get("can_followup"))
                if compatibility_level == "clarification_only":
                    self.assertFalse(runtime_policy.get("can_execute"))
                    self.assertFalse(runtime_policy.get("can_followup"))

        for scope_id, owner in owners.items():
            for family_id in list(owner.get("prohibited_families") or []):
                with self.subTest(scope_id=scope_id, prohibited_family_id=family_id):
                    family_spec = get_family_scope_compatibility_spec(scope_id, family_id)
                    runtime_policy = governed_scope_runtime_policy(scope_id, family_id)
                    self.assertFalse(
                        family_spec
                        and str(family_spec.get("compatibility_level") or "").strip() != "not_allowed"
                    )
                    self.assertFalse(runtime_policy.get("can_execute"))
                    self.assertFalse(runtime_policy.get("can_followup"))

    def test_phase_g_coverage_matrix_active_scopes_have_owner_family_projection_and_clarification(self):
        scopes = {
            str(item.get("scope_id") or "").strip(): item
            for item in (load_governed_scope_registry().get("scopes") or [])
            if isinstance(item, dict) and str(item.get("scope_id") or "").strip()
        }
        owners = {
            str(item.get("scope_id") or "").strip(): item
            for item in (load_scope_owner_registry().get("entries") or [])
            if isinstance(item, dict)
        }
        families_by_scope = {}
        for item in (load_family_scope_compatibility_registry().get("entries") or []):
            if not isinstance(item, dict):
                continue
            scope_id = str(item.get("scope_id") or "").strip()
            compatibility_level = str(item.get("compatibility_level") or "").strip()
            if scope_id and compatibility_level != "not_allowed":
                families_by_scope.setdefault(scope_id, []).append(item)

        active_support_states = {"active_reference", "active_broad"}
        active_scope_classes = {"master_data", "document", "financial_operation"}
        active_scope_ids = [
            scope_id
            for scope_id, scope in scopes.items()
            if str(scope.get("status") or "").strip() == "active"
        ]

        self.assertEqual(
            set(active_scope_ids),
            {
                "customer_master",
                "supplier_master",
                "item_master",
                "sales_invoice",
                "purchase_invoice",
                "delivery_note",
                "sales_order",
                "purchase_order",
                "purchase_receipt",
                "payment_entry",
            },
        )

        for scope_id in active_scope_ids:
            with self.subTest(scope_id=scope_id):
                scope = scopes.get(scope_id) or {}
                owner = owners.get(scope_id) or {}
                primary_owner = str(owner.get("primary_owner_family") or "").strip()
                compatible_families = families_by_scope.get(scope_id) or []
                compatible_family_ids = {
                    str(item.get("family_id") or "").strip()
                    for item in compatible_families
                    if str(item.get("family_id") or "").strip()
                }
                clarification_family_ids = {
                    str(item.get("family_id") or "").strip()
                    for item in list_scope_clarification_specs_for_scope(scope_id)
                    if isinstance(item, dict) and str(item.get("family_id") or "").strip()
                }

                self.assertIn(str(scope.get("support_state") or "").strip(), active_support_states)
                self.assertIn(str(scope.get("scope_class") or "").strip(), active_scope_classes)
                self.assertEqual(str(scope.get("primary_owner_family") or "").strip(), primary_owner)
                self.assertIn(primary_owner, compatible_family_ids)
                self.assertTrue(compatible_family_ids)

                for family_entry in compatible_families:
                    family_id = str(family_entry.get("family_id") or "").strip()
                    compatibility_level = str(family_entry.get("compatibility_level") or "").strip()
                    followup_compatibility = str(
                        family_entry.get("followup_compatibility") or ""
                    ).strip()
                    runtime_policy = governed_scope_runtime_policy(scope_id, family_id)

                    self.assertIn(family_id, clarification_family_ids)
                    self.assertEqual(runtime_policy.get("scope_id"), scope_id)
                    self.assertEqual(runtime_policy.get("family_id"), family_id)
                    self.assertEqual(runtime_policy.get("compatibility_level"), compatibility_level)
                    if compatibility_level in {"full_consumption", "projection_only"}:
                        self.assertTrue(bool(get_scope_projection_spec(scope_id, family_id)))
                        self.assertTrue(runtime_policy.get("can_execute"))
                    if followup_compatibility in {"preserve_scope", "requery_same_scope"}:
                        self.assertTrue(runtime_policy.get("can_followup"))

    def test_governed_scope_registry_maps_active_reports_to_scope_and_grain(self):
        self.assertEqual(scope_id_for_report_name("Customer Master List"), "customer_master")
        self.assertEqual(entity_grain_for_report_name("Customer Master List"), "customer")
        self.assertEqual(scope_id_for_report_name("Supplier Master List"), "supplier_master")
        self.assertEqual(entity_grain_for_report_name("Supplier Master List"), "supplier")
        self.assertEqual(scope_id_for_report_name("Payment Entry List"), "payment_entry")
        self.assertEqual(listing_view_for_report_name("Payment Entry List"), "payment_entry")
        self.assertEqual(scope_id_for_report_name("Purchase Receipt List"), "purchase_receipt")
        self.assertEqual(listing_view_for_report_name("Purchase Receipt List"), "purchase_receipt")

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
        self.assertEqual(scope_id_for_listing_view("purchase receipt"), "purchase_receipt")
        self.assertEqual(scope_id_for_listing_view("goods receipt"), "purchase_receipt")
        self.assertIn("supplier invoices", canonical_scope_alias_phrases("purchase_invoice"))
        self.assertIn("goods receipts", canonical_scope_alias_phrases("purchase_receipt"))
        self.assertIn("collections", canonical_scope_alias_phrases("payment_entry"))
        self.assertIn("supplier invoices", canonical_listing_view_alias_phrases("purchase_invoice"))
        self.assertIn("goods receipts", canonical_listing_view_alias_phrases("purchase_receipt"))

    def test_active_listing_view_aliases_are_governed_scope_backed(self):
        aliases = active_listing_view_aliases()
        self.assertIn("purchase_invoice", aliases)
        self.assertIn("supplier invoices", aliases["purchase_invoice"])
        self.assertIn("purchase_receipt", aliases)
        self.assertIn("goods receipts", aliases["purchase_receipt"])
        self.assertIn("payment_entry", aliases)
        self.assertIn("receipts", aliases["payment_entry"])
        self.assertNotIn("supplier", aliases["purchase_order"])
        self.assertNotIn("customer_master", aliases)

    def test_governed_scope_runtime_policy_combines_family_projection_and_followup(self):
        policy = governed_scope_runtime_policy("purchase_invoice", "transaction_listing")
        self.assertEqual(policy.get("scope_id"), "purchase_invoice")
        self.assertEqual(policy.get("family_id"), "transaction_listing")
        self.assertEqual(policy.get("report_name"), "Purchase Invoice List")
        self.assertEqual(policy.get("capability_id"), "purchase_invoice_read")
        self.assertEqual(policy.get("compatibility_level"), "full_consumption")
        self.assertEqual(policy.get("followup_compatibility"), "preserve_scope")
        self.assertTrue(policy.get("can_execute"))
        self.assertTrue(policy.get("has_projection_policy"))
        self.assertIn("Purchase Invoice", list(policy.get("allowed_dimensions") or []))
        self.assertIn("Outstanding Amount", list(policy.get("allowed_metrics") or []))

    def test_governed_scope_runtime_policy_exposes_followup_only_boundary(self):
        policy = governed_scope_runtime_policy("payment_entry", "followup_boundary")
        self.assertEqual(policy.get("compatibility_level"), "followup_only")
        self.assertFalse(policy.get("can_execute"))
        self.assertTrue(policy.get("can_followup"))
        self.assertIn("column_projection", list(policy.get("allowed_modes") or []))

    def test_master_data_scope_activation_carries_runtime_policy(self):
        activation = master_data_scope_activation("product")
        runtime_policy = activation.get("runtime_policy") or {}

        self.assertEqual(activation.get("scope_id"), "item_master")
        self.assertIn("directory_list", list(activation.get("allowed_lookup_modes") or []))
        self.assertEqual(runtime_policy.get("scope_id"), "item_master")
        self.assertEqual(runtime_policy.get("family_id"), "master_data_lookup")
        self.assertTrue(runtime_policy.get("can_execute"))
        self.assertTrue(runtime_policy.get("has_projection_policy"))
        self.assertIn("Item", list(runtime_policy.get("allowed_dimensions") or []))

    def test_entity_detail_scope_activation_carries_runtime_policy(self):
        activation = entity_detail_scope_activation("supplier")
        runtime_policy = activation.get("runtime_policy") or {}

        self.assertEqual(activation.get("scope_id"), "supplier_master")
        self.assertEqual(activation.get("doctype"), "Supplier")
        self.assertIn("profile_target", list(activation.get("allowed_lookup_modes") or []))
        self.assertEqual(runtime_policy.get("family_id"), "entity_detail")
        self.assertTrue(runtime_policy.get("can_execute"))
        self.assertIn("profile_target", list(runtime_policy.get("allowed_modes") or []))
        self.assertIn(
            "supplier",
            [
                item.get("entity_grain")
                for item in list_active_entity_detail_scope_activations(request_mode="profile_target")
            ],
        )

    def test_entity_reference_resolution_activation_switches_by_lookup_family(self):
        candidate_activation = entity_reference_resolution_activation("supplier", "candidate_resolution")
        profile_activation = entity_reference_resolution_activation("supplier", "profile_target")

        self.assertEqual(candidate_activation.get("scope_id"), "supplier_master")
        self.assertEqual(candidate_activation.get("runtime_policy", {}).get("family_id"), "master_data_lookup")
        self.assertIn("candidate_resolution", list(candidate_activation.get("allowed_lookup_modes") or []))
        self.assertEqual(profile_activation.get("scope_id"), "supplier_master")
        self.assertEqual(profile_activation.get("runtime_policy", {}).get("family_id"), "entity_detail")
        self.assertIn("profile_target", list(profile_activation.get("allowed_lookup_modes") or []))
        self.assertEqual(profile_activation.get("doctype"), "Supplier")
        self.assertFalse(entity_reference_resolution_activation("supplier", "unsupported_mode"))

    def test_entity_detail_runtime_policy_covers_profiles_and_documents(self):
        supplier_policy = entity_detail_runtime_policy("supplier")
        invoice_policy = entity_detail_runtime_policy("sales_invoice")

        self.assertEqual(supplier_policy.get("scope_id"), "supplier_master")
        self.assertIn("profile_target", list(supplier_policy.get("allowed_modes") or []))
        self.assertTrue(supplier_policy.get("can_execute"))
        self.assertEqual(invoice_policy.get("scope_id"), "sales_invoice")
        self.assertIn("document_detail", list(invoice_policy.get("allowed_modes") or []))
        self.assertTrue(invoice_policy.get("can_execute"))
        self.assertFalse(entity_detail_runtime_policy("unsupported_entity"))


if __name__ == "__main__":
    unittest.main()
