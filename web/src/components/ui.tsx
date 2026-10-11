import { AlertCircle, ArrowRight, Layers3, Moon, Sun } from 'lucide-react';

export function Brand() {
  return <div className="brand"><span className="brand-mark"><Layers3 size={23} /></span>
    <span>rama<span className="brand-sub">COMMERCE INTELLIGENCE</span></span></div>;
}

export function ThemeButton({ theme, toggle }: { theme: string; toggle: () => void }) {
  return <button className="icon-button" onClick={toggle} aria-label={`Switch to ${theme === 'dark' ? 'light' : 'dark'} theme`}>
    {theme === 'dark' ? <Sun size={19} /> : <Moon size={19} />}</button>;
}

export function ErrorNotice({ message, retry }: { message: string; retry?: () => void }) {
  return <div className="error-notice" role="alert"><AlertCircle size={19} />
    <span>{message}</span>{retry && <button className="text-button" onClick={retry}>Try again <ArrowRight size={15} /></button>}</div>;
}

export function EmptyState({ title, detail }: { title: string; detail: string }) {
  return <div className="empty-state"><div className="empty-icon"><Layers3 size={27} /></div>
    <h3>{title}</h3><p>{detail}</p></div>;
}
