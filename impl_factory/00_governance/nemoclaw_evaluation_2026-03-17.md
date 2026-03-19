# NVIDIA NemoClaw Evaluation for ERP AI Assistant

Date: 2026-03-17  
Scope: evaluate NVIDIA NemoClaw for possible future integration into this project  
Decision owner: governance / AI assistant program

## 1) Executive Decision
1. **Do not integrate NemoClaw into production or core runtime now.**
2. **Track NemoClaw as a future security-plane and sandbox-execution candidate only.**
3. **Re-evaluate after upstream maturity gates are met and after a contained sidecar proof-of-concept is possible.**

Reason in one sentence: NemoClaw is promising for isolated agent execution, network policy, and sandbox controls, but it is currently alpha-stage and does not satisfy this project's contract-critical runtime, audit, ERP policy, and write-safety requirements on its own.

## 2) What NemoClaw Is
Based on NVIDIA's public repository and docs as of 2026-03-17, NemoClaw is an NVIDIA-maintained open source stack for running OpenClaw assistants inside the OpenShell runtime with policy-controlled sandboxing and NVIDIA-routed inference.

Observed upstream facts:
1. Official repo exists at `NVIDIA/NemoClaw`.
2. Repository metadata shows it was created on 2026-03-15.
3. Repo/package version is `0.1.0`.
4. README explicitly labels the project as **Alpha software** and says it "should not yet be considered production-ready".
5. Docs describe a TypeScript CLI plus a Python blueprint that manages OpenShell resources.
6. The published quickstart currently requires a fresh OpenClaw installation, Ubuntu 22.04+, Node 20+, Docker, and OpenShell.
7. Docs show useful controls for:
   - restricted network egress,
   - filesystem confinement,
   - process restrictions,
   - inference routing,
   - operator approval of blocked outbound requests,
   - sandbox status/log inspection,
   - runtime model switching.
8. Upstream release notes page points users to GitHub releases, but as checked on 2026-03-17 there are no published GitHub releases or tags yet.

## 3) Why It Is Interesting for This Project
NemoClaw maps best to parts of our **Security Plane** and operational sandboxing goals, not to the core semantic ERP assistant contract.

Potential benefits if the project matures:
1. Stronger isolation for autonomous or semi-autonomous tool execution.
2. Deny-by-default outbound network control with operator approval flow.
3. Better separation between application runtime and agent runtime.
4. A path to run higher-risk external-tool tasks in a dedicated sandbox instead of inside the ERP app process.
5. Useful observability for sandbox status, logs, and egress activity.

This makes NemoClaw more relevant as a future host for:
1. external research/tool agents,
2. controlled background automations,
3. high-risk integrations that should not execute inside the Frappe worker/web process.

## 4) Why It Does Not Fit the Current Core Architecture Yet
This repository's active contract is the `v7.3` ERP assistant contract in `ai_assistant_contract_v2.md`. That contract requires deterministic ERP semantics, typed planning, validation, write confirmation, and auditability that NemoClaw does not currently provide as a drop-in capability.

Current mismatch areas:
1. **Wrong layer**
   NemoClaw is a sandbox/runtime wrapper around OpenClaw and OpenShell. Our project's hardest problems are business-request parsing, constraint building, capability retrieval, typed FAC planning, result validation, and ERP-safe response composition.
2. **No direct ERP/Frappe integration story**
   The current upstream path is CLI and sandbox oriented, and the quickstart requires a fresh OpenClaw install. Our assistant is an embedded ERPNext Desk assistant with a Frappe-based runtime.
3. **No evidence of our required typed business contracts**
   Our contract requires `BusinessRequestSpec`, `ConstraintSet`, `CapabilityCandidateSet`, `ExecutionPlan`, `ValidationResult`, `ClarificationEnvelope`, `ResponseEnvelope`, and `TurnAuditEnvelope`. NemoClaw docs describe sandbox orchestration, not these ERP semantics.
4. **No evidence of ERP policy enforcement**
   Our contract requires RBAC plus row-level and field-level policy enforcement at the tool boundary. NemoClaw docs show network/filesystem/process policy, which is useful but not a substitute for ERP authorization controls.
5. **No evidence of our write-safety workflow**
   Our contract requires `draft -> confirm -> execute -> audit`, explicit confirmation, and idempotency for writes. NemoClaw's operator approval flow is for blocked network requests, not ERP document mutation approval.
6. **Audit gap**
   NemoClaw exposes status/log/TUI monitoring, but that is different from our required per-turn deterministic audit envelope with parser output, constraints, candidate selection, validation result, and final response hash.
7. **Provider/runtime coupling**
   Current docs emphasize NVIDIA-routed inference via OpenShell/OpenClaw. Our current assistant runtime calls models directly from Frappe and is optimized around the existing `v7` contract rather than an external OpenClaw-hosted agent process.
8. **Maturity risk**
   Alpha label, `0.1.0` versioning, repository age of two days, active security fixes landing immediately after launch, and no tagged releases/tags make it too early for contract-critical adoption.

## 5) Fit Against This Project's Governance Contract
Assessment against `impl_factory/00_governance/ai_assistant_contract_v2.md`:

