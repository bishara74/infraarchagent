export type IconName = 'circuit-board' | 'gear' | 'account' | 'chevron-down' | 'chevron-up' | 'zap' | 'check' | 'loading' | 'history' | 'terminal' | 'watch' | 'credit-card' | 'dashboard' | 'shield' | 'folder' | 'file' | 'cloud-download' | 'arrow-left' | 'search' | 'sign-out' | 'key' | 'person-add' | 'person' | 'trash' | 'lock' | 'close' | 'eye' | 'eye-closed';

/** Decorative glyph: the surrounding button/link/text supplies the accessible name. */
export function Icon({ name, spin = false }: { name: IconName; spin?: boolean }) {
  return <span aria-hidden="true" className={`icon codicon codicon-${name}${spin ? ' icon-spin' : ''}`} />;
}
