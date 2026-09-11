async (page) => {
  if (page.__portalCapture?.status === "recording") throw new Error("Portal recording is already active.");
  const browser = page.__realPortalBrowser;
  const state = await page.__realPortalContext.storageState({indexedDB:true});
  const context = await browser.newContext({
    storageState: state,
    viewport: {width:1920,height:1080},
    recordVideo: {
      dir: "/Users/junwoojeong/GitHub/foundry-evaluation/artifacts/foundry-portal-recording/raw",
      size: {width:1920,height:1080}
    }
  });
  await context.addInitScript(() => {
    const conceal = () => {
      document.querySelectorAll('[aria-label^="Account menu"],[aria-label="My profile settings"]').forEach(element => {
        element.style.filter="blur(10px)";
        element.dataset.privacyRedacted="true";
      });
      const walker=document.createTreeWalker(document.body || document.documentElement,NodeFilter.SHOW_TEXT);
      let text;
      while((text=walker.nextNode())){
        if((/[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}/.test(text.textContent)||text.textContent.includes("Junwoo Jeong"))&&text.parentElement&&text.parentElement.childElementCount===0){
          text.parentElement.style.filter="blur(10px)";
          text.parentElement.dataset.privacyRedacted="true";
        }
      }
    };
    addEventListener("DOMContentLoaded",()=>{
      conceal();
      new MutationObserver(conceal).observe(document.body,{subtree:true,childList:true,characterData:true});
    });
  });
  const p=await context.newPage();
  const started=Date.now();
  const capture={
    context,page:p,status:"recording",started,segments:[],video:null,currentKey:"main",
    pages:[{key:"main",page:p,offset_ms:0}],
    createdModels:[],deletedModels:[],createdDatasets:[],
    register(key,target){
      const existing=this.pages.find(item=>item.page===target);
      if(existing){existing.key=key;return;}
      this.pages.push({key,page:target,offset_ms:Date.now()-this.started});
    },
    use(key){
      const item=this.pages.find(item=>item.key===key);
      if(!item)throw new Error("Register the recorded page before selecting it.");
      this.end();this.page=item.page;this.currentKey=key;
    },
    begin(label){
      this.end();
      this.segments.push({label,start_ms:Date.now()-this.started,page_key:this.currentKey,source:this.page.url().split("?")[0]});
    },
    end(){const last=this.segments[this.segments.length-1];if(last&&!last.end_ms)last.end_ms=Date.now()-this.started;}
  };
  context.on("page",target=>capture.register(`popup-${capture.pages.length}`,target));
  page.__portalCapture=capture;
  const home=await page.__realPortalPage.getByRole("banner").getByRole("link",{name:"Home",exact:true}).getAttribute("href");
  await p.goto("https://ai.azure.com"+home);
  await p.getByRole("main").waitFor();
  capture.begin("01 Foundry project and learning-loop entry");
  return {status:"recording",headless:true,hostname:p.url().split("/")[2],started,old_video_preserved:true};
}
