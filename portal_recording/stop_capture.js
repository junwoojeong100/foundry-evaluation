async (page) => {
  const r = page.__portalCapture;
  if (!r || r.status !== "recording") throw new Error("No live portal recording.");
  r.end();
  const pageKeys = new Set(r.segments.map(segment => segment.page_key || "main"));
  const pages = r.pages.filter(item => pageKeys.has(item.key)).map(item => ({
    key: item.key,
    offset_ms: item.offset_ms,
    video: item.page.video()
  }));
  await Promise.all(r.pages.filter(item => !item.page.isClosed()).map(item => item.page.close()));
  await r.context.close();
  const metadata = {
    started: r.started,
    ended: Date.now(),
    headless: true,
    method: "Playwright recordVideo of actual Microsoft portal pages",
    pages: [],
    segments: r.segments.map((segment, index) => ({index, ...segment})),
    created_models: r.createdModels,
    deleted_models: r.deletedModels,
    created_datasets: r.createdDatasets,
    supplemental_ui_evaluation: r.uiEvaluation
  };
  for (const item of pages) {
    if (item.video) {
      metadata.pages.push({
        key: item.key,
        offset_ms: item.offset_ms,
        video: await item.video.path()
      });
    }
  }
  const pending = page.waitForEvent("download");
  await page.evaluate(value => {
    const url = URL.createObjectURL(new Blob([JSON.stringify(value, null, 2)], {type: "application/json"}));
    const link = document.createElement("a");
    link.href = url;
    link.download = "capture-metadata.json";
    link.style.display = "none";
    document.body.appendChild(link);
    link.click();
    link.remove();
    setTimeout(() => URL.revokeObjectURL(url), 10000);
  }, metadata);
  const download = await pending;
  await download.saveAs("/Users/junwoojeong/GitHub/foundry-evaluation/artifacts/foundry-portal-recording/capture-metadata.json");
  r.status = "completed";
  r.metadata = metadata;
  return {
    status: r.status,
    pages: metadata.pages,
    segment_count: metadata.segments.length,
    metadata_file: "artifacts/foundry-portal-recording/capture-metadata.json"
  };
}
