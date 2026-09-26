# Contributing and keeping the workshop reproducible

[한국어](maintaining.ko.md) · [Compatibility](compatibility.en.md) · [Main guide](../README.md)

**Preserve executable instructions, both language editions, and the boundary between examples and real evidence.** A score improvement is not a reason to weaken a test or rewrite a previous result.

## Report a problem safely

Use the repository's **Issues → New issue → Workshop problem** form. Include the guide/section, language, command, expected and actual completion signal, Python/package/CLI versions, and a **sanitized** error. State whether it happened in the offline lesson or a live cloud step.

Do not attach `.env`, tokens, account/subscription identifiers, raw traces, live result directories, or unredacted screenshots. An issue report is public. If you suspect a credential exposure, rotate/revoke it through your organization's process; do not publish the value to demonstrate it.

## Make a focused change

1. Change the code and directly related English/Korean instructions together. Keep stable anchors so existing links keep working.
2. Add a regression test for the original symptom. Prefer synthetic minimal inputs; do not add customer data or copied cloud artifacts.
3. Reuse existing helpers and command parsers. Never implement a separate “demo grader” that silently diverges from the live business checks.
4. State what was verified locally and what still needs an authorized Azure rehearsal.

For setup in a fresh contributor clone, create the same Python 3.13 environment as the workshop:

```bash
python3.13 -m venv src/agent/.venv &&
source src/agent/.venv/bin/activate &&
python -m pip install -r requirements.lock.txt
```

**Checkpoint:** package installation completes. **If not:** stop and follow the package/download diagnosis in [offline-test recovery](troubleshooting.en.md#offline-tests); do not change pins merely to suppress an error.

Run the offline suite from the repository root:

```bash
python -m unittest discover -s tests -v
```

**Checkpoint:** `OK`. No Azure authentication is needed. The documentation checks validate local links/anchors, Bash syntax, real CLI parser arguments, paired language commands, and workshop handoffs. **If not:** fix the specific failing behavior or incorrect documentation; do not remove an assertion just to make the build green.

Exercise the dependency-free route separately:

```bash
python -S -m unittest discover -s tests -p test_offline_lab.py -v
```

**Checkpoint:** `OK` with site packages disabled. The tests execute both lessons in a minimal copied directory without `.env`, cloud datasets, or agent code, with network and external commands blocked. **If not:** remove the accidental runtime dependency or I/O; do not skip the credential-free checks.

## What automatic CI does

[`validate.yml`](../.github/workflows/validate.yml) runs on pushes, pull requests, and manual dispatch after publication. It has read-only repository permission, immutable action references, and no Azure login or secrets.

| Job | Configured checks |
|---|---|
| Standard-library lesson | Linux/Python 3.10, macOS/Python 3.13, Windows/Python 3.13; both language reports and the offline regression tests |
| Workshop/documentation | Linux/Python 3.13; recorded dependencies, `pip check`, all offline unit and documentation tests |

This is **not** the paid cloud release workflow. [`ci/release-gate.yml`](../ci/release-gate.yml) stays an inactive template until an owner explicitly publishes/configures it in an authorized repository. Do not add cloud sign-in, provisioning, paid evaluations, or raw evidence uploads to the default PR workflow. In particular, do not use `pull_request_target` to execute contributor code with elevated credentials.

The lesson's deliberate regression does not make default CI fail: its test asserts that the optional gate returns **1 for the right reason**.

<a id="upgrades"></a>

## SDK, API, evaluator, and model upgrades

Treat an upgrade as a **new experiment**, not a formatting change.

| Change | Minimum evidence before claiming compatibility |
|---|---|
| SDK/framework/transport | Review upstream breaking changes; update direct pins and the full snapshot together; test imports, payloads, polling, resume, errors, and cleanup |
| Model or judge | Verify deployment capability/region/quota; freeze identity/version; calibrate; run new baseline/candidate/holdout rather than mixing cohorts |
| Evaluator or threshold | Record definition/version, scale, required fields, polarity, and threshold; rerun the complete affected comparison |
| Data/policy/prompt | Preserve original hashes and artifacts; version the data; avoid dev/holdout leakage |
| Portal/CLI | Verify the actual command and checkpoint; record tool version and rehearsal date separately from source-review date |

Never regenerate a full lock snapshot from an unrelated global environment. Use a clean environment, inspect the resolved dependency graph, and check that `requirements.txt`, `src/agent/requirements.txt`, and `requirements.lock.txt` remain coherent.

New upstream documentation may require a later SDK than the frozen workshop. The [compatibility page](compatibility.en.md) records the known 2.3 → 2.4/2.5/2.7 boundaries. Do not copy a `begin_...` poller example into a job-ID polling implementation without updating state persistence and retry behavior.

An offline pass is insufficient to claim live compatibility. Rehearse the affected cloud path in an authorized isolated environment, with budget and cleanup scope agreed in advance. Retain failed attempts and report remaining failures honestly. A guide-only/source-review change does not create new live execution evidence.

## Keep the public claims auditable

Before updating a recorded-result table, preserve its cohort, language, model/judge/evaluator versions, raw result provenance, and whether inputs changed. Never copy Korean scores into the English table. Keep synthetic fixtures marked as synthetic and out of `.foundry` evidence.

When reviewing external sources, link the exact public source and date; pin a GitHub revision for comparisons. Describe what the inspected material demonstrates, not what the entire repository supposedly lacks. Do not equate stars, recency, or the number of documents with quality, and do not claim a comprehensive ranking without evidence.
