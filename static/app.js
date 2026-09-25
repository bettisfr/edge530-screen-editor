const state = { catalog: [], screens: [], screenIndex: 0, category: "All", selectedField: null, filename: "", original: null, dirty: false, prepared: false, deviceReady: false };
const $ = (id) => document.getElementById(id);
const categoryOrder = ["Popular", "Speed", "Distance", "Timer", "Elevation", "Navigation", "MTB Performance", "Graphical", "Other", "Cadence", "Heart Rate", "Power", "Cycling Dynamics", "Gears", "Lights", "Workouts", "Indoor Trainer", "eBike"];

function currentScreen(){ return state.screens[state.screenIndex] || null; }
function currentOption(screen, count){ return screen?.layoutOptions.find(o => o.count === count); }
function variantsFor(screen, count){ return currentOption(screen, count)?.variants || []; }
function activeVariant(screen){
  const options = variantsFor(screen, screen.count);
  return options.find(v => v.value === screen.variant) || options[0] || {value:0,label:"A",grid:[]};
}
function fieldName(id){ return state.catalog.find(f => f.id === id)?.name || `ID ${id}`; }
function setDirty(value=true){
  state.dirty = value;
  if(value) state.prepared = false;
  $("dirtyState").querySelector("b").textContent = value ? "Unexported changes" : "Profile loaded";
  $("dirtyState").querySelector("span").style.background = value ? "#d2a341" : "#8eaa68";
  $("saveMessage").textContent = value ? "Preview changes" : "Ready to edit";
  updateInstallButton();
}
function updateInstallButton(){
  const button=$("installButton");
  if(button){
    // The server performs the authoritative mount/profile check immediately
    // before writing. Do not let a stale or failed 5-second poll strand a
    // successfully prepared profile behind a disabled button.
    button.disabled=!state.prepared;
    button.title=state.prepared ? "Install the prepared Road profile on the Garmin" : "Prepare changes first";
  }
}
function showToast(message, error=false){
  const toast = $("toast"); toast.textContent = message; toast.classList.toggle("error", error); toast.classList.add("show");
  clearTimeout(showToast.timer); showToast.timer = setTimeout(() => toast.classList.remove("show"), 3000);
}
async function api(url, options={}){
  const response = await fetch(url, options);
  const data = await response.json().catch(() => ({}));
  if(!response.ok) throw new Error(data.error || `Error ${response.status}`);
  return data;
}
function activateWorkspace(data){
  state.filename = data.filename; state.screens = data.screens.filter(s => s.editable); state.screenIndex = 0; state.original = structuredClone(state.screens); state.selectedField = 0; state.prepared = false;
  if(!state.screens.length) throw new Error("This profile has no editable data screens.");
  $("welcome").classList.add("hidden"); $("workspace").classList.remove("hidden"); $("fileName").textContent = state.filename; $("downloadButton").disabled = false;
  setDirty(false); render();
}
async function openDevice(){
  try{ showToast("Reading Road profile…"); activateWorkspace(await api("/api/open-device", {method:"POST"})); showToast("Road profile loaded."); }
  catch(error){ showToast(error.message, true); }
}
async function openFile(file){
  if(!file) return;
  const form = new FormData(); form.append("file", file);
  try{ showToast("Opening FIT profile…"); activateWorkspace(await api("/api/open", {method:"POST", body:form})); showToast("Profile loaded."); }
  catch(error){ showToast(error.message, true); }
}
async function checkDeviceStatus(){
  if(document.hidden) return;
  try{
    const data=await api("/api/device-status",{cache:"no-store"});
    const status=$("deviceStatus"), label=$("deviceStatusText");
    const openButtons=[$("openDevice"),$("welcomeDevice")];
    const ready=data.connected && data.profileAvailable;
    state.deviceReady=ready;
    if(ready){
      status.dataset.state="connected"; label.textContent="Garmin connected · Road profile ready";
    }else if(data.connected){
      status.dataset.state="profile-missing"; label.textContent="Garmin connected · Road profile not found";
    }else{
      status.dataset.state="disconnected"; label.textContent="Garmin not connected";
    }
    openButtons.forEach(button=>button.disabled=!ready);
    updateInstallButton();
  }catch(_error){
    state.deviceReady=false;
    $("deviceStatus").dataset.state="unavailable";
    $("deviceStatusText").textContent="Connection status unavailable";
    $("openDevice").disabled=true; $("welcomeDevice").disabled=true;
    updateInstallButton();
  }
}
function render(){
  const screen = currentScreen(); if(!screen) return;
  $("pageCounter").textContent = `${state.screenIndex+1} / ${state.screens.length}`;
  $("screenTitle").textContent = screen.type;
  $("screenSubtitle").textContent = `Slot ${screen.slot} · ${screen.enabled ? "active" : "hidden"}`;
  $("previousPage").disabled = state.screenIndex === 0;
  $("nextPage").disabled = state.screenIndex === state.screens.length-1;
  $("fieldCount").value = screen.count;
  const variants = variantsFor(screen, screen.count);
  $("layoutControl").style.visibility = variants.length > 1 ? "visible" : "hidden";
  document.querySelectorAll(".segmented button").forEach(button => button.classList.toggle("active", Number(button.dataset.variant) === screen.variant));
  renderGrid(screen); renderFieldPicker();
}
function previewValue(field){
  const name=field.name.toLocaleLowerCase("en");
  if(name.startsWith("time in ")) return "00:00:00";
  if(name.includes("avg speed")) return "00.0 km/h";
  if(name.includes("speed")) return "00 km/h";
  if(name.includes("cadence")) return "000 rpm";
  if(name.includes("%") || name.includes("balance") || name.includes("effectiveness") || name.includes("smoothness")) return "00%";
  if(name.includes("heart rate")) return "000 bpm";
  if(name.includes("zone")) return "Zone 0";
  if(/time|duration|eta|sunrise|sunset/.test(name)) return "00:00:00";
  if(name.includes("distance") || name.includes("odometer")) return "00.0 km";
  if(name.includes("temperature")) return "00 °C";
  if(name.includes("vam")) return "000 m/h";
  if(name.includes("elevation") || name.includes("ascent") || name.includes("descent")) return "000 m";
  if(name.includes("kilojoule")) return "000 kJ";
  if(name.includes("calorie")) return "000 kcal";
  if(name.includes("battery")) return "00%";
  if(name.includes("power")) return "000 W";
  if(name.includes("heading")) return "000°";
  if(name.includes("gear combo")) return "00 × 00";
  if(name.includes("gear ratio")) return "0.0";
  if(name.includes("front gear") || name.includes("rear gear")) return "00";
  return "00";
}
function renderGrid(screen){
  const grid = $("dataGrid"), layout = activeVariant(screen), variants = variantsFor(screen, screen.count); grid.replaceChildren(); grid.style.gridTemplateRows = `repeat(${Math.max(layout.grid.length,1)}, minmax(0,1fr))`;
  layout.grid.forEach((row, rowIndex) => row.forEach((fieldIndex) => {
    const entry = screen.fields[fieldIndex];
    const cell = document.createElement("button"); cell.type = "button";
    cell.className = `data-cell ${row.length === 1 ? "full" : "half"}${entry ? "" : " empty"}${state.selectedField === fieldIndex ? " selected" : ""}${screen.count === 3 && screen.variant === 1 && fieldIndex === 0 ? " top-small" : ""}`;
    const label = document.createElement("span"); label.className = "cell-label"; label.textContent = entry ? entry.name : "Choose field";
    const value = document.createElement("strong"); value.className = "cell-value";
    const sample = entry ? previewValue(entry) : "+";
    const parts = entry && !sample.includes("×") ? sample.match(/^(\d+(?:[.,]\d+)?)(\s*(?:km\/h|rpm|bpm|°C|m\/h|m|kcal|kJ|W|°|%))$/i) : null;
    if(parts){
      const number = document.createElement("span"); number.className = "cell-number"; number.textContent = parts[1];
      const unit = document.createElement("span"); unit.className = "cell-unit"; unit.textContent = parts[2];
      value.append(number, unit);
    } else value.textContent = sample;
    cell.append(label, value); cell.setAttribute("aria-label", `Field ${fieldIndex+1}: ${entry?.name || "empty"}`);
    cell.addEventListener("click", () => { state.selectedField = fieldIndex; render(); $("fieldSearch").focus(); });
    grid.append(cell);
  }));
  $("layoutCaption").textContent = variants.length > 1 ? `Layout ${activeVariant(screen).label} · click a cell to choose its field` : "Click a cell to choose its field";
  $("pickerTitle").textContent = state.selectedField == null ? "Choose a cell" : `Field ${state.selectedField+1}`;
  $("selectedNumber").textContent = state.selectedField == null ? "—" : String(state.selectedField+1).padStart(2,"0");
}
function renderCategories(){
  const row = $("categoryRow"); row.replaceChildren();
  const cats = ["All", ...categoryOrder.filter(c => state.catalog.some(f => f.category === c))];
  cats.forEach(category => { const button = document.createElement("button"); button.className = `category-chip${state.category===category?" active":""}`; button.textContent = category; button.addEventListener("click",()=>{state.category=category;$("fieldList").scrollTop=0;renderCategories();renderFieldPicker();}); row.append(button); });
}
function renderFieldPicker(){
  const list = $("fieldList"); list.replaceChildren();
  const query = $("fieldSearch").value.trim().toLocaleLowerCase("en");
  const fields = state.catalog.filter(f => (state.category === "All" || f.category === state.category) && (!query || `${f.name} ${f.category} ${f.id}`.toLocaleLowerCase("en").includes(query)));
  if(state.selectedField == null){ list.innerHTML = '<div class="empty-state">Select a cell on the display, then choose a field here.</div>'; return; }
  if(!fields.length){ list.innerHTML = '<div class="empty-state">No matching fields.</div>'; return; }
  const screen = currentScreen(), selectedId = screen.fields[state.selectedField]?.id;
  fields.forEach(field => {
    const button = document.createElement("button"); button.type = "button"; button.className = `field-row${selectedId===field.id?" selected":""}`;
    const id=document.createElement("span"); id.className="field-id"; id.textContent=field.id;
    const title=document.createElement("span"); title.className="field-title"; title.textContent=field.name;
    const category=document.createElement("span"); category.className="field-category"; category.textContent=field.category;
    const check=document.createElement("span"); check.className="field-check"; check.textContent="✓";
    button.append(id,title,category,check); button.addEventListener("click",()=>assignField(field)); list.append(button);
  });
}
function assignField(field){
  const screen=currentScreen(); if(!screen || state.selectedField==null) return;
  screen.fields[state.selectedField]={id:field.id,name:field.name}; setDirty(); render();
}
function changeCount(next){
  const screen=currentScreen(); if(!screen) return;
  const count=Math.max(1,Math.min(10,Number(next)||1)); if(count===screen.count) return;
  const old=screen.fields.slice(0,count); while(old.length<count) old.push(null); screen.fields=old; screen.count=count;
  const variants=variantsFor(screen,count); if(!variants.some(v=>v.value===screen.variant)) screen.variant=variants[0]?.value??0;
  state.selectedField=screen.fields.findIndex(f=>!f); if(state.selectedField<0) state.selectedField=0;
  setDirty(); render();
}
async function saveChanges(){
  const missing=state.screens.flatMap(screen=>screen.fields.map((field,index)=>field?null:`${screen.type}, campo ${index+1}`).filter(Boolean));
  if(missing.length){ showToast(`Choose fields for: ${missing.slice(0,3).join(" · ")}`,true); return; }
  const screens=state.screens.map(s=>({slot:s.slot,count:s.count,variant:s.variant,fieldIds:s.fields.map(f=>f.id)}));
  $("saveButton").disabled=true; $("saveMessage").textContent="Validating and preparing FIT…";
  try{
    const data=await api("/api/save",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({screens})});
    activateWorkspace(data);
    state.prepared=true;
    await checkDeviceStatus();
    updateInstallButton();
    showToast(state.deviceReady ? "Changes prepared. Ready to install on Garmin." : "Changes prepared. Connect the Garmin to enable installation.");
  }
  catch(error){ showToast(error.message,true); $("saveMessage").textContent="Preview changes"; }
  finally{ $("saveButton").disabled=false; }
}
async function reloadState(){
  try{ activateWorkspace(await api("/api/state")); showToast("Changes discarded."); }
  catch(error){ showToast(error.message,true); }
}
function download(){ window.location.href="/api/download"; }
function confirmInstall(){
  const dialog=$("installDialog");
  $("installDialogFilename").textContent=state.filename;
  dialog.showModal();
  return new Promise(resolve=>dialog.addEventListener("close",()=>resolve(dialog.returnValue==="install"),{once:true}));
}
async function installOnGarmin(){
  if(!state.prepared) return;
  const accepted=await confirmInstall();
  if(!accepted) return;
  const button=$("installButton"); button.disabled=true; button.textContent="Installing…";
  try{
    const data=await api("/api/install",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({confirm:true})});
    state.prepared=false; updateInstallButton();
    showToast(`Queued in NewFiles. Backup: ${data.backup}. Safely eject and restart the Edge.`);
  }catch(error){
    showToast(error.message,true);
  }finally{
    button.textContent="Install on Garmin"; updateInstallButton();
  }
}
function initialize(){
  $("installDialog").addEventListener("click",event=>{if(event.target===$("installDialog")) $("installDialog").close("cancel");});
  $("openDevice").addEventListener("click",openDevice); $("welcomeDevice").addEventListener("click",openDevice);
  checkDeviceStatus(); window.setInterval(checkDeviceStatus,5000);
  document.addEventListener("visibilitychange",()=>{if(!document.hidden) checkDeviceStatus();});
  $("fitFile").addEventListener("change",event=>openFile(event.target.files[0]));
  $("previousPage").addEventListener("click",()=>{if(state.screenIndex>0){state.screenIndex--;state.selectedField=0;render();}});
  $("nextPage").addEventListener("click",()=>{if(state.screenIndex<state.screens.length-1){state.screenIndex++;state.selectedField=0;render();}});
  $("countDown").addEventListener("click",()=>changeCount(currentScreen()?.count-1)); $("countUp").addEventListener("click",()=>changeCount(currentScreen()?.count+1));
  $("fieldCount").addEventListener("change",event=>changeCount(event.target.value));
  document.querySelectorAll(".segmented button").forEach(button=>button.addEventListener("click",()=>{const screen=currentScreen();if(!screen)return;const value=Number(button.dataset.variant);if(variantsFor(screen,screen.count).some(v=>v.value===value)){screen.variant=value;setDirty();render();}}));
  $("fieldSearch").addEventListener("input",()=>{$("fieldList").scrollTop=0;renderFieldPicker();}); $("saveButton").addEventListener("click",saveChanges); $("reloadButton").addEventListener("click",reloadState); $("downloadButton").addEventListener("click",download); $("installButton").addEventListener("click",installOnGarmin);
  api("/api/catalog").then(data=>{state.catalog=data;renderCategories();renderFieldPicker();}).catch(error=>showToast(error.message,true));
  const params=new URLSearchParams(location.search); if(params.get("device")==="1") openDevice();
}
document.addEventListener("DOMContentLoaded",initialize);
