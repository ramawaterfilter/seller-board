import { useEffect, useRef, useState, type FormEvent } from 'react';
import { ArrowLeft, ArrowRight, Eye, EyeOff, ShieldCheck } from 'lucide-react';
import { api, type Challenge } from '../api';
import { Brand, ErrorNotice, ThemeButton } from '../components/ui';

export function Login({ onAuthenticated, preview, theme, toggleTheme }: {
  onAuthenticated: () => Promise<void>; preview: () => void; theme: string; toggleTheme: () => void;
}) {
  const [challenge, setChallenge] = useState<Challenge | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const codeInput = useRef<HTMLInputElement>(null);
  useEffect(() => { if (challenge) codeInput.current?.focus(); }, [challenge]);

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (busy) return;
    const form = event.currentTarget;
    const values = new FormData(form);
    setBusy(true); setError('');
    try {
      if (challenge) {
        await api('/auth/mfa/verify', { method: 'POST', body: JSON.stringify({
          challenge_id: challenge.challenge_id, code: values.get('code'),
        }) });
        form.reset();
        await onAuthenticated();
      } else {
        const next = await api<Challenge | { status: 'authenticated' }>('/auth/login', { method: 'POST', body: JSON.stringify({
          email: String(values.get('email')).trim(), password: values.get('password'), method: 'totp',
        }) });
        form.reset();
        if ('status' in next && next.status === 'authenticated') await onAuthenticated();
        else if ('challenge_id' in next) setChallenge(next);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Sign in could not be completed.');
      if (challenge) { form.reset(); codeInput.current?.focus(); }
    } finally { setBusy(false); }
  }

  return <div className="auth-page"><header className="auth-header"><Brand /><ThemeButton theme={theme} toggle={toggleTheme} /></header>
    <main className="auth-main" id="main"><div className="auth-intro"><span className="eyebrow">ONE CLEAR VIEW OF YOUR BUSINESS</span>
      <h1>Know where your<br /><span>profit comes from.</span></h1>
      <p>Bring your channels, costs and operations into one workspace. Make decisions with the full picture.</p>
      <div className="channel-labels"><span>Amazon</span><span>Shopify</span><span>B2B</span></div>
      <div className="auth-footnote"><ShieldCheck size={18} /><span>Private workspace · Secure sign in</span></div>
    </div><section className="auth-card" aria-labelledby="login-title"><div className="auth-card-icon"><ShieldCheck size={25} /></div>
      <span className="eyebrow">YOUR WORKSPACE AWAITS</span><h2 id="login-title">{challenge ? 'Verify it’s you' : 'Welcome back'}</h2>
      <p>{challenge ? 'Enter the six-digit code from your authenticator. This request expires after five minutes.' : 'Sign in to Rama Commerce Intelligence.'}</p>
      {error && <ErrorNotice message={error} />}
      <form onSubmit={submit} aria-busy={busy}>
        {challenge ? <label>Authenticator code<input ref={codeInput} name="code" inputMode="numeric" autoComplete="one-time-code" pattern="[0-9]{6}" minLength={6} maxLength={6} required placeholder="000000" className="otp-input" /></label>
          : <><label>Email address<input name="email" type="email" autoComplete="username" required maxLength={254} placeholder="you@example.com" /></label>
            <label>Password<span className="password-field"><input name="password" type={showPassword ? 'text' : 'password'} autoComplete="current-password" required maxLength={1024} />
              <button type="button" className="icon-button" aria-label={showPassword ? 'Hide password' : 'Show password'} onClick={() => setShowPassword(!showPassword)}>{showPassword ? <EyeOff size={18} /> : <Eye size={18} />}</button></span></label></>}
        <button className="primary-button" type="submit" disabled={busy}>{busy ? 'Please wait…' : challenge ? 'Verify and sign in' : 'Continue'}<ArrowRight size={18} /></button>
        {challenge && <button type="button" className="text-button back-button" disabled={busy} onClick={() => { setChallenge(null); setError(''); }}><ArrowLeft size={16} />Back to sign in</button>}
      </form>
      <div className="auth-help">{challenge ? 'Email verification is not configured locally.' : 'Local setup: use the account created by the initialization script.'}</div>
      <button className="preview-button" onClick={preview} disabled={busy}>Preview the interface <ArrowRight size={16} /></button>
      <p className="tiny">Preview has no account access or business data.</p>
    </section></main><footer className="auth-footer">Rama Commerce Intelligence <span>Local development · Foundation release</span></footer></div>;
}
