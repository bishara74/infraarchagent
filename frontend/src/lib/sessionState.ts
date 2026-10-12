const keyName = 'infraarch.apiKey';
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
export const getApiKey = () => read(keyName);
export const setApiKey = (key: string | null) => write(keyName, key);
export const getActiveRun = () => read(runName);
export const setActiveRun = (run: string | null) => write(runName, run);
export const subscribeSession = (listener: () => void) => {
  listeners.add(listener);
  return () => { listeners.delete(listener); };
};
