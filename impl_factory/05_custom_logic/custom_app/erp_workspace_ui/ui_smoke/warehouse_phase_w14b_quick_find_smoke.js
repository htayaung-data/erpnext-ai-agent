process.env.ERPW_WAREHOUSE_W9A_EXPECT_W12K = "1";
process.env.ERPW_WAREHOUSE_W9A_EXPECT_W14B = "1";
process.env.ERPW_WAREHOUSE_W9A_PHASE_LABEL = "Warehouse W14B Quick Find";
process.env.ERPW_WAREHOUSE_W9A_SUMMARY_NAME = "warehouse-w14b-quick-find-summary.json";

if (process.env.ERPW_WAREHOUSE_W14B_ASSET_ROOT && !process.env.ERPW_WAREHOUSE_W9A_ASSET_ROOT) {
  process.env.ERPW_WAREHOUSE_W9A_ASSET_ROOT = process.env.ERPW_WAREHOUSE_W14B_ASSET_ROOT;
}

if (process.env.ERPW_WAREHOUSE_W14B_ARTIFACT_DIR && !process.env.ERPW_WAREHOUSE_W9A_ARTIFACT_DIR) {
  process.env.ERPW_WAREHOUSE_W9A_ARTIFACT_DIR = process.env.ERPW_WAREHOUSE_W14B_ARTIFACT_DIR;
}

if (process.env.ERPW_WAREHOUSE_W14B_TIMEOUT && !process.env.ERPW_WAREHOUSE_W9A_TIMEOUT) {
  process.env.ERPW_WAREHOUSE_W9A_TIMEOUT = process.env.ERPW_WAREHOUSE_W14B_TIMEOUT;
}

require("./warehouse_phase_w9a_cockpit_smoke");
