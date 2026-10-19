export interface SessionStatus {auth_required:boolean;authenticated:boolean;mode:'local'|'shared_key';message?:string}
let auth:SessionStatus|null=null;
export const getSessionStatus=()=>auth;
export function setSessionStatus(value:SessionStatus|null){auth=value;listeners.forEach(listener=>listener());}
try{window.sessionStorage.removeItem('infraarch.apiKey');}catch{/* Storage may be disabled. */}
const runName = 'infraarch.activeRun';
const listeners = new Set<() => void>();

function read(name: string): string | null {
  try { return window.sessionStorage.getItem(name); } catch { return null; }
}
function write(name: string, value: string | null) {
  try {
    if (value) window.sessionStorage.setItem(name, value);
    else window.sessionStorage.removeItem(name);
  } catch { /* Storage may be disabled; never fall back to persistent storage. */ }
  listeners.forEach(listener => listener());
}
export const getActiveRun = () => read(runName);
export const setActiveRun = (run: string | null) => write(runName, run);
export const subscribeSession = (listener: () => void) => {
  listeners.add(listener);
  return () => { listeners.delete(listener); };
};
