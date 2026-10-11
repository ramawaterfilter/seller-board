import { useCallback, useEffect, useState } from 'react';
import { ArrowRight, Bell, Building2, ChevronRight, CircleHelp, Database, LayoutDashboard, LogOut, Package, Settings, ShieldCheck, ShoppingBag, Wallet } from 'lucide-react';
import { api, ApiError, type Grant, type Identity } from './api';
import { Brand, EmptyState, ErrorNotice, ThemeButton } from './components/ui';
import { Login } from './pages/Login';
import { Dashboard } from './pages/Dashboard';
import { Channels } from './pages/Channels';

export function App() {
  const [identity, setIdentity] = useState<Identity | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [preview, setPreview] = useState(false);
  const [path, setPath] = useState(window.location.pathname);
  const [workspace, setWorkspace] = useState('');
  const [grants, setGrants] = useState<Grant[] | null>(null);
  const [grantError, setGrantError] = useState('');
  const [grantAttempt, setGrantAttempt] = useState(0);
  const [signingOut, setSigningOut] = useState(false);
  const [theme, setTheme] = useState(() => {
    try { return localStorage.getItem('rci-theme') === 'light' ? 'light' : 'dark'; } catch { return 'dark'; }
  });
  useEffect(() => {
    document.documentElement.dataset.theme = theme;
    try { localStorage.setItem('rci-theme', theme); } catch { /* Preference storage is optional. */ }
  }, [theme]);
  useEffect(() => {
    const changed = () => setPath(window.location.pathname);
    window.addEventListener('popstate', changed);
    return () => window.removeEventListener('popstate', changed);
  }, []);
  function navigate(next: string) { window.history.pushState(null, '', next); setPath(next); }

  async function restoreSession(signal?: AbortSignal) {
    setLoading(true); setError('');
    try { setIdentity(await api<Identity>('/me', { signal })); }
    catch (err) {
      if (signal?.aborted) return;
      setIdentity(null);
      if (!(err instanceof ApiError && err.status === 401)) setError(err instanceof Error ? err.message : 'Unable to load your session.');
    } finally { if (!signal?.aborted) setLoading(false); }
  }
  useEffect(() => {
    const controller = new AbortController();
    void restoreSession(controller.signal);
    return () => controller.abort();
  }, []);

  useEffect(() => {
    setGrants(null); setGrantError('');
    if (!identity || !workspace || preview) return;
    const controller = new AbortController();
    api<{ grants: Grant[] }>('/auth/permissions', {
      headers: { 'X-Workspace-Id': workspace }, signal: controller.signal,
    }).then(result => setGrants(result.grants)).catch(err => {
      if (controller.signal.aborted) return;
      if (err instanceof ApiError && err.status === 401) { setIdentity(null); setWorkspace(''); }
      else setGrantError(err instanceof Error ? err.message : 'Unable to load permissions.');
    });
    return () => controller.abort();
  }, [identity, workspace, preview, grantAttempt]);

  async function authenticated() {
    setIdentity(await api<Identity>('/me'));
    setWorkspace(''); setPreview(false); navigate('/workspaces');
  }
  async function logout() {
    if (preview) { setPreview(false); navigate('/auth/login'); return; }
    if (!identity || signingOut) return;
    setSigningOut(true); setError('');
    try {
      await api('/auth/logout', { method: 'POST', headers: { 'X-CSRF-Token': identity.csrf_token } });
      setIdentity(null); setWorkspace(''); navigate('/auth/login');
    } catch (err) {
      if (err instanceof ApiError && err.status === 401) { setIdentity(null); setWorkspace(''); }
      else setError(err instanceof Error ? err.message : 'Sign out failed. Please try again.');
    } finally { setSigningOut(false); }
  }
  const expireSession = useCallback(() => {
    setIdentity(null); setWorkspace('');
    window.history.replaceState(null, '', '/auth/login'); setPath('/auth/login');
  }, []);
  const toggleTheme = () => setTheme(theme === 'dark' ? 'light' : 'dark');
  const themeButton = <ThemeButton theme={theme} toggle={toggleTheme} />;

  if (loading) return <main className="loading-page" aria-busy="true"><Brand /><p role="status">Loading your workspace…</p></main>;
  if (!identity && !preview) return <>{error && <div className="connection-banner"><ErrorNotice message={error} retry={() => void restoreSession()} /></div>}
    <Login onAuthenticated={authenticated} preview={() => { setPreview(true); setError(''); navigate('/dashboard'); }} theme={theme} toggleTheme={toggleTheme} /></>;

  const workspaceIndex = identity?.workspace_ids.indexOf(workspace) ?? -1;
  if (!preview && (!workspace || path === '/workspaces')) return <div className="workspace-page"><header className="auth-header"><Brand /><div className="inline-actions">{themeButton}<button className="text-button" onClick={() => void logout()} disabled={signingOut}><LogOut size={17} />Sign out</button></div></header>
    <main className="workspace-main" id="main"><span className="eyebrow">YOUR BUSINESS, ORGANIZED</span><h1>Choose a workspace</h1><p>Select where you’d like to work. Only your assigned workspaces appear here.</p>
      {error && <ErrorNotice message={error} />}
      <div className="workspace-list">{identity?.workspace_ids.map((id, index) => <button className="workspace-card" key={id} onClick={() => { setWorkspace(id); navigate('/dashboard'); }}><span className="workspace-icon"><Building2 size={26} /></span><span><strong>{identity.workspaces?.find(w => w.id === id)?.name ?? `Workspace ${index + 1}`}</strong><span className="workspace-id">{id}</span></span><ArrowRight size={21} /></button>)}</div>
      {!identity?.workspace_ids.length && <EmptyState title="No workspace assigned" detail="Ask your administrator to assign workspace access. Invitations and role management are still being built." />}
      <p className="tiny">Demo workspaces are read only. Use your integration workspace to configure stores.</p>
    </main></div>;

  const settings = path === '/settings';
  const channels = path === '/settings/connectors';
  const canReadProfit = preview || grants?.some(g => g.function_code === 'profit.read');
  return <div className="app-shell"><a className="skip-link" href="#main">Skip to content</a>
    <aside className="sidebar"><Brand /><span className="nav-caption">WORKSPACE</span><nav aria-label="Main navigation">
      <button onClick={() => navigate('/dashboard')} className={!settings && !channels ? 'nav-item active' : 'nav-item'}><LayoutDashboard size={19} />Profit<span className="nav-dot" /></button>
      <button className="nav-item" disabled><Package size={19} />Inventory<span className="soon">Soon</span></button>
      <button className="nav-item" disabled><Wallet size={19} />Money Back<span className="soon">Soon</span></button>
      <button className="nav-item" disabled><Bell size={19} />Alerts<span className="soon">Soon</span></button>
      <span className="nav-caption">OPERATIONS</span>
      <button onClick={() => navigate('/settings/connectors')} className={channels ? 'nav-item active' : 'nav-item'}><ShoppingBag size={19} />Channels</button>
      <button className="nav-item" disabled><Building2 size={19} />B2B<span className="soon">Soon</span></button>
      <button onClick={() => navigate('/settings')} className={settings ? 'nav-item active' : 'nav-item'}><Settings size={19} />Settings</button>
    </nav><div className="sidebar-bottom"><div className="foundation-label"><ShieldCheck size={18} /><span>Foundation release<small>Local development</small></span></div></div></aside>
    <div className="app-body"><header className="topbar"><div className="breadcrumb"><span>Workspace</span><ChevronRight size={14} /><strong>{channels ? 'Channels' : settings ? 'Settings' : 'Profit'}</strong></div>
      <div className="inline-actions">{!preview && <button className="workspace-switch" onClick={() => navigate('/workspaces')}><Building2 size={16} /><span>{identity?.workspaces?.find(w => w.id === workspace)?.name ?? `Workspace ${workspaceIndex + 1}`}</span></button>}{themeButton}<button className="icon-button" onClick={() => void logout()} disabled={signingOut} aria-label={preview ? 'Exit preview' : 'Sign out'}><LogOut size={19} /></button></div></header>
      <main className="main-content" id="main"><div className="release-banner"><ShieldCheck size={17} /><span>{preview ? 'Interface preview · No account access or business data' : 'Foundation release · Reporting APIs and channel connections are not built yet'}</span>{preview && <button className="text-button" onClick={() => void logout()}>Sign in <ArrowRight size={14} /></button>}</div>
        {error && <ErrorNotice message={error} />}
        {!preview && grantError ? <ErrorNotice message={grantError} retry={() => setGrantAttempt(grantAttempt + 1)} />
          : !preview && !grants ? <p role="status" className="panel loading-panel">Loading workspace permissions…</p>
          : channels ? <Channels key={workspace} workspace={workspace} csrf={identity?.csrf_token ?? ''} grants={grants ?? []} preview={preview} onSessionExpired={expireSession} />
          : settings ? <><div className="page-heading"><div><span className="eyebrow">WORKSPACE SETTINGS</span><h1>Access & permissions</h1><p>Your active access in this workspace.</p></div></div><section className="panel settings-panel"><h2><ShieldCheck size={20} />Session</h2><dl><dt>Signed in as</dt><dd>{preview ? 'Interface preview' : identity?.display_name || identity?.email}</dd><dt>Authentication</dt><dd>{preview ? 'No authenticated session' : identity?.authentication_method === 'password' ? 'Password only (local development)' : 'Password + multi-factor verification'}</dd><dt>Workspace</dt><dd>{preview ? 'No workspace selected' : workspace}</dd></dl></section><section className="panel settings-panel"><h2><Database size={20} />Permission scopes</h2>{preview ? <EmptyState title="Preview only" detail="Sign in to see permissions returned by the API." /> : <div className="table-scroll"><table><caption className="sr-only">Your active permission scopes</caption><thead><tr><th scope="col">Function</th><th scope="col">Products</th><th scope="col">Markets</th></tr></thead><tbody>{grants?.map((g, index) => <tr key={index}><td>{g.function_code}</td><td>{g.product_scope}</td><td>{g.market_scope}</td></tr>)}</tbody></table>{!grants?.length && <p>No active grants.</p>}</div>}<p className="tiny">Role editing and invitations are not available yet. The API enforces access for each request.</p></section></>
          : !canReadProfit ? <EmptyState title="Profit access not assigned" detail="Your workspace does not include profit.read permission. Ask your administrator for access." />
          : <Dashboard />}
        <footer className="app-footer"><span>Rama Commerce Intelligence</span><span><CircleHelp size={14} />Missing data is never shown as zero</span></footer>
      </main>
    </div>
  </div>;
}
