async (page) => {
  if (page.__workshopCapture?.status === "running") {
    throw new Error("A recording is already running.");
  }
  const browser = page.context().browser();
  const context = await browser.newContext({
    viewport: { width: 1920, height: 1080 },
    recordVideo: {
      dir: "/Users/junwoojeong/GitHub/foundry-evaluation/artifacts/recording/raw",
      size: { width: 1920, height: 1080 }
    }
  });
  const recordingPage = await context.newPage();
  await recordingPage.goto("http://127.0.0.1:8877/");
  await recordingPage.waitForFunction(() => window.recordingReady === true);
  const capture = {
    status: "running", page: recordingPage, context,
    started: Date.now(), step: null, markers: [], video: null, error: null
  };
  page.__workshopCapture = capture;
  capture.promise = (async () => {
    try {
      const config = await recordingPage.evaluate(async () => (await fetch("/api/config")).json());
      for (const step of config.steps) {
        const existing = await recordingPage.evaluate(id => window.recordingState.jobs[id]?.status, step.id);
        if (existing === "completed") continue;
        capture.step = step.id;
        await recordingPage.locator(`#chapters button[data-chapter="${Number(step.chapter)-1}"]`).click();
        await recordingPage.locator('[data-view="terminal"]').click();
        await recordingPage.getByRole("combobox", { name: "실습 명령" }).selectOption(step.id);
        await recordingPage.evaluate(s => window.lab.caption(s.description, `실제 실행 · ${s.title}`, "대기 시간은 최종 편집에서 제거"), step);
        await recordingPage.waitForTimeout(1200);
        const marker = { step: step.id, start_ms: Date.now()-capture.started };
        capture.markers.push(marker);
        await recordingPage.getByRole("button", { name: "이 명령 실행", exact: true }).click();
        await recordingPage.waitForFunction(id => !!window.recordingState.jobs[id], step.id);
        marker.command_ms = Date.now()-capture.started;
        await recordingPage.waitForTimeout(2000);
        marker.wait_start_ms = Date.now()-capture.started;
        await recordingPage.waitForFunction(
          id => ["completed", "failed"].includes(window.recordingState.jobs[id]?.status),
          step.id, { timeout: 1800000 }
        );
        marker.wait_end_ms = Date.now()-capture.started;
        const job = await recordingPage.evaluate(id => window.recordingState.jobs[id], step.id);
        marker.status = job.status;
        await recordingPage.waitForTimeout(2500);
        marker.end_ms = Date.now()-capture.started;
        if (job.status !== "completed") throw new Error(`${step.id}: ${job.error || "실제 명령 실패"}`);
      }
      capture.status = "completed";
    } catch (error) {
      capture.status = "failed";
      capture.error = String(error);
    } finally {
      const video = recordingPage.video();
      await context.close();
      capture.video = await video.path();
      capture.ended = Date.now();
    }
  })();
  return { status: "started", headless_browser: browser.version(), viewport: "1920x1080", capture_started: capture.started };
}
