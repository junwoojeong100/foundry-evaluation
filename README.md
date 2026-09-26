# Run, evaluate, and improve a travel-policy agent

[한국어 가이드](README.ko.md)

**Run an AI agent that finds travel policies and answers expense questions, then check whether changing its instructions improves its answers.** The agent code and both instruction versions (V1, V2) are provided; you write no code.

**No previous terminal, Azure, or AI-agent experience is assumed.** Your job is to **copy a command → check its completion signal → describe your actual result in your own words**.

**Allow about 120 minutes with an environment already prepared.** For first-time self-study, allow extra time to read and follow the explanations. Collect 48 real responses, then **review one case, compare V1 → V2, and report whether V2 also works on new questions**. Low scores are valid workshop results. Perfect scores and production approval are not the goal.

<a id="start-here"></a>
<a id="other-starts"></a>
<a id="other-situations"></a>
<a id="choose-your-starting-point"></a>

## Start the workshop

**Follow only the starting point that matches you.** You do not need to read every linked guide.

| Your situation | Start here |
|---|---|
| Your instructor gave you a complete team `.env` (class) | Read the [concepts](#understand-first) and [how to follow](#how-to-follow) below, then [step 1](#start) and **steps 1–10 in order** |
| Your `.env` is not ready, and the Foundry, Search, and observability services you will use all exist | The environment owner completes [existing-environment preparation](docs/instructor.en.md#existing-foundation) → follows its handoff |
| A required foundation service is missing and you need a **new dedicated environment** | Finish the prerequisites and steps 1–6 in [Create a new environment](docs/environment.en.md) → follow its handoff to [1-4 binding](#bind-project) |
| Continuing an earlier attempt | [Resume in the same folder](docs/troubleshooting.en.md#resume): next unexecuted block after a normal pause; command recovery after an error or uncertain outcome |

**A missing `.env` does not mean you need new services.** Choose one preparation path. In self-study, you are the environment owner.

**Tools required:** Git, Python 3.13, Bash, curl, Azure CLI, azd with the `microsoft.foundry` extension, an editor (VS Code recommended), and a browser; on Windows, use WSL ([install and check](docs/instructor.en.md#tools)). Tool installation and Azure preparation are outside the 120 minutes.

**Cost:** local execution still calls paid Azure models and Search. For your exclusive environment created with the new-environment tools, [delete its resource group](docs/environment.en.md#final-cleanup) after step 10 to stop foundation costs. For existing services, follow the [environment owner's cleanup scope](docs/instructor.en.md#foundation-cleanup).

<details>
<summary>Optional: delegate execution to Copilot CLI</summary>

Follow the [Copilot guide](docs/copilot.en.md); do not also execute the steps manually. Manual execution needs neither Copilot nor Playwright.

</details>

<a id="understand-first"></a>

## Understand first: a convincing answer is not necessarily a correct one

Imagine an employee at the fictional **Hanbit Technology** asking the question below. The policies are synthetic training material, not a real company's rules. The agent explains them; it does not book travel, approve requests, or make payments.

> For a business trip to Busan on 2026-09-10, is lodging at KRW 170000 per night allowed by policy? Please also state the limit.

The provided current policy, `TRAVEL-2026`, sets a lodging limit of **KRW 180000 per night**. The answer should explain that this expense is within the limit and **identify the policy supporting it**. Fluent wording alone is insufficient if the amount, decision, or citation is wrong. This is `D01` in the `dev` questions used for improvement, not an early look at the separate new questions.

| Term | Plain meaning | In this workshop |
|---|---|---|
| Model | The engine that reads input and generates an answer | Each request calls one of `sol`, `luna`, or `astra` |
| Agent | The program connecting retrieval and model calls | The provided Python travel-policy app |
| Instructions (prompt) | Rules telling the model how to answer | Original `V1` and candidate `V2` |
| Evaluation | Checking an answer against criteria | Python business checks and Foundry's AI scoring |

**Microsoft Foundry** is an Azure platform for deploying, evaluating, and observing AI agents. Here is how the workshop fits together. This diagram is **an explanation, not commands to run**.

```text
Question -> Python agent (step 3: your PC / step 4 onward: Azure)
              |-- Foundry IQ: retrieve policy evidence from Azure AI Search
              |-- Question + evidence + V1/V2 instructions -> one candidate model -> answer
              `-- Retrieval/model-call records (traces) -> Application Insights

Agent answers -> business checks and saving -> Foundry evaluation -> human review -> reevaluate V2
```

The three models do not debate or vote: **compare their separate answers to the same questions**. Saving a review does not train the model automatically. The exercise changes the provided instructions and **measures whether that actually helps**.

<a id="workshop-overview"></a>

## The 10-step path

**Steps 1–4 get the agent running, 5–9 evaluate and compare it, and 10 cleans up.** This table is your route map; execute commands one block at a time in each step below.

| Step | Continue when |
|---|---|
| [1. Prepare](#start) | Tests, both sign-ins, preflight, and project binding succeed |
| [2. Retrieve policies](#lab-a) | Your knowledge base returns `TRAVEL-2026` |
| [3. Run locally](#local) | Readiness is `HTTP 200` and the agent returns a real V1 answer |
| [4. Deploy](#deploy) | The hosted answer has a numeric agent version |
| [5. Evaluate V1](#lab-c) | 6 questions × 3 models = 18 evaluated V1 responses |
| [6. Review one case](#lab-d) | Your review is saved with the case's original trace |
| [7. Evaluate V2](#lab-e) | The **same 6 questions** × 3 models = 18 evaluated V2 responses and a before/after comparison |
| [8. Check new questions](#lab-f) | 4 new questions × 3 models = 12 evaluated responses from unchanged V2 |
| [9. Verify and report](#lab-g) | 48 responses, 48 traces, and your review lineage are verified; your three-point report is filled in |
| [10. Clean up](#cleanup) | Only your owned objects are removed |

**Time:** 1–2: 25 min · 3–4: 15 min · 5–6: 30 min · 7–8: 30 min · 9–10: 15 min · buffer: 5 min. **Report in step 9, then clean up in step 10**; optional [Levels 2–3](#levels) go in between.

<a id="how-to-follow"></a>

### How to follow the steps

**Coming from an environment-setup guide?** Read the [concepts above](#understand-first) too. This is reading only; do not repeat installation or sign-in already completed.

- **Class runner:** for each team `.env`, **one person runs commands with their own account, PC, and one workshop folder**; teammates review that screen together. Running the same `.env` on several PCs causes ownership conflicts over the same named resources. For individual execution, obtain a separate `.env` with distinct `LAB_PREFIX` and `LAB_AGENT_NAME` values for each runner before starting.
- **Where:** follow the bold label before each block: **Terminal A**, **Terminal B** (step 3 only), **Editor**, or **Portal**. "Your agent" means `LAB_AGENT_NAME`.
- **One block at a time:** follow **location → run the command → checkpoint → next block**. Wait for the input prompt—the line where you can type another command—to return, except for step 3's server. When asked for input, paste only the requested value and press Enter.
- **When to stop:** for an error or a missing required **Checkpoint** value, follow the **If not** below it to [recover only that command](docs/troubleshooting.en.md#resume). Once execution finishes, **record and continue** for low valid scores. Never rerun for a better score. To finish early or continue another day, use [the early-stop path](#stop-early).
- **New terminal later:** start Bash and run the [restore block](#resume-shell) with the path you noted; step 3's Terminal B block already includes it.
- **Record:** open **one** text document in your editor and record the values each step requests. Before a break, also save `Last completed block / Next block / Workshop folder`. In 9-3, organize **that same document** using the [report template](#finish).

**Do not open `data/en/holdout.jsonl` before step 8.** Terms are explained where you use them ([full glossary](docs/reference.en.md#terms)). Open collapsed references, examples, or the video only when needed.

### Which window do I use?

Keep the guide open in your browser and switch between these work surfaces. **Terminal A and B are names used by this guide, not application names.**

| Label in the guide | How to open it | What to do there |
|---|---|---|
| **Terminal A** | Terminal on macOS, your terminal on Linux, or your installed WSL Linux terminal such as Ubuntu on Windows. After opening the folder, VS Code **Terminal → New Terminal** also works | Paste commands and press Enter. Only step 3's server intentionally keeps running without returning a prompt |
| **Terminal B** | Only in step 3: another terminal window/tab, or **+** in VS Code's terminal panel | Send a request while A keeps the server running. Step 3-2 sets this new terminal's folder and environment |
| **Editor / Portal** | VS Code / Foundry in a web browser | Read and save files/notes in the editor; inspect deployment, evaluation, and trace screens in the portal |

On Windows, [connect VS Code to WSL](docs/instructor.en.md#tools) first. Do not paste workshop commands into PowerShell, Command Prompt, or the browser address bar.

<a id="reading-commands"></a>

### Reading commands, files, and output

| What you see | How to read it |
|---|---|
| Repository root / "this folder" | The top of the code folder where commands run: the 1-1 clone in a class, or the `/workshop` folder from setup step 6-3 for a new environment |
| Code block | Copy only the commands inside it, without a leading `$`. After collection recovery, first apply your [actual labels and concurrency](docs/troubleshooting.en.md#run-values) |
| `cd`, `pwd`, `ls` | Change folder, print the current folder's path, and list files, respectively |
| `&&` | Run the next command only if the previous one succeeds |
| `\` at the end of a line | The command continues on the next line. Copy the **whole block at once**, including `\` |
| `$PWD`, `"$ROW_ID"`, and similar code | The terminal substitutes the value. Do not remove `$` or quotes, or replace the variables yourself |
| `<your agent>` in an output description | Your actual `LAB_AGENT_NAME` value appears in the output. Do not type this placeholder |
| `language: en` | JSON displays it as `"language": "en"`. `true` means true, `false` means false, and `[]` is an empty list |

`python scripts/workshop.py ...` runs the provided workshop tool. The following word, such as `collect` or `evaluate`, selects its job; options such as `--label` supply inputs. You do not need to memorize them: each step explains what it uses.

Long JSON or queries are normal. **Checkpoint** values are usually at the **bottom** of the output. Follow **this guide's next block**, not the `Next:` suggestions or `Update available` notice printed by a tool.

`.env` (settings) and `src/agent/.foundry/` (results) are hidden files or folders because their names start with a dot. Open the workshop folder with VS Code **File → Open Folder** to see them in the Explorer. After editing a file, save with **Ctrl+S (macOS: Cmd+S)**. Never run or `source` `.env`.

For help, share only the failed command, error, and step—not passwords, tokens, or the whole `.env`. “Instructor” and “environment owner” mean the instructor in a class and you in self-study.

<a id="background-learning-loops-and-frontier-ecosystems"></a>

<a id="start"></a>

## 1. Prepare your workspace

**Goal:** a fresh English workshop folder, signed in and bound to your project. **If you created your own environment** (step 6 of [Create a dedicated environment](docs/environment.en.md) is done), skip 1-1 to 1-3 and the preflight, and run only the [binding](#bind-project).

<a id="source-setup"></a>

### 1-1. Get the source and `.env`

**What are you preparing?** A `clone` downloads the provided code folder to your PC. It does not create Azure resources or sign you in. Because each learner can use a different Azure environment, you receive `.env` separately from the code.

**Terminal A — start Bash:** open a terminal and run this (fine even if it already runs Bash; macOS starts zsh by default, and on Windows use the WSL terminal):

```bash
bash
```

**Checkpoint:** a new input prompt appears. No new window or success message is expected.

**If not:** for `command not found`, check [Bash/WSL installation](docs/instructor.en.md#tools).

**Terminal A — clone into a new folder:** if you already have an **unused clone or extracted ZIP**, skip this block; `cd` into its root and run `ls README.md && pwd` instead.

```bash
git clone https://github.com/junwoojeong100/foundry-evaluation.git foundry-evaluation-en &&
cd foundry-evaluation-en &&
ls README.md &&
pwd
```

**Checkpoint:** `README.md` and this folder's absolute path are printed, so Terminal A is in the repository root ("this folder" from here on). Note the path; you use it to return from a new terminal.

**If not:** for `already exists`, replace both `foundry-evaluation-en` in the command with a new name, such as `foundry-evaluation-en-2`; never reuse a folder with earlier results.

<a id="workspace-settings"></a>

**Editor — add `.env` (class participants):** open this folder with VS Code **File → Open Folder**. Put the instructor's `.env` next to `README.md` (the top of the folder) in the Explorer, open it, and confirm the items below. Do not overwrite an existing `.env`; ask the instructor.

Each line is `SETTING_NAME=value`: **the name is on the left, your environment's value on the right**. For example, `LAB_LANGUAGE=en` selects the English workshop; it is not a command to enter in the terminal.

- **File:** `.env`, not `.env.txt`.
- **Who signs in:** `AZURE_EXPECTED_USERNAME` must be the runner's **own Azure sign-in name/email**. `.env` supplies settings, not an account, password, or access permission. The instructor prepares access for that account; the runner completes their own sign-in and MFA.
- **Role-assignment support:** if you cannot assign roles, agree with the instructor **who will help and when for 2-1 `prepare-iq` and 4-2 `grant-agent-access`** ([access checks](docs/instructor.en.md#access)). The administrator makes only the required assignments in their own session; the runner keeps their own account and folder.
- **Your values:** `LAB_LANGUAGE=en`, `LAB_PROMPT_VERSION=v1`, and team names in `LAB_PREFIX` and `LAB_AGENT_NAME` that no one else uses.
- **Instructor values:** `MODEL_*_DEPLOYMENT` and `LAB_AUX_DEPLOYMENT` hold the instructor's deployment names.
- **Never:** empty values, `<...>` placeholders, passwords, keys, or tokens.

**Terminal A — check the file name and two values:**

```bash
ls -a .env &&
grep -E '^LAB_(LANGUAGE|PROMPT_VERSION)=' .env
```

**Checkpoint:** `.env` prints, followed by the two lines `LAB_LANGUAGE=en` and `LAB_PROMPT_VERSION=v1`, and the editor check above passes. Never run or `source` `.env`; Python reads it.

**If not:** for `No such file`, check whether the file was saved as `.env.txt` or `env` and rename it to exactly `.env`. Ask the instructor about missing values or a different `AZURE_EXPECTED_USERNAME`; continue only with settings and access prepared for the runner's account. Never borrow someone else's account/password or guess settings.

<details>
<summary>Why these values matter</summary>

- Keep `LAB_LANGUAGE` and `LAB_PROMPT_VERSION` unchanged when resuming a run; results and ownership are language-bound.
- Team names in `LAB_PREFIX` and `LAB_AGENT_NAME` use 3–50 lowercase letters, digits, or hyphens and start with a letter. When deriving candidate deployment names, **choose a 3–44-character `LAB_PREFIX` from the start** so the `-astra` suffix fits within 50 characters ([existing deployment-name requirements](docs/instructor.en.md#candidate-names)).
- Changing a `MODEL_*` value does not create a model. Keep the instructor's names even when you change team names ([name distinctions](docs/reference.en.md#model-names)).

</details>

<a id="python-setup"></a>

### 1-2. Create the Python environment and run the offline tests

**Why a virtual environment?** It keeps this workshop's Python packages separate from other projects. The tests below check the provided code without calling Azure.

| Similar-looking name | Actual purpose | Your action |
|---|---|---|
| `.env` | A **settings file** identifying which Azure environment to use | Check the supplied values in 1-1 |
| `src/agent/.venv/` | A **virtual-environment folder** containing this workshop's Python and packages | Create and activate it below |
| `src/agent/.foundry/` | A **results and review-record folder** created by the workshop tools later | Read results after they exist; it may be absent at the start |

`source .../.venv/bin/activate` below **activates the virtual environment**. It does not contradict the warning against running `source` on the different file `.env`.

**Terminal A — install:**

```bash
python3.13 -m venv src/agent/.venv &&
source src/agent/.venv/bin/activate &&
python -m pip install -r requirements.txt
```

**Checkpoint:** installation logs finish and the prompt returns with `(.venv)`. `Requirement already satisfied` is normal too.

**If not:** for a missing `python3.13`, check [tool installation](docs/instructor.en.md#tools). For a package-download error, check your network and repeat only this install block; do not start the tests yet.

**Terminal A — test:**

```bash
python -m unittest discover -s tests -v
```

**Checkpoint:** the test output ends with **`OK`**.

**If not:** do not continue. For installation problems, follow the install block's recovery above. For a test `FAIL` or `ERROR`, use [offline-test recovery](docs/troubleshooting.en.md#offline-tests) to distinguish the cause. Do not edit tests or references to make them pass.

<a id="login"></a>

### 1-3. Sign in to Azure CLI and azd

**Why two sign-ins?** `az` inspects and prepares Azure resources; `azd` runs and deploys the agent. They manage sign-in separately, so sign in to both with the same account. Signing in to the browser portal does not replace either one.

**Reading the IDs:** a tenant is the organization directory used for this Azure sign-in; a subscription groups the Azure resources and billing you will use. The IDs identify those targets. Use the values supplied in `.env`; do not create or guess replacements.

**Terminal A:** run blocks 1–4 in order in this terminal; block 4 checks both sign-ins.

- Block 1 stores the IDs that blocks 2–4 reuse. Paste only the values after `=` from `.env`, never a password or login code.
- After blocks 2 and 3, finish the browser sign-in as `AZURE_EXPECTED_USERNAME` (choose **Use another account** if needed) and wait for the prompt.
- If block 2 or 3 shows an error, stop there and do not run the next block.

<a id="login-input"></a>

**Terminal A — 1. enter the IDs:** this keeps the sign-in in this folder's `.azure-cli/` (never share or commit it):

```bash
export AZURE_CONFIG_DIR="$PWD/.azure-cli" &&
read -r -p "AZURE_TENANT_ID value from .env: " LOGIN_TENANT_ID &&
read -r -p "AZURE_SUBSCRIPTION_ID value from .env: " LOGIN_SUBSCRIPTION_ID
```

**Checkpoint:** the prompt returns after you enter both IDs. Sign-in has not started yet.

**If not:** rerun only this block to correct an entry. For `read: -p: no coprocess`, run `bash` first, then enter the IDs again.

**Terminal A — 2. sign in to Azure CLI:** choose the `.env` subscription if asked:

```bash
az login --tenant "$LOGIN_TENANT_ID" --subscription "$LOGIN_SUBSCRIPTION_ID" --output none
```

**Checkpoint:** browser sign-in finishes and the terminal prompt returns without an error. `--output none` suppresses the account JSON.

**If not:** [recover only Azure CLI sign-in](docs/troubleshooting.en.md#login), then continue to block 3.

<a id="azd-login"></a>

**Terminal A — 3. sign in to azd** with the same account:

```bash
azd auth login --tenant-id "$LOGIN_TENANT_ID"
```

**Checkpoint:** browser sign-in finishes and the terminal prompt returns without an error. The next block checks the actual account.

**If not:** [recover only azd sign-in](docs/troubleshooting.en.md#login); do not repeat a successful Azure CLI sign-in.

<a id="login-check"></a>

**Terminal A — 4. verify both sign-ins:**

```bash
az account show --subscription "$LOGIN_SUBSCRIPTION_ID" \
  --query "{user:user.name,tenant:tenantId,subscription:id,state:state}" --output json &&
azd auth status --output json
```

**Checkpoint:** CLI `user` and azd `email` equal `AZURE_EXPECTED_USERNAME`; `tenant` and `subscription` equal the `.env` IDs; `state` is `Enabled`; `status` is `authenticated`.

**If not:** sign in again with the configured account; if no browser opens, see [authentication troubleshooting](docs/troubleshooting.en.md#login).

<a id="project-binding"></a>

### 1-4. Check and bind the project

**Terminal A — check the project:** the first output can take around 30 seconds.

```bash
python scripts/workshop.py preflight
```

**Checkpoint:** the bottom of the output shows `missing_models: []` and `language: en`, and above them `gpt-6-sol`, `gpt-6-luna`, and `gpt-6-astra` all show `deployed: true`.

**If not:** for `language: ko`, change `LAB_LANGUAGE` in `.env` to `en` only if this folder is unused. For a nonempty `missing_models`, first check that the `MODEL_*_DEPLOYMENT` values in `.env` are exactly as you received them. If they are, the deployments are not ready; ask the environment owner (for your own environment, recheck [environment step 6-1](docs/environment.en.md#setup-candidates) in that folder).

<details>
<summary>Example screen: successful preflight</summary>

Find `language: en` and `missing_models: []`; the lines above them list the three candidates.

![English project and model preflight](docs/assets/live-en-20260923b/screenshots/01-ready.webp)

</details>

<a id="bind-project"></a>

**Terminal A — bind:** run this after passing the preflight checkpoint above. **If the environment guide (step 6) brought you here,** its `prepare-models` already ran the preflight, so run only this block in the folder opened by that guide's 6-3 “open the workshop folder” block.

```bash
python scripts/workshop.py bind
```

**Checkpoint:** `Bound <your agent> to /subscriptions/.../projects/<your project>`.

**If not:** see the `bind` row in [common symptoms](docs/troubleshooting.en.md#symptoms).

<a id="resume-shell"></a>

<details>
<summary>Later, in a new terminal: restore this folder's environment</summary>

In the new terminal, start `bash`, run this block, and paste this folder's absolute path you noted; it reuses your sign-in cache. Step 3's Terminal B block already includes it. **Before the virtual environment exists,** skip restoration and continue the next task in your notes in the existing folder. If 1-1 is complete, that is [1-2](#python-setup).

```bash
read -r -p "Absolute workshop folder path: " WORKSHOP_DIR &&
cd "$WORKSHOP_DIR" &&
source src/agent/.venv/bin/activate &&
export AZURE_CONFIG_DIR="$PWD/.azure-cli"
```

**Checkpoint:** the prompt shows `(.venv)` and no error appears. Never use `az account set`, and never change `LAB_LANGUAGE` after a run has started.

**If not:** for `No such file or directory`, paste the full path starting with `/` again, without quotes and without `~`. If you forgot it, use **Terminal → New Terminal** in the VS Code window that has your workshop folder open, then run `pwd`.

**After restoring:** if you started step 5, [restore the run values](docs/troubleshooting.en.md#run-values) for labels and concurrency before returning to the next unexecuted block in your notes. Before step 5, that input is unnecessary. “Next: step 2” below is only for someone finishing step 1 for the first time. If a command reports an expired sign-in, use [sign-in recovery](docs/troubleshooting.en.md#login).

**If you closed the terminal during sign-in:** restoration does not restore `LOGIN_TENANT_ID` or `LOGIN_SUBSCRIPTION_ID`. Run [only 1-3's ID-input block](#login-input), then continue the unfinished sign-in or verification. Do not repeat successful sign-ins.

</details>

**Next:** [2. Add and retrieve organizational knowledge](#lab-a)

<a id="lab-a"></a>
<a id="2-add-and-retrieve-organizational-knowledge--lab-a"></a>

## 2. Add and retrieve organizational knowledge

**Goal:** a searchable **knowledge base (KB)** of seven synthetic policies that returns the right one.

**Why start with retrieval?** If the needed policy is not retrieved, changing the model alone may not fix the answer. `prepare-iq` registers the policies; `retrieve` finds evidence in them. **This is not yet the step that generates the final travel-expense answer.**

<a id="knowledge-registration"></a>

### 2-1. Register the policies

**Editor:** open `data/en/policies.json` and use **Ctrl+F (macOS: Cmd+F)** to find `TRAVEL-2026`. In its `content`, check the **effective date `2026-09-01`, status `published`, and lodging limit of `KRW 180000` per night**. Do not edit the file. The corpus also contains old policies and a draft, so not every retrieved document is current policy.

**Terminal A:**

```bash
python scripts/workshop.py prepare-iq
```

**Checkpoint:** after the `Created: ...` lines, `Foundry IQ ready: <your KB>; 7 synthetic documents.` appears. Your KB is `LAB_PREFIX` plus `-kb`.

**If not:** for `AuthorizationFailed` or `roleAssignments/write`, stop before 2-2. The access administrator **assigns and confirms the Search identity's planner access** using the `prepare-iq` row in [role-assignment recovery](docs/instructor.en.md#role-recovery). Then the runner repeats only this command in the same account and folder; do not switch the runner's login to the administrator. For other errors, see [common symptoms](docs/troubleshooting.en.md#symptoms).

<a id="policy-retrieval"></a>

### 2-2. Test retrieval

**Terminal A:**

```bash
python scripts/workshop.py retrieve --query "What is the lodging limit for a domestic business trip in September 2026?"
```

**Checkpoint:** `knowledge_base` is your KB, `document_ids` includes **`TRAVEL-2026`**, and `activity` is not empty. Archived policies may also appear.

**If not:** [recover retrieval](docs/troubleshooting.en.md#retrieval).

### 2-3. Check the KB in the portal

**Portal:** open [Microsoft Foundry](https://ai.azure.com/) in a browser and sign in with the same account; every portal step uses the English menus.

1. Turn on the **New Foundry** switch at the top right.
2. Select the project name at the top left and choose `AZURE_AI_PROJECT_NAME` from `.env` (resource `AZURE_AI_ACCOUNT_NAME`).
3. Open **Build** at the top → **Knowledge** on the left → **Knowledge bases** → your KB (`LAB_PREFIX` plus `-kb`).

**Checkpoint:** under **Knowledge sources** near the bottom, the source (`LAB_PREFIX` plus `-source`) is **Active**, and **Retrieval instructions** are filled in.

**If not:** see [portal differences](docs/troubleshooting.en.md#portal-differs).

**Example screen:** the KB, its retrieval instructions, and its source (your names differ).

![English Foundry IQ knowledge base and retrieval instructions](docs/assets/live-en-20260923b/screenshots/02-knowledge.webp)

**Next:** [3. Run the agent locally](#local)

<a id="local"></a>
<a id="3-run-the-agent-locally--lab-b"></a>

## 3. Run the agent locally

**Goal:** a real English V1 answer from the agent running on your machine.

**Why two terminals?** A keeps the **server**, a program waiting for requests, running while B sends it a question. `127.0.0.1:8088` means port 8088 on your own PC. Only the program runs locally: retrieval and models still call Azure, requiring internet access and incurring costs.

### 3-1. Start the server

**Terminal A — copy the path:** print this folder's path and copy it; you paste it into Terminal B in 3-2:

```bash
pwd
```

**Checkpoint:** you copied the workshop folder's path, starting with `/`.

**If not:** if it differs from the folder noted in step 1, [restore the terminal](#resume-shell), then check again.

**Terminal A — start the server:** select V1 and start it; leave it running until 3-3. The deployment that `Selected v1; run azd deploy ...` mentions happens in step 4, and the first start takes about 30 seconds to install dependencies.

```bash
python scripts/workshop.py set-prompt v1 &&
azd ai agent run --no-client
```

**Checkpoint:** after `Starting agent on http://localhost:8088`, log lines continue until `Running on http://0.0.0.0:8088` appears without a traceback; the prompt does not return.

**If not:** see the port 8088 row in [common symptoms](docs/troubleshooting.en.md#symptoms).

### 3-2. Send a request from Terminal B

**Terminal B — start Bash:** keep Terminal A running, open a second terminal window (or tab), and run this; it is fine if it already runs Bash:

```bash
bash
```

**Checkpoint:** Terminal B has a new input prompt, while Terminal A's server keeps running.

**If not:** if you stopped A's server, restart it at 3-1. Do not paste the server-start command into B.

**Terminal B — send a request:** when prompted, paste the absolute path from 3-1 and press Enter. The block quotes the path for you, restores the environment, checks readiness, and sends one request:

```bash
read -r -p "Absolute workshop path printed by Terminal A: " WORKSHOP_DIR &&
cd "$WORKSHOP_DIR" &&
source src/agent/.venv/bin/activate &&
export AZURE_CONFIG_DIR="$PWD/.azure-cli" &&
curl --fail --show-error --write-out '\nHTTP %{http_code}\n' http://127.0.0.1:8088/readiness &&
python scripts/workshop.py smoke --local
```

**Checkpoint:** **`HTTP 200`**, then JSON with a nonempty English `answer`, `model_key: sol`, `language: en`, and `prompt_version: v1`.

**If not:** confirm that Terminal A is still running, then see [common symptoms](docs/troubleshooting.en.md#symptoms).

**Read your first answer this way.** JSON presents results as `field name: value`. `HTTP 200` means the readiness request succeeded, not that the travel-policy answer is correct.

| Result field | Plain meaning |
|---|---|
| `answer` | The answer text a user reads |
| `decision` | A decision such as allowed or approval required. `allowed` means permitted by policy, not that approval was executed |
| `citations` | Document IDs the model **cited as support** for its answer |
| `source_ids` | Document IDs **actually returned by retrieval** |

The two ID lists serve different purposes. V1 can cite a title instead of a document ID while the request itself still succeeds. Check execution now; review such quality issues in steps 5–6.

<details>
<summary>Example screen: a real local response</summary>

![Real local English response](docs/assets/live-en-20260923b/screenshots/03-local.webp)

</details>

### 3-3. Stop the server

**Terminal A:** press **`Ctrl+C`**. Then close Terminal B.

**Checkpoint:** Terminal A shows its prompt again. All later commands run in Terminal A.

**If not:** press `Ctrl+C` once more and wait.

**Next:** [4. Deploy the Hosted Agent](#deploy)

<a id="deploy"></a>
<a id="4-deploy-the-hosted-agent--lab-b"></a>

## 4. Deploy the Hosted Agent

**Goal:** the same code answering from Azure as a numbered agent version. Local Docker is not required.

**What is deployment?** It puts the program that ran on your PC in step 3 into Azure's managed runtime. It does not train a new model. **`v1` names the instructions**, while `agent_version` is **a number created by deployment**; they need not match.

<a id="deploy-code"></a>

### 4-1. Deploy the code

**Terminal A:** this usually takes 1–3 minutes; status lines such as `Polling agent status (1/30)` are normal.

```bash
azd deploy --no-prompt
```

**Checkpoint:** `SUCCESS: Your application was deployed ...` appears and the prompt returns. Do not run the `Next:` suggestions or the `Update available` notice around it.

**If not:** keep the error output and follow [deployment failure and status checks](docs/troubleshooting.en.md#deployment-recovery). Do not redeploy or continue to 4-2 while success is uncertain.

<a id="agent-access"></a>

### 4-2. Grant the agent access

A service you can access after signing in is not automatically accessible to the agent running in Azure. The agent uses **its own service identity (managed identity)**, so it needs separate retrieval and model-call permissions.

**Terminal A:**

```bash
python scripts/workshop.py grant-agent-access
```

**Checkpoint:** `Search read and Foundry model inference access configured for <your agent>.`

**If not:** for a role-assignment permission error, identify the agent principal, roles, and scopes using the `grant-agent-access` row in [role-assignment recovery](docs/instructor.en.md#role-recovery). After the administrator completes the assignments in their own session, the runner repeats only this command in the same account and folder. Do not redeploy or add Owner permissions. For other errors, see [Hosted Agent symptoms](docs/troubleshooting.en.md#symptom-hosted).

<a id="hosted-smoke"></a>

### 4-3. Check the hosted response

**Terminal A:** send one request to the hosted agent, and note the printed `agent_version` as `V1 version: N`. The first call can take about 30 seconds.

```bash
python scripts/workshop.py smoke
```

**Checkpoint:** JSON with a nonempty English `answer`, `prompt_version: v1`, a `trace_id` (the ID of this request's execution record), and a **numeric `agent_version`**; it need not be `1`, and 7-2 must show a different one.

**If not:** for `424` or a timeout, the agent may still be starting; rerun only `smoke` after 1–2 minutes. For a permission error (`403`), check that 4-2 succeeded; role changes can take a few minutes, so retry after about 5 minutes. Do not redeploy ([Hosted Agent symptoms](docs/troubleshooting.en.md#symptom-hosted)).

<details>
<summary>Example screen: a real hosted response</summary>

![Real hosted English response](docs/assets/live-en-20260923b/screenshots/04-hosted.webp)

</details>

### 4-4. Find the version in the portal

**Portal:** open **Agents** on the left → your agent (`LAB_AGENT_NAME`) → the **Playground** tab, then pick 4-3's number in the **Version** selector at the top right.

**Checkpoint:** the **Version** selector at the top right shows the numeric `agent_version` from 4-3.

**If not:** first check that the selected version equals 4-3's `agent_version`; if it still differs, see [portal differences](docs/troubleshooting.en.md#portal-differs).

**Next:** [5. Evaluate the three-model baseline](#lab-c)

<a id="lab-c"></a>
<a id="5-evaluate-the-four-model-baseline--lab-c"></a>
<a id="5-evaluate-the-three-model-baseline"></a>

## 5. Evaluate the three-model baseline

**Goal:** collect and evaluate 18 V1 responses (6 dev questions × 3 models) as `baseline`.

<a id="evaluation-runs"></a>

**V1 and V2 are instruction (prompt) versions, not models; split means question set; label means result-folder name.** Use `dev` for improvement and open the new `holdout` questions only at the end, after fixing V2.

| Result name (label) | Instructions | Question set (split) | Responses | What to check |
|---|---|---|---|---|
| `baseline` | V1 | 6 `dev` questions | 18 | Answers before the change |
| `improved` | V2 | The same 6 `dev` questions | 18 | The before-and-after difference |
| `holdout` | Unchanged V2 | 4 new `holdout` questions | 12 | Whether V2 also works on new questions |

**Run only the first row, `baseline`, now.** Step 7 runs `improved` and step 8 runs `holdout`, giving **18 + 18 + 12 = 48 responses**. Setup calls and scores from the scoring model (judge) are not added to this count. `improved` is a name, not an improvement verdict; dev and holdout use different questions, so do not treat them as a before/after comparison.

The same agent (`LAB_AGENT_NAME`) routes each question to three candidate models, which each produce one answer: `model_key` values `sol`, `luna`, and `astra` select `gpt-6-sol`, `gpt-6-luna`, and `gpt-6-astra`. These keys are not agent names or Azure deployment names.

**Generating answers and scoring answers are separate commands.** The two kinds of checks do not replace each other.

| Command | What it does | What it checks |
|---|---|---|
| `collect` | Saves **18 new agent responses** and runs Python business checks | Whether decisions, amounts, and citations match the fixed rules |
| `evaluate` | Scores **the 18 saved responses** with the judge; generates no new agent answers | Whether answers match their evidence (`groundedness`) and address the question (`relevance`) |

The judge is **a separate model that reads and scores answers**. Each metric passes at **4 out of 5 or above**, independently of the Python business checks. `evaluate` also makes paid judge calls. See [evaluator inputs](#what-is-being-evaluated) for details.

**These three labels are the first-run defaults.** Later commands use the variables you set below, so recovery does not require editing each command. Read `baseline`, `improved`, and `holdout` in output and path descriptions as your [actual labels](docs/troubleshooting.en.md#run-values).

<a id="run-settings"></a>

**Terminal A — set result names only on the first run:** copy these four values into your existing notes. **When resuming or recovering, do not overwrite them with these defaults; [restore the run values](docs/troubleshooting.en.md#run-values)** instead.

```bash
BASELINE_LABEL=baseline
CANDIDATE_LABEL=improved
HOLDOUT_LABEL=holdout
COLLECTION_CONCURRENCY=4
printf 'V1 dev=%s\nV2 dev=%s\nV2 holdout=%s\nconcurrency=%s\n' \
  "$BASELINE_LABEL" "$CANDIDATE_LABEL" "$HOLDOUT_LABEL" "$COLLECTION_CONCURRENCY"
```

**Checkpoint:** the output shows `baseline`, `improved`, `holdout`, and `4` on separate lines, and you recorded them in the same notes. Variables last only in this terminal; do not add them to `.env`.

**If not:** in a new terminal or with existing collected results, [restore the run values](docs/troubleshooting.en.md#run-values). Do not rename existing results.

### 5-1. Check the judge

**Terminal A:** use two examples to check that the scoring model (the judge) distinguishes a grounded answer from a wrong one. This is calibration, separate from the 48 evaluated agent responses. You may wait about a minute with no output.

```bash
python scripts/workshop.py calibrate
```

**Checkpoint:** after the evaluation-completed line and a URL, the last line is `Judge calibration passed; ...`.

**If not:** [resolve calibration first](docs/troubleshooting.en.md#calibration).

<a id="baseline-collection"></a>

### 5-2. Collect the 18 baseline responses

**Terminal A:** `--split dev` selects the six questions; `--label "$BASELINE_LABEL"` uses the result-folder name set above. A long readiness JSON appears first, then lines such as `01/18 ...` add up one by one (usually 1–3 minutes).

```bash
python scripts/workshop.py collect --split dev --label "$BASELINE_LABEL" --concurrency "$COLLECTION_CONCURRENCY"
```

**Checkpoint:** the progress reaches `18/18` without errors and ends with a `Session ... retained ...` line. `business=False` marks a result to review, not a command failure.

**If not:** [recover collection](docs/troubleshooting.en.md#collection-retry).

<a id="baseline-evaluation"></a>

### 5-3. Evaluate the saved responses

**Terminal A:** the variable below reuses your [actual V1 label](docs/troubleshooting.en.md#run-values), including any update made during collection recovery. There may be no output for 1–3 minutes while Foundry scores the answers.

```bash
python scripts/workshop.py evaluate --label "$BASELINE_LABEL"
```

**Checkpoint:** `Foundry evaluation completed: ... (18 rows)`, followed by a report URL. Low scores are valid results.

**If not:** [recover evaluation](docs/troubleshooting.en.md#evaluation-retry); do not repeat the collection.

<a id="baseline-report"></a>

### 5-4. Open the evaluation report

**Portal:** copy the report URL that `evaluate` printed and open it in the browser.

**Checkpoint:** **Status** is **Completed**, and under **Overall metric results** the groundedness and relevance counts are out of **18** (for example, `18 / 18` or `15 / 18`). The table below shows 10 rows per page; use **Next** to see the rest.

**If not:** find the run in the project-wide **Evaluations** list, not the agent's Evaluation tab; see [portal differences](docs/troubleshooting.en.md#portal-differs).

<details>
<summary>Example screen: the baseline evaluation report (your names differ)</summary>

![Actual English baseline evaluation](docs/assets/live-en-20260923b/screenshots/05-baseline.webp)

</details>

<a id="what-is-being-evaluated"></a>

<details>
<summary>Reference: question sets and evaluator inputs</summary>

- The six dev cases cover current limits, prior approval, historical policy, uncovered questions, prohibited expenses, and requests to ignore policy.
- Keep the question sets and result names from [this step's evaluation plan](#evaluation-runs).
- The judge, `gpt-5.4-mini`, is not a candidate, and its two calibration examples are not among the 48 responses.
- `compare` and `summary` only read saved results; they make no model calls.
- Foundry's groundedness and relevance evaluators see the answer text, not the `decision` or `citations` fields, so **a high groundedness score does not establish a correct decision or citation IDs** ([what each evaluator receives](docs/validation.en.md#business-checks)).
- Step 9's gates use the business checks; Foundry scores are a separate quality signal.

</details>

**Next:** [6. Review a real case and preserve its source](#lab-d)

<a id="lab-d"></a>
<a id="6-review-a-real-case-and-preserve-its-source--lab-d"></a>

## 6. Review a real case and preserve its source

**Goal:** explain one real response with its fixed reference and its **trace** (the record of that request's retrieval and model calls), then save it as a **regression case** that V2's collection reuses.

**What is a regression case?** A question to check again after the next change. It links the existing fixed answer to your review reason and the original trace. It does not turn a wrong response into a new correct answer or retrain the model.

### 6-1. Aggregate the results and find a row to review

**Terminal A — aggregate the results** into `comparison.json`, which `summary` reads:

```bash
python scripts/workshop.py compare --labels "$BASELINE_LABEL"
```

**Checkpoint:** a long comparison JSON prints without errors and ends with `comparison_notes`; inside it, `baseline → models` has `sol`, `luna`, and `astra`.

**If not:** confirm step 5's collection and evaluation completed, then [recover only the failed command](docs/troubleshooting.en.md#resume).

<a id="baseline-traces"></a>

**Terminal A — check the traces:** if you already saved this label's `telemetry.json` before a pause and it matches the checkpoint below, use that file and skip this command. Otherwise a long KQL query prints first, then a result JSON below it.

```bash
python scripts/workshop.py monitor --label "$BASELINE_LABEL"
```

**Checkpoint:** the command finishes without errors, and the result JSON shows `complete: true`, `expected_trace_count: 18`, and `observed_trace_count: 18`.

**If not:** `Telemetry is incomplete` may mean the traces are still arriving. Rerun only this command after 2–3 minutes; if it persists, [recover monitoring](docs/troubleshooting.en.md#telemetry). Do not repeat the collection.

**Terminal A — find a row to review:**

```bash
python scripts/workshop.py summary --labels "$BASELINE_LABEL"
```

**Checkpoint:** a model summary table and a `baseline business-check failures:` line appear; the line holds a comma-separated list of row IDs or `none`. The summary reads saved results; it does not evaluate again.

**If not:** check the file or label named in the error and repeat only `summary`.

<a id="review-case"></a>

### 6-2. Choose and explain one case

**Practice reading an ID:** `baseline-luna-D01` is a response name (`row_id`) made from **result set `baseline` + model `luna` + question `D01`**. Another model or a V2 answer to the same question produces a different row. `trace_id` is a separate ID for finding that row's execution record. Below, use an ID **actually present in your own output**.

**Choose:** copy the **first `row_id`** after `business-check failures:` in 6-1 (for example, `baseline-luna-D01`), up to the parenthesis; the parentheses name its failed checks. If it says `none`, choose **your actual V1 label's `-sol-D01` row**, shown in the input prompt below, and review why it passed.

**Terminal A — show one row:** paste the `row_id` you copied. The command shows the saved response beside the fixed reference; it changes no files and calls no model.

```bash
read -r -p "row_id to review (if none: ${BASELINE_LABEL}-sol-D01): " ROW_ID &&
python scripts/workshop.py show --label "$BASELINE_LABEL" --row-id "$ROW_ID"
```

**Checkpoint:** the JSON has `case_id`, `trace_id`, `saved_response` (the saved answer), `business_checks` (the five business checks), and `fixed_reference` (the fixed answer from `data/en/dev.jsonl`). Note the `row_id` and `trace_id`.

**If not:** for `Unknown row ID`, copy only the ID from the same V1 label's output, without parentheses or commas. If the variable differs from your notes, [restore the run values](docs/troubleshooting.en.md#run-values) first.

**First read the question (`query`) in Terminal A.** Compare `saved_response` → `answer` with `fixed_reference` → `ground_truth`, then use this table to explain each `false` in `business_checks`. `saved_response` is the agent's answer; `fixed_reference` is the reference set in advance.

| Check in `business_checks` | Values to compare in the same output |
|---|---|
| `decision` | `saved_response` → `decision` must equal `fixed_reference` → `expected_decision` ([decision meanings](docs/reference.en.md#decision-values)) |
| `required_numbers` | `saved_response` → `answer` must include every amount in `fixed_reference` → `required_numbers` |
| `citations_retrieved` | Every ID in `saved_response` → `citations` must appear in `saved_response` → `source_ids` |
| `citations_relevant` | Every cited ID must also appear in `fixed_reference` → `allowed_citations` |
| `citation_present` | If `fixed_reference` → `citation_required` is `true`, `citations` must not be empty. If it is `false`, `[]` is allowed |

Finding a document (`source_ids`) is not the same as citing it (`citations`). An empty citation list can pass the two “every ID” checks but fail `citation_present`. If all five checks are `true`, explain why the case passed. You do not need to interpret every JSON field.

**Next, inspect the same request in the portal.** `row_id` names the response; `trace_id` identifies the execution record you search for in the portal.

1. Open **Agents** on the left → your agent → **Traces → Trace view**. Paste the full `trace_id` into the search box above the table on the left, then click the matching row's **Trace ID** link. If it is missing, widen **Date range → 7D**.
2. In the opened window's **Graph view**, open the `foundry_iq.retrieve` (retrieval) box and the box starting with `chat` (model call), and check their **names and execution statuses**. Each box is a **span**, the record of one operation. Add `Retrieval span=name/status; Model span=name/status` to your notes. You do not need to interpret all the internal JSON. **Success** establishes execution, not answer quality or a cause; base your explanation on the evidence you compared with `show`.

**Then record one line:** `row_id=...; trace_id=...; Observation: ...; Evidence: ...; Change: ...`. In `Observation`, say what was right or wrong; in `Evidence`, name the fields or document IDs you compared; in `Change`, state the instruction needed. For a passing case, write the **behavior V2 should preserve** ([passing cases](docs/troubleshooting.en.md#no-failures), [cause-analysis example](#how-to-distinguish-retrieval-and-instruction-problems)).

**Checkpoint:** the `ID:` at the top of the portal window equals your `trace_id`, and your notes include both span names/statuses and `row_id=...; trace_id=...; Observation: ...; Evidence: ...; Change (or behavior to preserve): ...`.

**If not:** for a missing trace, widen the time range and search by the full `trace_id` again ([portal differences](docs/troubleshooting.en.md#portal-differs)). If a required span is missing, do not record the check as complete; use [trace recovery](docs/troubleshooting.en.md#telemetry). Edit no files.

**Example screen:** **Graph view** with the `foundry_iq.retrieve` and `chat` spans (your IDs and names differ).

![Real English trace review](docs/assets/live-en-20260923b/screenshots/06-trace.webp)

<details>
<summary>Reference: source files and the five business checks</summary>

- `show` reads `src/agent/.foundry/results/baseline/responses.jsonl` (saved responses) and `data/en/dev.jsonl` (fixed references). A `.jsonl` file holds one JSON object per line.
- The `false` checks come from the [five business checks](docs/validation.en.md#business-checks): correct `decision` ([labels](docs/reference.en.md#decision-values)), every required amount, every citation retrieved, every citation allowed, and a citation when required.

</details>

<a id="save-review"></a>

### 6-3. Save your review

**Saved reviews cannot be overwritten.** Check the preview first, then run the separate save block.

**Terminal A — enter and preview, without saving yet:** at the first prompt, enter your reviewed `row_id`; at the second, paste your one-line review from 6-2 (at least 10 characters, not an example):

```bash
read -r -p "Reviewed row_id: " ROW_ID &&
read -r -p "Observation, evidence, and what to change or preserve (at least 10 characters): " REVIEW_REASON &&
printf 'label=%s\nrow_id=%s\nreason=%s\n' "$BASELINE_LABEL" "$ROW_ID" "$REVIEW_REASON"
```

**Checkpoint:** the printed label, row ID, and reason match the actual review in your 6-2 notes.

**If not:** repeat only the input block above. Do not save below yet.

**Terminal A — save the reviewed input:** use the same terminal in which you checked the preview. If it was closed, restore the run values and repeat the preview first.

```bash
python scripts/workshop.py feedback --label "$BASELINE_LABEL" --row-id "$ROW_ID" \
  --reason "$REVIEW_REASON" --reviewer human
```

**Checkpoint:** `Reviewed trace-to-dataset record saved:` followed by the actual path `src/agent/.foundry/datasets/regression-<your row_id>.jsonl`.

**If not:** for `already exists`, a review for this row already exists; check it as in the `feedback` row of [resume](docs/troubleshooting.en.md#resume) and never overwrite it.

<a id="read-review"></a>

**Terminal A — verify the saved review:** in the same terminal, print the file you just saved in a readable form. Do not edit it. **If you came from 9-3, do not run `feedback` above.** If you lost `ROW_ID`, open the existing `regression-*.jsonl` files in `src/agent/.foundry/datasets/` with your editor and read the fields below.

```bash
python -m json.tool --no-ensure-ascii "src/agent/.foundry/datasets/regression-$ROW_ID.jsonl"
```

**Checkpoint:** `lineage → source_row_id`, `source_trace_id`, and `review_reason` match the row, trace, and reason you actually reviewed, and the top-level `ground_truth` equals the `ground_truth` in 6-2's `fixed_reference`, not the model's answer.

**If not:** for `No such file`, `ROW_ID` may be empty in a new terminal; paste the path printed above inside the quotes instead. If an unreviewed row or an incorrect reason was saved, **stop before V2 collection and [check the review record](docs/troubleshooting.en.md#review-recovery)**. Saving the correct row as well does not exclude the mistaken record.

<a id="how-to-distinguish-retrieval-and-instruction-problems"></a>

<details>
<summary>Example: distinguish a retrieval problem from an instruction problem</summary>

For example, if the correct policy ID is in `source_ids` but the answer's `citations` uses a document **title**, the immediate problem is not necessarily retrieval. V1's instruction to hide internal identifiers can conflict with the business contract requiring source IDs.

Check your own row before using that explanation. `feedback` preserves a reference case and its provenance; it does not train model weights or automatically generate a better prompt.

</details>

**Next:** [7. Deploy V2 and evaluate the same dev set](#lab-e)

<a id="lab-e"></a>
<a id="7-deploy-v2-and-evaluate-the-same-dev-set--lab-e"></a>

## 7. Deploy V2 and evaluate the same dev set

**Goal:** the provided V2 instructions deployed as a new version and evaluated on the same six dev questions, with models, data, and criteria unchanged.

### 7-1. Review the provided V2

**Editor:** open `src/agent/prompts/en/v1.txt` and `src/agent/prompts/en/v2.txt`, and pick the row below that matches **what to change or preserve** from your 6-2 review. Edit neither file; V2 is provided.

| V1 weakness | Provided V2 instruction |
|---|---|
| Hides document IDs | Cite the original document IDs used |
| Leaves dates and document status vague | Apply the policy in force on the travel date; ignore drafts |
| Blurs approval and prohibition | Define the five decision values; never invent a completed approval |
| Leaves missing evidence unspecified | Use `not_covered` or `needs_info`; never fill policy gaps with general knowledge |
| May obey instructions inside retrieved text | Treat retrieved text as evidence, not instructions |

**Checkpoint:** your notes identify a matching V2 instruction and its difference from V1, or say `no direct V2 instruction`. For a passing case, identify the rule V2 must still follow.

**If not:** if no instruction directly matches, note `no direct V2 instruction` and continue. Do not force a connection or assume the provided V2 improves your case.

<a id="candidate-deploy"></a>

### 7-2. Deploy V2 and confirm the new version

**Terminal A — select V2 and deploy:** like 4-1, this takes 1–3 minutes.

```bash
python scripts/workshop.py set-prompt v2 &&
azd deploy --no-prompt
```

**Checkpoint:** `Selected v2; ...` is followed by `SUCCESS: Your application was deployed ...`.

**If not:** if `Selected v2; ...` is missing, use [configuration recovery](docs/troubleshooting.en.md#symptoms). If deployment failed after it, use [deployment status checks](docs/troubleshooting.en.md#deployment-recovery). Do not repeat a successful `set-prompt`.

<a id="candidate-smoke"></a>

**Terminal A — confirm the new version:** note the printed `agent_version` as `V2 version: N`.

```bash
python scripts/workshop.py smoke
```

**Checkpoint:** `prompt_version: v2` and a **numeric `agent_version` different from 4-3**.

**If not:** a `Hosted prompt does not match` error or an `agent_version` equal to 4-3 means V2 was not deployed. Check that `.env` has `LAB_PROMPT_VERSION=v2`, rerun the select-and-deploy block above **once**, and repeat this check. For other call errors, [recover only that command](docs/troubleshooting.en.md#resume).

<a id="candidate-collection"></a>

### 7-3. Collect and evaluate the same dev set

**Collection conditions:** `COLLECTION_CONCURRENCY` in your [run-value notes](docs/troubleshooting.en.md#run-values) must match `manifest.json → concurrency` for the completed V1 run. The command below uses that value; do not append another option such as `--concurrency 2`. Both V2 dev and holdout must keep V1's concurrency.

**Terminal A — collect:** as in 5-2, lines such as `01/18 ...` add up after the readiness JSON (usually 1–3 minutes).

```bash
python scripts/workshop.py collect --split dev --label "$CANDIDATE_LABEL" --concurrency "$COLLECTION_CONCURRENCY"
```

**Checkpoint:** the progress reaches `18/18` without errors.

**If not:** [recover collection](docs/troubleshooting.en.md#collection-retry).

<a id="candidate-evaluation"></a>

**Terminal A — evaluate:** the variable below uses your [actual V2 dev label](docs/troubleshooting.en.md#run-values). As in 5-3, there may be no output for 1–3 minutes.

```bash
python scripts/workshop.py evaluate --label "$CANDIDATE_LABEL"
```

**Checkpoint:** `Foundry evaluation completed: ... (18 rows)`, followed by a report URL.

**If not:** [recover evaluation](docs/troubleshooting.en.md#evaluation-retry).

<a id="candidate-comparison"></a>

**Terminal A — save the comparison:** after recovery, match both labels to your [run-value notes](docs/troubleshooting.en.md#run-values). Keep using those values in later `summary` and `show` commands.

```bash
python scripts/workshop.py compare --labels "$BASELINE_LABEL" "$CANDIDATE_LABEL"
```

**Checkpoint:** a long comparison JSON prints without errors, with `baseline` and `improved` inside it and `comparison_notes` at the end.

**If not:** check the label named in the error and step 7-3's evaluation completion, then [recover only the failed command](docs/troubleshooting.en.md#resume).

<a id="compare-results"></a>

### 7-4. Read your before-and-after comparison

**Terminal A:** print a read-only summary of the saved results. Keep what it shows; never lower the criteria, swap models, or adopt V2 automatically.

```bash
python scripts/workshop.py summary --labels "$BASELINE_LABEL" "$CANDIDATE_LABEL"
```

**Checkpoint:** the output shows these three parts in order; copy them into your notes:

1. `Reviewed case ...` with `source trace carried: yes` (provenance, not improvement) and the case's V2 `business passed` or `business failed (...)`;
2. the `sol` / `luna` / `astra` V1 `->` V2 table ([columns](#metric-fields)); mark any V2 token or latency increase for the 9-3 limitations line;
3. `improved business-check failures:` and `improved Foundry-score failures:`, each with row IDs or `none`.

**If not:** for a missing file or label, confirm 7-3's evaluation finished, then rerun only `compare` and `summary`. If the `Reviewed case` line is missing or says `source trace carried: no`, V2's collection did not read your 6-3 review (usually because 7-3 ran before 6-3). Do 6-3 first if you have not, then use [V2 dev collection recovery](docs/troubleshooting.en.md#collection-retry-improved) to collect `improved-retry` and use it instead of `improved` from then on. Do not delete earlier results.

<a id="metric-fields"></a>

**Reading order:** the left side of `->` is V1; the right side is V2. Read **business passes**, then **judge passes**, then **any increase in tokens or time**. One better column does not establish an overall improvement.

| Column | How to read it |
|---|---|
| `business` | Responses passing **all five** business checks / total. `5/6` means five of six passed |
| `required citations` | Citation-required responses with valid citations / responses requiring a citation |
| `groundedness`, `relevance` | Responses scoring **at least 4 out of 5** / total responses for evidence grounding and question relevance, respectively. `5/6` is a pass count, not a score |
| `tokens in/out` | How much text the model read / produced, measured in tokens. Totals for that model's **six dev responses**, not an Azure bill |
| `p50/p95 s` | Retrieval plus model processing time, in **seconds**. Of six responses ordered fastest to slowest, p50 is the third and p95 is the last. Lower is faster |

<a id="comparison-reading-example"></a>

**Reading exercise — these are illustrative numbers, not measured results.** Suppose one model's table contains the values below. They are neither commands to run nor target scores to reproduce.

```text
business       3/6 -> 5/6
groundedness   6/6 -> 6/6
relevance      6/6 -> 5/6
p50/p95 s      1.20/2.00 -> 1.40/2.30
```

Here, **two more answers pass the business checks, but one fewer passes relevance and p95 rises from 2.00 to 2.30 seconds**. Read this as “business checks improved, but relevance and latency need review,” not “better in every way.” These selected columns alone do not establish a quality-gate pass or production approval.

**Interpretation to note:** use your values to write `Business passes increased/stayed the same/decreased; judge failures were ...; tokens and time were ...`. Preserve unchanged or worse results too.

**Terminal A — inspect your reviewed case's saved V2 answer:** in the `Reviewed case ...` line above, copy the V2 row ID **after `->` and before `:`**. Use the line whose V1 row matches your 6-3 review, not a new Playground response.

```bash
read -r -p "V2 row_id from the Reviewed case line: " V2_ROW_ID &&
python scripts/workshop.py show --label "$CANDIDATE_LABEL" --row-id "$V2_ROW_ID"
```

**Checkpoint:** `case_id` and `model_key` match your 6-2 case, while `trace_id` is different: this is a new response, not the original trace copied as V2 evidence. Compare `saved_response` → `answer`, `decision`, and `citations` with 6-2 and the unchanged `fixed_reference`. Note the V2 `row_id` and what actually changed (or stayed the same), even if its business pass/fail did not change.

**If not:** for `Unknown row ID`, copy only the right-hand ID, without `:` or the following text; use your actual recovery label if applicable. If you lost the V1 view, reopen [6-2's saved row](#review-case); do not collect or evaluate again.

<details>
<summary>Reference: source files and comparison limits</summary>

The summary reads `src/agent/.foundry/results/comparison.json` (`labels → baseline / improved → models`) and each label's `evaluation-results.json`. See [reading results](docs/validation.en.md#read-your-results) for the aggregate fields.

Tokens exclude the planner, judge, and other calls; timing six responses does not establish production performance ([measurement scope](docs/validation.en.md#tradeoffs)). Retrieval can also differ between runs (`comparison_notes`), so this compares **the whole agent, including retrieval**, not models in isolation.

Follow the link for the failure type: [business-check failures](docs/validation.en.md#business-failures) or [Foundry-score failures](docs/validation.en.md#native-failures). For a recorded example, not your target, see the [September 23, 2026 English results](docs/validation.en.md#measured-results).

</details>

<a id="portal-comparison"></a>

<details>
<summary>Optional, only if time remains after 7-4: compare V1 and V2 in the portal (extra calls and cost, not part of the 48)</summary>

Open **your agent → Playground → Version dropdown → Compare versions**. Select your V1 version on the left and V2 on the right; the portal may initially select the same version twice. Paste this same dev question into either input:

```json
{
  "query": "For a business trip to Busan on 2026-09-10, is lodging at KRW 170000 per night allowed by policy? Please also state the limit.",
  "model_key": "sol",
  "case_id": "D01",
  "run_id": "portal-en-comparison"
}
```

Click **Send once**: the comparison view sends the question to both versions. Check each response's `language`, `prompt_version`, `citations`, and distinct `trace_id`. These are extra demo calls, not replacements for the 18 + 18 collected responses.

**The screenshot is a recorded example:** both answers allowed the lodging, but V1 cited a title while V2 cited the original `TRAVEL-2026` ID. Your decisions and citations may differ. Read the actual differences; do not call again to match the example.

![Real English V1 and V2 comparison](docs/assets/live-en-20260923b/screenshots/07-comparison.webp)

</details>

**Next:** [8. Keep V2 unchanged and evaluate holdout](#lab-f)

<a id="lab-f"></a>
<a id="8-freeze-the-candidate-and-evaluate-holdout--lab-f"></a>

## 8. Keep V2 unchanged and evaluate holdout

**Goal:** 12 responses (4 held-out questions × 3 models) from the unchanged V2.

**Why keep new questions aside?** Think of dev as practice questions whose answers you can inspect while improving, and holdout as questions attempted for the first time at the end. Better dev results do not guarantee better answers elsewhere. **If you change V2 after seeing these answers, the same questions can no longer count as untouched validation.**

### 8-1. Collect the holdout responses

**Warning:** keep V2 frozen by changing nothing after 7-2; there is no `freeze` command. If you did any of the following after 7-2 and **have not yet completed recovery for that change**, follow [recovery when V2 changed](docs/troubleshooting.en.md#v2-changed) before collecting:

- ran `set-prompt` or `azd deploy`; or
- edited `.env` or a prompt file.

**After recovery:** if you **confirmed the original V2 version, or collected and evaluated dev with the new V2 and completed 7-4**, do not repeat recovery unless you changed something afterward. When using a new version, make it your noted V2 reference. If holdout records already exist, use the recovery guide's retry label; always compare versions and hashes in 8-2.

<a id="holdout-collection"></a>

**Collection conditions:** `COLLECTION_CONCURRENCY` in your [run-value notes](docs/troubleshooting.en.md#run-values) must match `manifest.json → concurrency` for the completed V1 run. The command below uses that value; do not append another option such as `--concurrency 2`. Keep `--split holdout` unchanged.

**Terminal A:** lines such as `01/12 ...` add up after the readiness JSON (usually 1–3 minutes).

```bash
python scripts/workshop.py collect --split holdout --label "$HOLDOUT_LABEL" --concurrency "$COLLECTION_CONCURRENCY"
```

**Checkpoint:** the progress reaches `12/12` without errors.

**If not:** for `Hosted prompt does not match`, follow [recovery when V2 changed](docs/troubleshooting.en.md#v2-changed); for other errors, [recover collection](docs/troubleshooting.en.md#collection-retry).

<a id="holdout-evaluation"></a>

### 8-2. Evaluate the holdout and confirm V2 stayed frozen

**Terminal A — evaluate:** the variable below uses your [actual holdout label](docs/troubleshooting.en.md#run-values). There may be no output for 1–3 minutes.

```bash
python scripts/workshop.py evaluate --label "$HOLDOUT_LABEL"
```

**Checkpoint:** `Foundry evaluation completed: ... (12 rows)`, followed by a report URL.

**If not:** [recover evaluation](docs/troubleshooting.en.md#evaluation-retry).

<a id="holdout-comparison"></a>

**Terminal A — save the comparison:** after recovery, match all three labels to your [run-value notes](docs/troubleshooting.en.md#run-values). Read `baseline`, `improved`, and `holdout` in later output descriptions as those actual labels.

```bash
python scripts/workshop.py compare --labels "$BASELINE_LABEL" "$CANDIDATE_LABEL" "$HOLDOUT_LABEL"
```

**Checkpoint:** a long comparison JSON prints without errors and ends with `comparison_notes`.

**If not:** check the label named in the error and the evaluation above, then [recover only the failed command](docs/troubleshooting.en.md#resume).

**Terminal A — check that V2 stayed frozen:** print one line per label with only its agent version and instruction hash (a content fingerprint, first 12 characters) from the comparison file you just saved.

```bash
python -c 'import json; labels = json.load(open("src/agent/.foundry/results/comparison.json"))["labels"]; [print(name, "agent_version=" + str(item["agent_version"]), "prompt_hash=" + item["prompt_hash"][:12]) for name, item in labels.items()]'
```

**Checkpoint:** the `improved` and `holdout` lines have the same `agent_version` and `prompt_hash`, and that `agent_version` is the **V2 version** you noted. The `baseline` line differs because it is V1.

**If not:** different values mean **the comparison conditions changed**. Do not reevaluate or edit files to make them match; follow [recovery when V2 changed](docs/troubleshooting.en.md#v2-changed).

<a id="holdout-results"></a>

### 8-3. Read the holdout results

**Terminal A:** after 8-2 confirms V2 stayed frozen, print a read-only summary of the saved holdout (no model calls). Holdout uses different questions from dev, so its pass rates are not a V1 → V2 improvement claim.

```bash
python scripts/workshop.py summary --labels "$HOLDOUT_LABEL"
```

**Checkpoint:** the `sol` / `luna` / `astra` table shows `business`, `groundedness`, and `relevance` as **`.../4`**, followed by these two lists with row IDs or `none`; copy both lists into your notes separately (a `4/4` business result can still have Foundry failures):

- `holdout business-check failures:`
- `holdout Foundry-score failures:`

**If not:** for a missing comparison file or label, resume at 8-2's `compare` block. For `n/a` evaluator results or a missing Foundry failure list, [recover evaluation](docs/troubleshooting.en.md#evaluation-retry). Inspect failed rows separately for [business checks](docs/validation.en.md#business-failures) and [Foundry scores](docs/validation.en.md#native-failures).

<a id="holdout-report"></a>

### 8-4. Open the holdout report

**Portal:** open the report URL printed by the holdout `evaluate`, not the dev report.

**Checkpoint:** **Status** is **Completed**, and the **Overall metric results** counts are out of **12** (for example, `12 / 12`).

**If not:** see [portal differences](docs/troubleshooting.en.md#portal-differs).

**Warning:** do not tune the prompt on these results and then resubmit the same cases as untouched validation; these four educational cases are not an independent benchmark.

<details>
<summary>Example screen: the holdout evaluation report (your names differ)</summary>

![Actual English holdout evaluation](docs/assets/live-en-20260923b/screenshots/08-holdout.webp)

</details>

**Next:** [9. Check operational signals and complete evidence](#lab-g)

<a id="lab-g"></a>
<a id="9-check-operational-signals-and-complete-evidence--lab-g"></a>

## 9. Check operational signals and complete evidence

**Goal:** verify the evidence, inspect the operational dashboard, then write the final report. Gather all the values before assembling the report once.

**Evaluation, tracing, and monitoring answer different questions.**

| View | Question it answers | Where you use it |
|---|---|---|
| Evaluation | “Does this answer meet the criteria?” | Scores and business checks in steps 5, 7, and 8 |
| Trace | “Which retrieval and model calls did this request make?” | One request in step 6, and all traces in 9-1 |
| Monitor | “What are the overall run counts, tokens, and statuses?” | The dashboard in 9-2 below |

For example, a `completed` run can still contain an incorrect policy answer. See the official [Foundry evaluation, tracing, and monitoring explanation](https://learn.microsoft.com/azure/foundry/concepts/observability) for this distinction.

### 9-1. Verify the complete response matrix

**If you checked traces before pausing:** skip a `monitor` command only when `src/agent/.foundry/results/<label>/telemetry.json` for that same actual label matches its checkpoint below. Still run unfinished queries for other labels. Do not overwrite completed trace evidence by querying a window that no longer includes the run.

<a id="candidate-traces"></a>

**Terminal A — V2 dev traces:** the variable below uses your [actual V2 dev label](docs/troubleshooting.en.md#run-values).

```bash
python scripts/workshop.py monitor --label "$CANDIDATE_LABEL"
```

**Checkpoint:** the command finishes without errors, and the result JSON shows `complete: true`, `expected_trace_count: 18`, and `observed_trace_count: 18`.

**If not:** `monitor` looks back two hours. If more than two hours passed since the V2 collection, [extend the window](docs/troubleshooting.en.md#telemetry); if you just collected, rerun only this command after 2–3 minutes.

<a id="holdout-traces"></a>

**Terminal A — holdout traces:** the variable below uses your [actual holdout label](docs/troubleshooting.en.md#run-values).

```bash
python scripts/workshop.py monitor --label "$HOLDOUT_LABEL"
```

**Checkpoint:** the command finishes without errors, and the result JSON shows `complete: true`, `expected_trace_count: 12`, and `observed_trace_count: 12`.

**If not:** for `Telemetry is incomplete`, rerun only this command after 2–3 minutes; if it persists, [recover monitoring](docs/troubleshooting.en.md#telemetry) with the same label.

**Terminal A — verify all evidence:** check the three label **variable values** against your [run-value notes](docs/troubleshooting.en.md#run-values). The command below also reuses recovered values; keep the `--baseline`, `--candidate`, and `--holdout` option names. A long comparison JSON prints first, then the verification JSON.

```bash
python scripts/workshop.py verify --baseline "$BASELINE_LABEL" --candidate "$CANDIDATE_LABEL" --holdout "$HOLDOUT_LABEL"
```

**Checkpoint:** the last JSON shows `language: en`, `component_execution_verified: true`, `primary_model_outputs: 48`, and `distinct_verified_traces: 48`.

**If not:** find the stage the error message names in [recover the failed stage](docs/troubleshooting.en.md#resume); never edit evidence.

<details>
<summary>Example screen: complete execution evidence</summary>

![English response, evaluation, and trace verification](docs/assets/live-en-20260923b/screenshots/09-verification.webp)

</details>

<a id="operational-dashboard"></a>
<a id="9-3-inspect-the-operational-dashboard"></a>

### 9-2. Inspect the operational dashboard

**Portal:** open **Agents** on the left → your agent → the **Monitor** tab → **Overview**, and keep the range at **Last Day**.

**Checkpoint:** the **Agent runs** and **Runs and token metrics** charts show values in your run's time window. Note each status count in the **Agent runs** legend (for example, `completed: 53`) and `Total tokens`. Preserve the names and counts of any other statuses, or write `no statuses other than completed`. Do not count runs still in progress as errors. Totals include smoke and portal calls, so they need not equal 48.

**If not:** refresh after 2–3 minutes. For a run from an earlier date, widen to **7D**; if it stays empty, see [portal differences](docs/troubleshooting.en.md#portal-differs).

`Estimated cost: $0` does not mean the run was free; you must still complete step 10 cleanup.

<details>
<summary>Example screen (open if your portal looks different): the Foundry monitoring dashboard</summary>

![Actual English Foundry monitoring dashboard](docs/assets/live-en-20260923b/screenshots/09-monitor.webp)

</details>

<a id="completion-decision"></a>
<a id="9-2-decide-what-to-report"></a>
<a id="9-2-report-your-results-in-three-points"></a>
<a id="finish"></a>
<a id="finish-report-three-points"></a>

### 9-3. Report your results in three points

**Terminal A:** print the evidence file saved in 9-1 again (this does not verify again). Copy each model's `dev` and `holdout` values from `candidate_quality_gates` into your notes: `dev=true` means at least **5 of 6** responses passed all business checks with every required citation valid; `holdout=true` means **all 4** passed.

```bash
python -m json.tool --no-ensure-ascii src/agent/.foundry/results/verified-evidence.json
```

**Checkpoint:** `candidate_quality_gates` contains six `dev` / `holdout` values for `sol`, `luna`, and `astra`. A `false` value is a valid result to record.

**If not:** if the file is missing, check that [9-1 verification](#lab-g) completed. Do not create the file or fill in values yourself.

**Separate the final decision into three parts.**

| Evidence-file value | Meaning | What to report |
|---|---|---|
| `component_execution_verified: true` | Required execution, evaluation, and trace links were verified | Execution evidence verified |
| Each model's `dev` / `holdout` under `candidate_quality_gates` | Whether the fixed business-quality criteria passed | Record the actual `true` / `false` values |
| `production_release_approved: false` | This training exercise does not approve a production release | Keep the value unchanged |

The first being true while some of the second are false is not a contradiction. It means **“the evaluation completed correctly and found remaining quality gaps.”**

**Editor — save your notes as the report:** organize **the same document** you have been using into this template (not a command). Use VS Code **File → Save As** to save it as `src/agent/.foundry/results/workshop-report.txt` inside your workshop folder. Leave no `...`, write empty lists as `none`, and keep `production_release_approved=false`:

The actual labels are the result-folder names you used. Read `concurrency` from their `manifest.json`. Record these values even without recovery, using `Recovery history: none`.

```text
1. Review (6-2 line): ...
   Linked V2 instruction (7-1): ...
2. Change (7-4):
   V1 version (4-3)=...; V2 version (7-2)=...
   Reviewed V2 row and actual answer/decision/citation change (or unchanged): ...
   V1 -> V2 table: paste the table here
   Interpretation (business passes, judge failures, tokens, time): ...
   improved failures: business=...; Foundry=...
3. Decision (gates from verified-evidence.json):
   Actual labels: V1 dev=...; V2 dev=...; V2 holdout=...
   Collection concurrency=...
   Recovery history (none if unused): ...
   Holdout usage (first use, or reuse and its reason): ...
   sol: dev=..., holdout=...
   luna: dev=..., holdout=...
   astra: dev=..., holdout=...
   holdout failures (8-3): business=...; Foundry=...
   Monitor (9-2): Agent runs counts by status=...; Total tokens=...
   limitations (token/latency increases, run statuses other than completed, etc.): ...
   production_release_approved=false
```

**Report as is:** `false` gates, Foundry-score failures, and regressions are valid results; passing gates is not production approval. If V2-change recovery reused holdout, state that this is **not fresh, untouched validation**. Matching versions and hashes do not prove first use.

**Checkpoint:** the saved report has no `...` left and includes the 7-4 table, actual labels, concurrency, recovery and holdout usage history, and unchanged `production_release_approved=false`. Do not rerun for better scores.

**If not:** for missing gates, return to 9-1. For missing notes, read the **saved** [review](#read-review), [dev summary](#compare-results), and [holdout summary](#holdout-results). Recover versions from each label's `agent_version` under `verified-evidence.json → runs`, concurrency from `manifest.json → concurrency` in the **completed V1 result folder**, and `Agent runs` / `Total tokens` from the [9-2 dashboard](#operational-dashboard). Do not repeat review, collection, or evaluation.

**Next:** to add Levels 2–3, open the optional section below **before** cleanup; otherwise go to [10. Clean up only your owned workshop objects](#cleanup).

<a id="levels"></a>

<details>
<summary>Optional: with more time, add Levels 2–3 before cleanup</summary>

Stay in this folder. **Do not start these extras after step 10; it deletes the agent.** Additional model and judge calls cost money.

| Choice | Adds | Extra time | Path |
|---|---|---|---|
| Level 2 | Foundry evaluates your business rules; compare runs and failure causes | About 40 minutes | [Level 2](docs/level-2.en.md) → step 10 |
| Levels 2 and 3 | Generated criteria, model/agent/trace evaluation, continuous evaluation, and a release gate | About 110 minutes | [Level 2](docs/level-2.en.md) → [Level 3](docs/level-3.en.md) → step 10 |

</details>

<a id="cleanup"></a>

## 10. Clean up only your owned workshop objects

**Goal:** remove the objects this folder created and owns; keep local evidence and shared services. For self-study, this can include candidate-model deployments.

<a id="stop-early"></a>

<details>
<summary>If you need to finish early or continue another day</summary>

| Choice | Action |
|---|---|
| End before running any Azure creation/change command | Stop local work such as cloning or installation and note the last completed block and error. Do not sign in, run `cleanup`, or delete a resource group just to finish. If unsure whether Azure changes started, use cleanup recovery below. |
| Continue later | Once active work finishes, save `Last completed block / Next block / Workshop folder` and the labels in use in the same notes. Keep the same folder, settings, and evidence; [resume according to a normal pause or error](docs/troubleshooting.en.md#resume). **Closing the terminal may leave Azure resources costing money.** |
| End a run that started creating/changing Azure resources | Confirm that active collection, deployment, and evaluation work has finished. Save only completed steps, errors, and existing evidence in your current notes. Do not create results for unfinished steps; continue to [10-1's deletion plan](#cleanup-plan). |

**Before a long break:** for any collected label whose trace check is unfinished, complete [trace verification](docs/troubleshooting.en.md#telemetry) first and preserve `telemetry.json`. `monitor` looks back **at most 168 hours (7 days)**. Once unverified traces fall outside that window, the provided recovery command cannot retrieve them. This is the tool's query limit, not a claim that Azure deletes traces after seven days.

If your local server is still running, stop it with `Ctrl+C` in its terminal. If a cloud job's state is unclear or deployment/role assignment failed, first work with the owner through [cleanup recovery](docs/troubleshooting.en.md#cleanup-recovery) to confirm **every created object is recorded in the ownership plan**. Missing records do not make an empty plan proof of completed cleanup.

If setup created Azure resources but this folder cannot yet run `cleanup`, the owner uses [exclusive-environment shutdown](docs/environment.en.md#final-cleanup). Never delete a shared group. If steps 1–9 were not completed, record **workshop incomplete** separately from the actual cleanup status.

</details>

**Warning:** before cleanup:

- for a completed workshop, finish every portal check; for an early exit, follow the path above. Cleanup deletes the live agent;
- never run `azd down` or delete a shared resource group;
- Search, logs, the foundation, and the auxiliary model remain after this step and keep costing money. For **your exclusive environment created with the new-environment tools**, stop them by [deleting the resource group](docs/environment.en.md#final-cleanup) after 10-3. Existing or shared environments follow the [owner's separate cleanup scope](docs/instructor.en.md#foundation-cleanup).

<a id="cleanup-plan"></a>

### 10-1. Inspect the deletion plan

**Terminal A:**

```bash
python scripts/workshop.py cleanup --dry-run
```

**Checkpoint:** every target in the printed JSON belongs to this folder's ownership record. For a completed workshop, `agent` is your `LAB_AGENT_NAME` and all three `search_objects` names (`...-kb`, `...-source`, `...-policies`) contain your `LAB_PREFIX`. **For an early exit, expect only objects actually created.** `agent: null` or empty lists are normal for objects never created; if a created object is missing, use the cleanup recovery above before deletion.

**How to compare:** read `src/agent/.foundry/local-state.json` in your editor and compare these fields with the printed plan. Do not edit the file to make them match.

| Plan field | Ownership field |
|---|---|
| `agent` | `agent_owned` (absent/`null` if never created) |
| `search_objects` | The same paths in `owned_search_paths` (order can differ) |
| `role_assignments` | The same full IDs in `owned_roles` |
| `models` | The same names, IDs, models, and versions in `owned_models` |

| Plan field | Expected target |
|---|---|
| `agent`, `search_objects`, `role_assignments` | Your `LAB_AGENT_NAME`, your three `LAB_PREFIX` knowledge objects, and roles created by this folder (long IDs, usually two). In a shared class, have the owner confirm that [shared Search-to-planner access](docs/instructor.en.md#shared-search-access) is not listed; if it is, stop before 10-2. Exclusive self-study may also own that role in this folder. |
| `models` | **Empty for participants using shared deployments.** For self-study, it can contain only the candidates you created with `prepare-models`; delete them only if nobody else uses them. |
| `schedules`, `custom_evaluators`, `generated_datasets` | Empty unless you added Levels 2–3; then only this folder's schedule, evaluators, and generated datasets |
| `preserved` | The existing Foundry project, Search, App Insights, and evaluation evidence (not deleted) |

The foundation and auxiliary planner/judge are preserved. A model's name in `.env` does not establish ownership. **Copy the checked JSON output into your existing notes.** `--dry-run` does not save a plan file, and matching records does not replace the shared-dependency checks above.

**If not:** do not run 10-2; follow the “ownership/targets do not match” row of [cleanup recovery](docs/troubleshooting.en.md#cleanup-recovery). Delete nothing.

### 10-2. Delete only the reviewed plan

**Terminal A:**

```bash
python scripts/workshop.py cleanup --confirm
```

**Checkpoint:** the output ends with `Owned workshop resources removed; shared infrastructure and evidence preserved.`

**If not:** use [cleanup recovery](docs/troubleshooting.en.md#cleanup-recovery).

<a id="cleanup-check"></a>

### 10-3. Verify deletion separately

**Plan to compare:** open `plan` in `src/agent/.foundry/results/cleanup.json` in your editor. This is the plan 10-2 actually used; its targets must match your 10-1 notes. Compare the counts below with this `plan`. Do not repeat deletion or dry-run to recover the original plan.

**Terminal A:**

```bash
python scripts/workshop.py check-cleanup
```

**Checkpoint:** the printed JSON, saved as `src/agent/.foundry/results/cleanup-check.json`, shows `temporary_hosted_agent_absent: true`, `existing_foundry_project_preserved: true`, and `existing_search_service_preserved: true`. Each `*_absent` number counts deletions it confirmed: `temporary_search_objects_absent`, `temporary_role_assignments_absent`, and `temporary_model_deployments_absent` equal the number of `search_objects`, `role_assignments`, and `models` in your 10-1 plan.

**If not:** if only this check fails, [recover the check](docs/troubleshooting.en.md#cleanup-recovery). Never repeat a successful `cleanup --confirm`; it would replace the saved plan.

<details>
<summary>Example screen: cleanup confirmation</summary>

![Verified English workshop cleanup](docs/assets/live-en-20260923b/screenshots/10-cleanup.webp)

</details>

**The main workshop is complete only if you also finished steps 1–9.** Keep your [9-3 report](#finish), the cleanup check, and local evidence. For an early exit, retain the incomplete status and existing evidence only. **If you created the environment yourself,** [delete its resource group](docs/environment.en.md#final-cleanup) when you no longer need it; only that stops the Search, logging, and other foundation costs. Never delete a class or shared group.

<details>
<summary>Where your saved evidence is</summary>

| Location | Purpose |
|---|---|
| `src/agent/.foundry/results/baseline/` | 18 actual English V1 responses and their evaluations |
| `src/agent/.foundry/results/improved/` | 18 actual English V2 responses and their evaluations |
| `src/agent/.foundry/results/holdout/` | 12 responses from the frozen candidate |
| `src/agent/.foundry/results/comparison.json` | Before/after model metrics and failing cases |
| `src/agent/.foundry/datasets/regression-*.jsonl` | Reviewed case, fixed reference answer, and source trace |
| `src/agent/.foundry/results/verified-evidence.json` | Complete execution and lineage checks |
| `src/agent/.foundry/results/workshop-report.txt` | Your three-point report saved in 9-3 |
| `src/agent/.foundry/results/cleanup-check.json` | Deletion verification; the checked plan is in the same folder's `cleanup.json` |

Keep them for your report and any recovery; do not delete them or replace them with an example run.

</details>

## References

Everything below is optional; the 10-step workshop is complete.

- **Results and limits:** [evaluation method and English results](docs/validation.en.md)
- **Design and terms:** [learning-loop background](docs/reference.en.md#background) · [glossary](docs/reference.en.md#terms) · [architecture, models, and official sources](docs/reference.en.md)
- **Levels 2–3:** [Foundry custom evaluators and insights](docs/level-2.en.md) · [generated rubric, stress test, red teaming, live agent, trace and continuous evaluation, and release gate](docs/level-3.en.md)
- **Errors:** [troubleshooting](docs/troubleshooting.en.md)
- **Instructors and self-study setup:** [instructor preparation](docs/instructor.en.md) · [create a new English Azure environment](docs/environment.en.md)
- **Optional:** [delegate to Copilot CLI](docs/copilot.en.md)

<a id="summary-video"></a>

## Optional: 9-minute summary video

<details>
<summary>Watch the 8m40s English workshop summary</summary>

[English workshop summary (MP4, 8.4 MiB)](videos/foundry-evaluation-gpt6-en-20260923b.mp4)

It replays the verified English run of September 23, 2026 (`en-20260923b`). If the video and the text differ, follow the text.

- Portal segments are headless recordings; **CLI segments replay saved output, not live capture**.
- The `summary` tables at 6-1, 7-4, and 8-3 were rendered later with the current read-only `summary` command over the saved results; the optional portal V1/V2 comparison appears after 7-4, as in this guide.
- Level 2 and Level 3 chapters replay the same day's level-rehearsal output; the red-team chapter shows a rerun with the current `red-team` command.
- It is silent, waits are trimmed, and sign-in and account identifiers are removed.

| Step | Video position | Step | Video position |
|---|---|---|---|
| 1. Prepare | 00:07 | 2. Knowledge | 00:28 |
| 3. Local agent | 01:07 | 4. Hosted agent | 01:29 |
| 5. Baseline | 01:48 | 6. Trace and review | 02:28 |
| 7. V2 comparison | 03:43 | 8. Holdout | 05:16 |
| 9. Observe | 06:03 | Level 2 | 07:00 |
| Level 3 | 07:22 | 10. Cleanup | 08:08 |

The [Korean guide](README.ko.md#summary-video) has a 15m02s recording of the Korean run with live CLI footage.

</details>
