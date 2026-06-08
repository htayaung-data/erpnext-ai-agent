process.env.ERPW_WAREHOUSE_W8B_EXPECT_W12I = "1";
process.env.ERPW_WAREHOUSE_W8B_PHASE_LABEL = "Warehouse W12I movement review polish";
process.env.ERPW_WAREHOUSE_W8B_SUMMARY_NAME = "warehouse-w12i-movement-review-polish-summary.json";

if (process.env.ERPW_WAREHOUSE_W12I_ASSET_ROOT && !process.env.ERPW_WAREHOUSE_W8B_ASSET_ROOT) {
  process.env.ERPW_WAREHOUSE_W8B_ASSET_ROOT = process.env.ERPW_WAREHOUSE_W12I_ASSET_ROOT;
}

if (process.env.ERPW_WAREHOUSE_W12I_ARTIFACT_DIR && !process.env.ERPW_WAREHOUSE_W8B_ARTIFACT_DIR) {
  process.env.ERPW_WAREHOUSE_W8B_ARTIFACT_DIR = process.env.ERPW_WAREHOUSE_W12I_ARTIFACT_DIR;
}

if (process.env.ERPW_WAREHOUSE_W12I_TIMEOUT && !process.env.ERPW_WAREHOUSE_W8B_TIMEOUT) {
  process.env.ERPW_WAREHOUSE_W8B_TIMEOUT = process.env.ERPW_WAREHOUSE_W12I_TIMEOUT;
}

require("./warehouse_phase_w8b_movement_review_smoke");
