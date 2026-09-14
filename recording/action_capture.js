module.exports = async (page) => {
  const previous = page.__actionCapture;
  if (previous?.running || previous?.active) throw new Error("Finish the active capture before refreshing its helpers.");
  const response = await page.request.get("http://127.0.0.1:8897/api/config");
  if (!response.ok()) throw new Error("The recording console is unavailable.");
  const setup = await response.json();
  const run = setup.run;
  const directory = setup.paths.private;
  const shots = setup.paths.screenshots;
  if (previous && previous.run !== run) throw new Error("A different run cannot reuse these capture contexts.");
  const browser = previous?.browser || page.context().browser();
  const cliKey = previous?.cliKey || "cli";
  const context = previous?.context || await browser.newContext({
    viewport: { width: 1920, height: 1080 },
    recordVideo: {     dir: `${directory}/raw/${cliKey}`, size: { width: 1920, height: 1080 } },
  });
  const cli = previous?.cli || await context.newPage();
  const cliStarted = previous?.pages.find(item => item.key === cliKey)?.started || Date.now();
  await cli.goto("http://127.0.0.1:8897/");
  await cli.waitForFunction(() => window.actionConsoleReady === true);
  const configuration = await cli.evaluate(async () => (await fetch("/api/config")).json());
  const capture = {
    run, directory, shots, browser, context, cli, cliKey, actions: [], pages: [
      { key: cliKey, page: cli, context, started: cliStarted, video_dir: `${directory}/raw/${cliKey}` },
    ],
    active: null, running: false, error: null,
    ...previous,
    async save() {
      const report = {
        run: this.run, mode: "playwright-headless", running: this.running, error: this.error,
        pages: this.pages.map(({key,started,video,video_dir}) => ({key,started,video,video_dir})),
        actions: this.actions,
      };
      const response = await page.request.post("http://127.0.0.1:8897/api/capture", {
        headers: {"Origin": "http://127.0.0.1:8897", "X-Recording-Token": configuration.token},
        data: report,
      });
      if (!response.ok()) throw new Error(`Capture metadata was not saved: ${response.status()}`);
    },
    async shot(target, action, suffix) {
      const hostname = target.url().split("/")[2] || "";
      if (hostname.startsWith("login.")) {
        throw new Error("Authentication screens must not become guide screenshots.");
      }
      const filename = `${action.id}-${suffix}.png`;
      await target.screenshot({ path: `${this.shots}/${filename}`, type: "png" });
      action.screenshots.push({ filename, at: Date.now(), phase: suffix });
      await this.save();
    },
    async runCLI(ids) {
      if (this.running || this.active) throw new Error("Finish the current recorded action first.");
      this.running = true;
      this.error = null;
      await this.cli.evaluate(() => window.actionConsole.catalog());
      const available = await this.cli.evaluate(async () => (await fetch("/api/config")).json());
      this.promise = (async () => {
        try {
          for (const id of ids) {
            const definition = available.actions.find(action => action.id === id);
            if (!definition) throw new Error(`Unknown action: ${id}`);
            await this.cli.getByRole("combobox", {name: "실습 절차"}).selectOption(id);
            const action = {
              id, kind: "cli", title: definition.title, guide: definition.guide,
              check: definition.check, command: definition.command, page_key: this.cliKey,
              started: Date.now(), screenshots: [], status: "running",
            };
            this.actions.push(action);
            this.active = action;
            await this.cli.waitForTimeout(1500);
            await this.shot(this.cli, action, "before");
            await this.cli.getByRole("button", {name: "실제 명령 실행", exact: true}).click();
            action.command_at = Date.now();
            await this.cli.waitForFunction(
              target => ["completed", "service_ready", "failed"].includes(window.actionState.jobs[target]?.status),
              id, {timeout: 1900000},
            );
            const result = await this.cli.evaluate(target => window.actionState.jobs[target], id);
            action.result_at = Date.now();
            action.status = result.status;
            action.elapsed_seconds = result.ended - result.started;
            await this.cli.waitForTimeout(2500);
            await this.shot(this.cli, action, "after");
            const overflow = await this.cli.locator("#terminal").evaluate(
              element => element.scrollHeight > element.clientHeight * 1.5,
            );
            if (overflow) {
              await this.cli.locator("#terminal").evaluate(element => element.scrollTop = 0);
              await this.cli.waitForTimeout(1800);
              await this.shot(this.cli, action, "output-start");
              await this.cli.locator("#terminal").evaluate(element => element.scrollTop = element.scrollHeight);
              await this.cli.waitForTimeout(1800);
            }
            action.ended = Date.now();
            this.active = null;
            await this.save();
            if (!["completed", "service_ready"].includes(result.status)) throw new Error(`${id}: ${result.error}`);
          }
        } catch (error) {
          this.error = String(error);
          if (this.active) {
            this.active.status = "capture-error";
            this.active.error = String(error);
            this.active.ended = Date.now();
            this.active = null;
          }
        } finally {
          this.running = false;
          await this.save();
        }
      })();
      await this.save();
      return {started: ids, headless: true};
    },
    async beginPortal(id, title, guide, check = "") {
      if (this.running || this.active) throw new Error("Finish the current recorded action first.");
      if (!this.portal) throw new Error("Attach the authenticated, headless portal context first.");
      if (this.actions.some(action => action.id === id)) throw new Error("Action IDs cannot overwrite evidence.");
      const action = {
        id, kind: "portal", title, guide, check, page_key: this.portalKey || "portal",
        started: Date.now(), screenshots: [], status: "running",
      };
      this.actions.push(action);
      this.active = action;
      await this.shot(this.portal, action, "before");
      return action.id;
    },
    async endPortal(status = "completed") {
      const action = this.active;
      if (!action || action.kind !== "portal") throw new Error("No portal action is active.");
      await this.portal.waitForTimeout(1500);
      action.result_at = Date.now();
      await this.shot(this.portal, action, status === "completed" ? "after" : "failed");
      await this.portal.waitForTimeout(2200);
      action.ended = Date.now();
      action.status = status;
      this.active = null;
      await this.save();
      return {id: action.id, status, screenshots: action.screenshots.map(shot => shot.filename)};
    },
    async finish() {
      if (this.running || this.active) throw new Error("A recorded action has not finished.");
      for (const item of this.pages) {
        if (item.video) continue;
        const video = item.page.video();
        for (const openPage of item.context.pages()) {
          await openPage.close({runBeforeUnload: false});
        }
        await item.context.close();
        item.video = await video.path();
        await this.save();
      }
      await this.save();
      return {actions: this.actions.length, videos: this.pages.map(item => item.video)};
    },
  };
  if (!capture.pages.some(item => item.page === cli)) {
    capture.pages.push({key: cliKey, page: cli, context, started: cliStarted, video_dir: `${directory}/raw/${cliKey}`});
  }
  page.__actionCapture = capture;
  await capture.save();
  return {started: true, refreshed: !!previous, mode: "playwright-headless", directory, screenshots: shots};
}
