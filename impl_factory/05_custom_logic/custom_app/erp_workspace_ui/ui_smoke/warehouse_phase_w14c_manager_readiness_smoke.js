process.env.ERPW_WAREHOUSE_W9A_EXPECT_W12K = "1";
process.env.ERPW_WAREHOUSE_W9A_EXPECT_W14B = "1";
process.env.ERPW_WAREHOUSE_W9A_EXPECT_W14C = "1";
process.env.ERPW_WAREHOUSE_W9A_PHASE_LABEL = "Warehouse W14C Manager Readiness";
process.env.ERPW_WAREHOUSE_W9A_SUMMARY_NAME = "warehouse-w14c-manager-readiness-summary.json";

require("./warehouse_phase_w9a_cockpit_smoke");
