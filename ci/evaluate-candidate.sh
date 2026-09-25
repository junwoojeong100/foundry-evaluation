#!/usr/bin/env bash
# Workshop evaluation stages for an already deployed candidate, in the main guide's order (steps 5-9),
# followed by Level 3 sections 3-5. ci/release-gate.yml signs in again before each stage; you can also run
# the stages in order from the repository root: baseline, candidate, holdout, agent, traces, red-team.
#
# Required: BASELINE_VERSION and CANDIDATE_VERSION (hosted agent versions deployed with V1 and V2),
#           REVIEW_ROW_ID and REVIEW_REASON (the row and reason you recorded in step 6).
# The red-team stage sends harmful prompts; run it only if your organization approved red teaming.
#
# The baseline is collected again, so the step-6 review is recorded on the same row ID of this run.
set -euo pipefail

request_tokens() {
  # In CI the federated sign-in expires within minutes, so fetch every data-plane token the stage needs now;
  # the workshop's Azure CLI credential then reuses them from the cache.
  for scope in https://ai.azure.com/.default https://api.applicationinsights.io/.default; do
    az account get-access-token --subscription "$AZURE_SUBSCRIPTION_ID" --scope "$scope" --output none
  done
}

wait_for_telemetry() {
  # Application Insights can lag a few minutes behind collection; monitor fails until every trace arrives.
  for attempt in 1 2 3 4 5 6 7 8 9 10; do
    if python scripts/workshop.py monitor --label "$1"; then
      return 0
    fi
    echo "Telemetry for $1 is not complete yet; retrying in 60 seconds ($attempt/10)."
    sleep 60
  done
  return 1
}

case "${1:-}" in
  baseline)
    request_tokens
    export LAB_PROMPT_VERSION=v1 LAB_AGENT_VERSION="$BASELINE_VERSION"
    python scripts/workshop.py collect --split dev --label baseline
    python scripts/workshop.py evaluate --label baseline
    python scripts/workshop.py compare --labels baseline
    wait_for_telemetry baseline
    python scripts/workshop.py summary --labels baseline
    python scripts/workshop.py feedback --label baseline --row-id "$REVIEW_ROW_ID" --reason "$REVIEW_REASON"
    ;;
  candidate)
    request_tokens
    export LAB_PROMPT_VERSION=v2 LAB_AGENT_VERSION="$CANDIDATE_VERSION"
    python scripts/workshop.py collect --split dev --label improved
    python scripts/workshop.py evaluate --label improved
    python scripts/workshop.py compare --labels baseline improved
    wait_for_telemetry improved
    python scripts/workshop.py summary --labels baseline improved
    ;;
  holdout)
    request_tokens
    export LAB_PROMPT_VERSION=v2 LAB_AGENT_VERSION="$CANDIDATE_VERSION"
    python scripts/workshop.py collect --split holdout --label holdout
    python scripts/workshop.py evaluate --label holdout
    python scripts/workshop.py compare --labels baseline improved holdout
    wait_for_telemetry holdout
    python scripts/workshop.py summary --labels holdout
    python scripts/workshop.py verify --baseline baseline --candidate improved --holdout holdout
    ;;
  agent)
    request_tokens
    export LAB_PROMPT_VERSION=v2 LAB_AGENT_VERSION="$CANDIDATE_VERSION"
    python scripts/workshop.py register-evaluators
    # Foundry can finish an agent run without one evaluator's results; --retry-failed replaces only such runs.
    if ! python scripts/workshop.py evaluate-agent --split dev; then
      python scripts/workshop.py evaluate-agent --split dev --retry-failed
    fi
    ;;
  traces)
    request_tokens
    export LAB_PROMPT_VERSION=v2 LAB_AGENT_VERSION="$CANDIDATE_VERSION"
    python scripts/workshop.py evaluate-traces --label improved
    ;;
  red-team)
    request_tokens
    python scripts/workshop.py red-team --model sol
    ;;
  *)
    echo "usage: bash ci/evaluate-candidate.sh baseline|candidate|holdout|agent|traces|red-team" >&2
    exit 2
    ;;
esac
