import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';

import App from './App';
import '@fontsource/space-grotesk/latin-400.css';
import '@fontsource/space-grotesk/latin-500.css';
import '@fontsource/space-grotesk/latin-600.css';
import '@fontsource/space-grotesk/latin-700.css';
import '@fontsource/jetbrains-mono/latin-400.css';
import '@fontsource/jetbrains-mono/latin-500.css';
import '@vscode/codicons/dist/codicon.css';
import './styles/tokens.css';
import './styles/global.css';

const root = document.getElementById('root');
if (!root) {
  throw new Error('Application root is missing.');
}

createRoot(root).render(
  <StrictMode>
    <App />
  </StrictMode>,
);
