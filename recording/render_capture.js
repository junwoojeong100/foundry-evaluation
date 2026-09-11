async (page) => {
  if (page.__workshopRender?.status === "running") throw new Error("Render already running.");
  const browser = page.context().browser();
  const context = await browser.newContext({
    viewport: { width: 1920, height: 1080 },
    recordVideo: {
      dir: "/Users/junwoojeong/GitHub/foundry-evaluation/artifacts/recording/raw",
      size: { width: 1920, height: 1080 }
    }
  });
  const rp = await context.newPage();
  const pageCreated = Date.now();
  await rp.goto("http://127.0.0.1:8877/");
  await rp.waitForFunction(() => window.recordingReady === true);
  const story = await rp.evaluate(async () => (await fetch("/api/story")).json());
  const recordingConfig = await rp.evaluate(async () => (await fetch("/api/config")).json());
  const state = await rp.evaluate(() => window.recordingState);
  if (Object.values(state.jobs).filter(job => job.status === "completed").length !== 29) {
    await context.close();
    throw new Error("All real guide steps must finish before rendering the edited walkthrough.");
  }
  await rp.evaluate(() => window.lab.presentation(true));
  const render = { status: "running", started: Date.now(), page_created: pageCreated, page: rp, video: null, cues: [], error: null };
  page.__workshopRender = render;
  render.promise = (async () => {
    try {
      for (const cue of story.cues) {
        const target = render.started + cue.start * 1000;
        if (Date.now() < target) await rp.waitForTimeout(target - Date.now());
        await rp.locator(`#chapters button[data-chapter="${cue.chapter}"]`).click();
        await rp.locator(`[data-view="${cue.view}"]`).click();
        if (cue.source) await rp.getByRole("combobox", { name: "코드 파일" }).selectOption(cue.source);
        if (cue.source) await rp.waitForFunction(key => document.querySelector("#source-code").dataset.source === key, cue.source);
        if (cue.step) await rp.getByRole("combobox", { name: "실습 명령" }).selectOption(cue.step);
        if (cue.result && cue.view === "results") await rp.getByRole("combobox", { name: "결과 코호트" }).selectOption(cue.result);
        if (cue.result && cue.view === "trace") await rp.getByRole("combobox", { name: "Trace 코호트" }).selectOption(cue.result);
        await rp.evaluate(c => window.lab.caption(c.caption, `CHAPTER ${String(c.chapter+1).padStart(2,"0")} · 실제 실행기록`, "대기 시간 제거 · 한국어 AI 합성 음성"), cue);
        render.cues.push({ index: cue.index, actual_ms: Date.now()-render.started, expected_ms: cue.start*1000 });
        if (cue.view === "code") {
          await rp.waitForTimeout(Math.min(1800, cue.duration*200));
          const lines = cue.source === "agent" ? [27, 73] : cue.source === "knowledge" ? [23, 72] : cue.source === "evaluation" ? [155, 207] : [1, 22];
          await rp.evaluate(range => window.lab.highlight(...range), lines);
        }
      }
      const end = render.started + story.target_seconds * 1000;
      if (Date.now() < end) await rp.waitForTimeout(end - Date.now());
      render.status = "completed";
    } catch (error) {
      render.status = "failed";
      render.error = String(error);
    } finally {
      const video = rp.video();
      await context.close();
      render.video = await video.path();
      render.ended = Date.now();
      const saved = await page.request.post("http://127.0.0.1:8877/api/capture", {
        headers: { "Origin": "http://127.0.0.1:8877", "X-Recording-Token": recordingConfig.token },
        data: { kind: "render", status: render.status, started: render.started, page_created: render.page_created, ended: render.ended, video: render.video, cues: render.cues, error: render.error }
      });
      if (!saved.ok()) throw new Error("Could not persist completed recording metadata.");
    }
  })();
  return { status: "started", target_seconds: story.target_seconds, cues: story.cues.length, headless_browser: browser.version() };
}
