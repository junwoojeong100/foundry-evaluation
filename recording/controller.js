const fs = require("node:fs/promises");
const path = require("node:path");
const http = require("node:http");
const { chromium } = require("playwright");
const attachCapture = require("./action_capture");
const attachPortal = require("./portal_action_capture");

const root = path.resolve(__dirname, "..");
let capture, main, browser, manualAuth, config, runDir, server;
let controlBusy = false;
let stateWrites = Promise.resolve();
let finished = false;

function redactUI(text) {
  return text
    .replace(/([?&](?:sig|access_token|token|client_secret|code)=)[^&\s"']+/gi, "$1[redacted]")
    .replace(/(Bearer\s+)[A-Za-z0-9_.-]{20,}/gi, "$1[redacted]")
    .replace(/eyJ[\w-]+\.[\w-]+\.[\w-]+/g, "[token]");
}

async function writeState() {
  const state = {
    run: capture.run, mode: "playwright-headless", controller: "dedicated-process",
    running: capture.running, error: capture.error,
    pages: capture.pages.map(({key, started, video, video_dir}) => ({key, started, video, video_dir})),
    actions: capture.actions,
  };
  const target = path.join(runDir, "capture-state.json");
  const temporary = target + ".controller-tmp";
  const content = JSON.stringify(state, null, 2) + "\n";
  stateWrites = stateWrites.then(async () => {
    await fs.writeFile(temporary, content, {mode: 0o600});
    await fs.rename(temporary, target);
  });
  await stateWrites;
}

async function restoredState() {
  const filename = path.join(runDir, "capture-state.json");
  let old;
  try { old = JSON.parse(await fs.readFile(filename, "utf8")); }
  catch (error) { if (error.code === "ENOENT") return null; throw error; }
  if (old.run !== config.run_id) throw new Error("The previous capture belongs to a different run.");
  await fs.copyFile(filename, path.join(runDir, `capture-before-controller-${Date.now()}.json`));
  for (const item of old.pages) {
    if (!item.video) throw new Error("Map and verify interrupted video files before resuming.");
  }
  if (old.actions.some(action => action.status === "running")) {
    throw new Error("Preserve and classify the interrupted action before resuming.");
  }
  const part = 1 + Math.max(1, ...old.pages.map(item => Number(item.key.match(/-(\d+)$/)?.[1] || 1)));
  return {
    run: old.run, actions: old.actions, pages: old.pages,
    cliKey: `cli-${part}`, portalKey: `portal-${part}`,
    running: false, active: null, error: null,
  };
}

function portalLocator(spec) {
  if (!capture.portal) throw new Error("Authenticate and attach the headless portal first.");
  const scope = spec.frame === undefined ? capture.portal : capture.portal.frames()[spec.frame];
  if (!scope) throw new Error("The requested frame no longer exists; take a fresh snapshot.");
  let locator;
  if (spec.role) {
    locator = scope.getByRole(spec.role, {
      name: spec.regex ? new RegExp(spec.name) : spec.name, exact: spec.exact ?? true,
    });
  } else if (spec.selector) {
    locator = scope.locator(spec.selector);
  } else {
    throw new Error("An observed role/name or selector is required.");
  }
  if (spec.hasText) locator = locator.filter({hasText: spec.hasText});
  if (spec.nth !== undefined) locator = locator.nth(spec.nth);
  return locator;
}

function requirePortalAction() {
  if (!capture.active || capture.active.kind !== "portal") {
    throw new Error("Begin a recorded portal action before changing its UI.");
  }
}

async function authenticate() {
  if (capture.running || capture.active) throw new Error("Finish the active recorded action before attaching portal authentication.");
  if (!manualAuth) throw new Error("Open the authentication window first.");
  const authPage = manualAuth.page;
  if (!authPage.url().startsWith("https://ai.azure.com/")) {
    return {authenticated: false, host: new URL(authPage.url()).hostname, title: await authPage.title()};
  }
  if (!(await authPage.getByRole("button", {name: /^Profile with current directory/}).count())) {
    return {authenticated: false, message: "Finish signing in to Foundry in the authentication-only window."};
  }
  const state = await manualAuth.context.storageState({indexedDB: true});
  const context = await browser.newContext({storageState: state, viewport: {width: 1920, height: 1080}});
  const p = await context.newPage();
  await p.goto(authPage.url());
  const profile = p.getByRole("button", {name: /^Profile with current directory/});
  await profile.waitFor({timeout: 60000});
  await profile.click();
  const dialog = p.getByRole("dialog");
  await dialog.waitFor();
  const text = (await dialog.innerText()).toLowerCase();
  if (!text.includes(config.username.toLowerCase())) {
    await context.close();
    throw new Error("The portal is signed in to a different account.");
  }
  await p.getByRole("button", {name: "Close profile panel", exact: true}).click();
  const azure = await context.newPage();
  await azure.goto(`https://portal.azure.com/#@${config.username.split("@")[1]}/home`);
  const accountMenu = azure.getByRole("button", {name: /^Account menu Currently signed in as/});
  await accountMenu.waitFor({timeout: 60000});
  if (!(await accountMenu.getAttribute("aria-label")).toLowerCase().includes(config.username.toLowerCase())) {
    await context.close();
    throw new Error("Azure Portal is signed in to a different account.");
  }
  capture.authContext = context;
  capture.authPage = p;
  const infra = JSON.parse(await fs.readFile(path.join(runDir, "infrastructure-state.json"), "utf8"));
  capture.groupId = infra.group_id;
  await attachPortal(main);
  await context.close();
  capture.authContext = null;
  capture.authPage = null;
  await manualAuth.browser.close();
  manualAuth = null;
  await writeState();
  return {authenticated: true, requested_account_verified: true, headless: true, auth_state_saved_to_disk: false};
}

async function dispatch(request) {
  switch (request.op) {
    case "status":
      return {
        run: capture.run, browser_connected: browser.isConnected(), headless: true,
        running: capture.running, active: capture.active?.id, error: capture.error,
        actions: capture.actions.length, portal_attached: !!capture.portal,
        last: capture.actions.slice(-4).map(({id,status}) => ({id,status})),
      };
    case "auth-open": {
      if (manualAuth?.browser.isConnected() && !manualAuth.page.isClosed()) {
        await manualAuth.page.bringToFront();
        return {authentication_window_open: true, recording: false};
      }
      manualAuth = null;
      const authBrowser = await chromium.launch({channel: "msedge", headless: false});
      const context = await authBrowser.newContext({viewport: {width: 1440, height: 1000}});
      const p = await context.newPage();
      manualAuth = {browser: authBrowser, context, page: p};
      await p.goto("https://ai.azure.com/login");
      await p.bringToFront();
      return {authentication_window_open: true, isolated_profile: true, recording: false};
    }
    case "auth-check":
      return await authenticate();
    case "cli":
      return await capture.runCLI(request.ids);
    case "begin":
      return {started: await capture.beginPortal(request.id, request.title, request.guide, request.check || "")};
    case "end":
      return await capture.endPortal(request.status || "completed");
    case "snapshot": {
      if (!capture.portal) throw new Error("The portal is not attached.");
      const maximum = request.max_chars || 18000;
      const frames = [];
      for (const [index, frame] of capture.portal.frames().entries()) {
        if (frame.isDetached()) continue;
        frames.push({
          index, url: frame.url().split(/[?#]/)[0],
          snapshot: redactUI(await frame.locator("body").ariaSnapshot()).slice(0, maximum),
        });
      }
      return {url: capture.portal.url(), frames};
    }
    case "goto": {
      requirePortalAction();
      const url = new URL(request.url);
      if (url.protocol !== "https:" || !["ai.azure.com", "portal.azure.com", "ms.portal.azure.com"].includes(url.hostname)) {
        throw new Error("Only the actual Foundry and Azure portals may be navigated.");
      }
      await capture.portal.goto(request.url, {waitUntil: "domcontentloaded", timeout: 60000});
      return {url: capture.portal.url()};
    }
    case "click":
      requirePortalAction();
      await portalLocator(request).click({timeout: 15000});
      return {clicked: true};
    case "fill":
      requirePortalAction();
      await portalLocator(request).fill(request.text);
      return {filled: true};
    case "press":
      requirePortalAction();
      await portalLocator(request).press(request.key);
      return {pressed: request.key};
    case "select":
      requirePortalAction();
      await portalLocator(request).selectOption(request.value);
      return {selected: request.value};
    case "scroll":
      requirePortalAction();
      await portalLocator(request).evaluate((element, top) => {
        element.scrollTop = top === "bottom" ? element.scrollHeight : Number(top);
      }, request.top);
      return {scrolled: true};
    case "wait":
      await portalLocator(request).waitFor({state: "visible", timeout: request.timeout || 30000});
      return {visible: true};
    case "read": {
      const locator = portalLocator(request);
      if (request.attribute) {
        if (!["href", "aria-label", "title", "role"].includes(request.attribute)) {
          throw new Error("Only non-secret UI attributes can be read.");
        }
        const value = await locator.getAttribute(request.attribute);
        return {value: value === null ? null : redactUI(value)};
      }
      return {text: redactUI(await locator.innerText())};
    }
    case "finish":
      await capture.finish();
      await writeState();
      finished = true;
      return {actions: capture.actions.length, videos: capture.pages.map(item => item.video)};
    default:
      throw new Error("Unknown controller operation.");
  }
}

async function start() {
  const index = process.argv.indexOf("--run-dir");
  if (index < 0 || !process.argv[index + 1]) throw new Error("--run-dir is required.");
  runDir = path.resolve(process.argv[index + 1]);
  if (!runDir.startsWith(path.join(root, ".recording") + path.sep)) throw new Error("Use this repository's private recording directory.");
  config = JSON.parse(await fs.readFile(path.join(runDir, "config.json"), "utf8"));
  const previous = await restoredState();
  browser = await chromium.launch({channel: "msedge", headless: true});
  const context = await browser.newContext();
  main = await context.newPage();
  if (previous) main.__actionCapture = previous;
  await attachCapture(main);
  capture = main.__actionCapture;
  capture.save = writeState;
  await writeState();
  browser.on("disconnected", () => {
    if (finished) return;
    capture.error = "Headless browser disconnected; do not count an unfinished action as completed.";
    if (capture.active) {
      capture.active.status = "interrupted";
      capture.active.ended = Date.now();
      capture.active = null;
    }
    capture.running = false;
    writeState().catch(error => console.error(error));
  });
  const socketPath = path.join(runDir, "control.sock");
  try { await fs.access(socketPath); throw new Error("The controller socket already exists; inspect its owner first."); }
  catch (error) { if (error.code !== "ENOENT") throw error; }
  server = http.createServer(async (request, response) => {
    response.setHeader("Content-Type", "application/json; charset=utf-8");
    if (request.method !== "POST" || request.url !== "/control") {
      response.writeHead(404).end(JSON.stringify({error: "Not found"}));
      return;
    }
    if (controlBusy) {
      response.writeHead(409).end(JSON.stringify({error: "Another UI operation is running."}));
      return;
    }
    controlBusy = true;
    try {
      const chunks = [];
      let length = 0;
      for await (const chunk of request) {
        length += chunk.length;
        if (length > 100000) throw new Error("Controller request too large.");
        chunks.push(chunk);
      }
      const result = await dispatch(JSON.parse(Buffer.concat(chunks).toString("utf8")));
      response.end(JSON.stringify(result));
    } catch (error) {
      console.error(String(error));
      response.writeHead(400).end(JSON.stringify({error: String(error)}));
    } finally {
      controlBusy = false;
    }
  });
  await new Promise((resolve, reject) => {
    server.once("error", reject);
    server.listen(socketPath, resolve);
  });
  await fs.chmod(socketPath, 0o600);
  console.log(JSON.stringify({ready: true, headless: true, control: "private Unix socket", run: capture.run}));
}

start().catch(async error => {
  console.error(error);
  if (server?.listening) server.close();
  if (browser?.isConnected()) await browser.close();
  process.exitCode = 1;
});
