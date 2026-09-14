module.exports = async (page) => {
  const c = page.__actionCapture;
  if (!c?.authContext || !c.groupId) throw new Error("Verify portal authentication and the returned group ID first.");
  if (c.portal) throw new Error("The portal recording already exists.");
  const profileButton = c.authPage.getByRole("button", {name: /^Profile with current directory/});
  await profileButton.click();
  const dialog = c.authPage.getByRole("dialog");
  await dialog.waitFor();
  const names = await dialog.getByRole("img").evaluateAll(elements =>
    elements.map(element => element.getAttribute("aria-label") || element.getAttribute("alt")).filter(Boolean),
  );
  await c.authPage.getByRole("button", {name: "Close profile panel", exact: true}).click();
  const state = await c.authContext.storageState({indexedDB: true});
  const key = c.portalKey || "portal";
  const context = await c.browser.newContext({
    storageState: state, viewport: {width: 1920, height: 1080},
    recordVideo: {dir: `${c.directory}/raw/${key}`, size: {width: 1920, height: 1080}},
  });
  await context.addInitScript(privateNames => {
    let scheduled = false;
    const conceal = () => {
      scheduled = false;
      if (!document.body) return;
      if (location.hostname.startsWith("login.")) {
        document.documentElement.style.visibility = "hidden";
        return;
      }
      const mark = element => {
        if (element.dataset.recordingPrivate === "true") return;
        element.style.setProperty("filter", "blur(12px)", "important");
        element.dataset.recordingPrivate = "true";
      };
      document.querySelectorAll(
        '[aria-label^="Account menu"],[aria-label^="Profile with current directory"],[aria-label="My profile settings"]',
      ).forEach(mark);
      const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
      let node;
      while ((node = walker.nextNode())) {
        const text = node.textContent || "";
        const sensitive = /[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}/.test(text)
          || /\b[0-9a-f]{8}(?:-[0-9a-f]{4}){3}-[0-9a-f]{12}\b/i.test(text)
          || /ME-MngEnvMCAP[^\s"']+/i.test(text)
          || privateNames.some(name => name.length > 2 && text.includes(name));
        if (sensitive && node.parentElement?.childElementCount === 0) mark(node.parentElement);
      }
    };
    const schedule = () => {
      if (!scheduled) { scheduled = true; requestAnimationFrame(conceal); }
    };
    addEventListener("DOMContentLoaded", () => {
      conceal();
      new MutationObserver(schedule).observe(document.body, {subtree: true, childList: true, characterData: true});
    });
  }, names);
  const portal = await context.newPage();
  const started = Date.now();
  c.portal = portal;
  c.portalContext = context;
  c.pages.push({key, page: portal, context, started, video_dir: `${c.directory}/raw/${key}`});
  await c.save();
  return {ready: true, headless: true, privacy_masks: true, authentication_recorded: false};
}
