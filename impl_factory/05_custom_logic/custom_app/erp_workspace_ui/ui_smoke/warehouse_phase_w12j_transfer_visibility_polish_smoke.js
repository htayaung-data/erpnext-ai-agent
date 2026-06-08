process.env.ERPW_WAREHOUSE_W8C_EXPECT_W12J = "1";
process.env.ERPW_WAREHOUSE_W8C_PHASE_LABEL = "Warehouse W12J transfer visibility polish";
process.env.ERPW_WAREHOUSE_W8C_SUMMARY_NAME = "warehouse-w12j-transfer-visibility-polish-summary.json";

if (process.env.ERPW_WAREHOUSE_W12J_ASSET_ROOT && !process.env.ERPW_WAREHOUSE_W8C_ASSET_ROOT) {
  process.env.ERPW_WAREHOUSE_W8C_ASSET_ROOT = process.env.ERPW_WAREHOUSE_W12J_ASSET_ROOT;
}

if (process.env.ERPW_WAREHOUSE_W12J_ARTIFACT_DIR && !process.env.ERPW_WAREHOUSE_W8C_ARTIFACT_DIR) {
  process.env.ERPW_WAREHOUSE_W8C_ARTIFACT_DIR = process.env.ERPW_WAREHOUSE_W12J_ARTIFACT_DIR;
}

if (process.env.ERPW_WAREHOUSE_W12J_TIMEOUT && !process.env.ERPW_WAREHOUSE_W8C_TIMEOUT) {
  process.env.ERPW_WAREHOUSE_W8C_TIMEOUT = process.env.ERPW_WAREHOUSE_W12J_TIMEOUT;
}

require("./warehouse_phase_w8c_transfer_visibility_smoke");
