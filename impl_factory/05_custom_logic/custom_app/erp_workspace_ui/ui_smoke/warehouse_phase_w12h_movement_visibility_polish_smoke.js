process.env.ERPW_WAREHOUSE_W8A_EXPECT_W12H = "1";
process.env.ERPW_WAREHOUSE_W8A_PHASE_LABEL = "Warehouse W12H movement visibility polish";
process.env.ERPW_WAREHOUSE_W8A_SUMMARY_NAME = "warehouse-w12h-movement-visibility-polish-summary.json";

if (process.env.ERPW_WAREHOUSE_W12H_ASSET_ROOT && !process.env.ERPW_WAREHOUSE_W8A_ASSET_ROOT) {
  process.env.ERPW_WAREHOUSE_W8A_ASSET_ROOT = process.env.ERPW_WAREHOUSE_W12H_ASSET_ROOT;
}

if (process.env.ERPW_WAREHOUSE_W12H_ARTIFACT_DIR && !process.env.ERPW_WAREHOUSE_W8A_ARTIFACT_DIR) {
  process.env.ERPW_WAREHOUSE_W8A_ARTIFACT_DIR = process.env.ERPW_WAREHOUSE_W12H_ARTIFACT_DIR;
}

if (process.env.ERPW_WAREHOUSE_W12H_TIMEOUT && !process.env.ERPW_WAREHOUSE_W8A_TIMEOUT) {
  process.env.ERPW_WAREHOUSE_W8A_TIMEOUT = process.env.ERPW_WAREHOUSE_W12H_TIMEOUT;
}

require("./warehouse_phase_w8a_movement_visibility_smoke");
