process.env.ERPW_WAREHOUSE_W9A_EXPECT_W12K = "1";
process.env.ERPW_WAREHOUSE_W9A_PHASE_LABEL = "Warehouse W12K cockpit polish";
process.env.ERPW_WAREHOUSE_W9A_SUMMARY_NAME = "warehouse-w12k-cockpit-polish-summary.json";

if (process.env.ERPW_WAREHOUSE_W12K_ASSET_ROOT && !process.env.ERPW_WAREHOUSE_W9A_ASSET_ROOT) {
  process.env.ERPW_WAREHOUSE_W9A_ASSET_ROOT = process.env.ERPW_WAREHOUSE_W12K_ASSET_ROOT;
}
if (process.env.ERPW_WAREHOUSE_W12K_ARTIFACT_DIR && !process.env.ERPW_WAREHOUSE_W9A_ARTIFACT_DIR) {
  process.env.ERPW_WAREHOUSE_W9A_ARTIFACT_DIR = process.env.ERPW_WAREHOUSE_W12K_ARTIFACT_DIR;
}
if (process.env.ERPW_WAREHOUSE_W12K_TIMEOUT && !process.env.ERPW_WAREHOUSE_W9A_TIMEOUT) {
  process.env.ERPW_WAREHOUSE_W9A_TIMEOUT = process.env.ERPW_WAREHOUSE_W12K_TIMEOUT;
}

require("./warehouse_phase_w9a_cockpit_smoke");
