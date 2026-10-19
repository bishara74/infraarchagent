import '@testing-library/jest-dom/vitest';
import { cleanup } from '@testing-library/react';
import {hydratePreferences} from '../lib/preferences';
import { afterEach, vi } from 'vitest';

afterEach(()=>{cleanup();if(typeof window!=='undefined'){localStorage.clear();void hydratePreferences(null);}});

if (typeof window !== 'undefined') Object.defineProperty(window, 'scrollTo', { value: vi.fn(), configurable: true });