| Contract area | Required here | NemoClaw status on 2026-03-17 | Evaluation |
|---|---|---|---|
| Runtime semantic correctness | Typed ERP request parsing and plan generation | Not provided as an ERP-specific contract | Not sufficient |
| FAC-only business facts | ERP/FAC output remains sole business source | Not addressed in upstream docs | Not sufficient |
| Deterministic validation | Per-turn semantic validation with verdicts | Not shown | Not sufficient |
| Clarification discipline | Blocker-only clarification contract | Not shown | Not sufficient |
| Turn audit envelope | Structured per-turn audit record | Logs/status only | Partial at best |
| Write safety | `draft -> confirm -> execute -> audit` | Network approval only, not ERP write approval | Not sufficient |
| Security plane | Network/filesystem/process controls | Clearly present | Strong fit |
| Deployment fit | Embedded ERP assistant runtime | Fresh OpenClaw sandbox flow | Weak fit |

Conclusion: NemoClaw is a **possible future supplement for the Security Plane**, but it is **not a candidate replacement for the `v7` ERP assistant engine**.

## 6) Recommendation
Recommended governance position:
1. Keep the current `v7` ERP assistant architecture as the system of record.
2. Do not re-platform the assistant around NemoClaw in 2026 H1.
3. Treat NemoClaw as a watchlist dependency for a later sidecar/worker-sandbox pattern.
4. Limit any future evaluation to non-authoritative tool-execution use cases first.

## 7) Maturity Gates Before Reconsidering Integration
We should only revisit integration after most or all of the following are true:

### 7.1 Upstream Product Maturity
1. NemoClaw is no longer explicitly labeled alpha.
2. At least two stable tagged releases exist.
3. Upgrade notes and version compatibility guarantees are published.
4. There is a clearer support matrix for host OS, Docker/OpenShell versions, and deployment modes.

### 7.2 Integration Readiness
1. NVIDIA provides a stable API, SDK, or service interface that can be invoked from our Python/Frappe runtime without requiring a fresh end-user OpenClaw installation.
2. Sidecar or remote-worker deployment is documented and supportable for enterprise applications.
3. Configuration can be automated non-interactively for CI, staging, and production.

### 7.3 Governance and Audit Readiness
1. Machine-readable event/audit export is available, not only TUI/log inspection.
2. Policy decisions and operator approvals can be captured in durable artifacts.
3. Sandbox events can be correlated with our `trace_id` and audit envelopes.

### 7.4 Security and Policy Readiness
1. Policy APIs are stable and scriptable.
2. There is a clean way to pre-approve only the minimum required endpoints.
3. The deployment model supports our own approval workflow and evidence retention.

### 7.5 Architectural Compatibility
1. NemoClaw can run as a bounded execution environment for external tools while our `v7` parser, resolver, planner, validator, and ERP write FSM remain authoritative.
2. The integration path does not weaken FAC-only fact sourcing.
3. The integration path does not bypass existing RBAC, row-level, field-level, or write-confirmation controls.

## 8) Approved Future Adoption Pattern
If NemoClaw matures, the only approved near-term adoption pattern is:

1. **Sidecar sandbox worker**
   Run NemoClaw outside the ERP app process as a bounded worker/sandbox.
2. **Non-authoritative tool execution only**
   Use it for web/tool tasks or external automation, not for direct business-fact answering without `v7` validation.
3. **Current `v7` engine remains authoritative**
   `BusinessRequestSpec`, constraints, candidate selection, planner, validator, and response composer remain in this codebase.
4. **ERP writes still go through existing write FSM**
   No direct document writes from NemoClaw without our current confirmation, policy, and audit controls.
5. **Phased rollout only**
   shadow -> controlled internal canary -> restricted production use, with explicit rollback.

## 9) Trigger to Revisit
Open a formal re-evaluation only when all three are true:
1. upstream publishes stable tagged releases,
2. a sidecar/service integration path exists,
3. we can prove no contract regression in auditability, ERP authorization, and write safety.

## 10) Source References
Primary upstream sources checked on 2026-03-17:
1. NVIDIA GitHub repository: https://github.com/NVIDIA/NemoClaw
2. NVIDIA NemoClaw documentation: https://docs.nvidia.com/nemoclaw/latest/
3. README (alpha status, quickstart, architecture summary): https://raw.githubusercontent.com/NVIDIA/NemoClaw/main/README.md
4. Architecture doc: https://docs.nvidia.com/nemoclaw/latest/reference/architecture.html
5. Monitoring doc: https://docs.nvidia.com/nemoclaw/latest/monitoring/monitor-sandbox-activity.html
6. Network approval doc: https://docs.nvidia.com/nemoclaw/latest/network-policy/approve-network-requests.html
7. Inference switching doc: https://docs.nvidia.com/nemoclaw/latest/inference/switch-inference-providers.html

Local project references:
1. `impl_factory/00_governance/ai_assistant_contract_v2.md`
2. `impl_factory/00_governance/ai_assistant_roadmap_2026.md`
3. `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/ai_core/llm/openai_client.py`
4. `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/ai_core/v7/write_engine.py`
5. `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/ai_core/chat/turn_audit.py`
