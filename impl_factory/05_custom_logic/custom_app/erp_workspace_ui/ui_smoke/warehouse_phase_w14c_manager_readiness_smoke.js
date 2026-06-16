process.env.ERPW_WAREHOUSE_W9A_EXPECT_W12K = "1";
process.env.ERPW_WAREHOUSE_W9A_EXPECT_W14B = "1";
process.env.ERPW_WAREHOUSE_W9A_EXPECT_W14C = "1";
process.env.ERPW_WAREHOUSE_W9A_PHASE_LABEL = "Warehouse Phase 0 Manager Readiness Removal";
process.env.ERPW_WAREHOUSE_W9A_SUMMARY_NAME = "warehouse-phase0-manager-readiness-removal-summary.json";

require("./warehouse_phase_w9a_cockpit_smoke");
