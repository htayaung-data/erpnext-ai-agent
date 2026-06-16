process.env.ERPW_WAREHOUSE_W9A_EXPECT_W12K = "1";
process.env.ERPW_WAREHOUSE_W9A_EXPECT_W14B = "1";
process.env.ERPW_WAREHOUSE_W9A_EXPECT_W14C = "1";
process.env.ERPW_WAREHOUSE_W9A_EXPECT_W15B = "1";
process.env.ERPW_WAREHOUSE_W9A_PHASE_LABEL = "Warehouse W15B Action Center shell";
process.env.ERPW_WAREHOUSE_W9A_SUMMARY_NAME = "warehouse-w15b-action-center-summary.json";

require("./warehouse_phase_w9a_cockpit_smoke");
