import { useCallback, useEffect, useRef, useState, type FormEvent } from 'react';
import { ArrowRight, CircleCheck, Link2, Pause, Plus, RefreshCw, ShieldCheck, ShoppingBag, TriangleAlert, Unplug } from 'lucide-react';
import { api, ApiError, type Grant } from '../api';
import { EmptyState, ErrorNotice } from '../components/ui';
import { When } from '../components/When';

interface Connection {
  id: string; shop_domain: string; country: string; auth_mode: 'client_credentials' | 'offline_token';
  status: string; shop_name: string | null; currency: string | null; timezone: string | null;
  scopes: string[]; last_success_at: string | null; last_error: string | null; revision: number;
}
interface Job { id: string; state: string; produced_raw_count: number; error_code: string | null; params: { stream?: string } }

export function Channels({ workspace, csrf, grants, preview, onSessionExpired }: {
  workspace: string; csrf: string; grants: Grant[]; preview: boolean; onSessionExpired: () => void;
}) {
  const [connections, setConnections] = useState<Connection[]>([]);
  const [jobs, setJobs] = useState<Record<string, Job[]>>({});
  const [demo, setDemo] = useState(false);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(!preview);
  const [busy, setBusy] = useState('');
  const [notice, setNotice] = useState('');
  const [adding, setAdding] = useState(false);
  const priorJobs = useRef<Record<string, string>>({});
  const canManage = grants.some(g => ['*', 'connectors.manage'].includes(g.function_code) && g.product_scope === '*');
  const headers = { 'X-Workspace-Id': workspace, 'X-CSRF-Token': csrf };

  const reload = useCallback(async (signal?: AbortSignal) => {
    if (preview || !canManage) { setLoading(false); return; }
    try {
      const result = await api<{ connections: Connection[]; demo_mode: boolean }>('/connectors/shopify', {
        headers: { 'X-Workspace-Id': workspace }, signal,
      });
      if (signal?.aborted) return;
      setConnections(result.connections); setDemo(result.demo_mode);
    } catch (err) {
      if (signal?.aborted) return;
      if (err instanceof ApiError && err.status === 401) onSessionExpired();
      else setError(err instanceof Error ? err.message : 'Could not load connections.');
    } finally { if (!signal?.aborted) setLoading(false); }
  }, [workspace, preview, canManage, onSessionExpired]);

  useEffect(() => {
    const abort = new AbortController();
    void reload(abort.signal);
    return () => abort.abort();
  }, [reload]);

  useEffect(() => {
    if (preview || !connections.length) return;
    const abort = new AbortController();
    let timer: ReturnType<typeof setTimeout>;
    async function poll() {
      const results = await Promise.allSettled(connections.map(async c => {
        const data = await api<{ jobs: Job[] }>(`/connectors/shopify/${c.id}/jobs`, {
          headers: { 'X-Workspace-Id': workspace }, signal: abort.signal,
        });
        return [c.id, data.jobs] as const;
      }));
      if (abort.signal.aborted) return;
      const next: Record<string, Job[]> = {};
      for (const result of results) {
        if (result.status === 'fulfilled') next[result.value[0]] = result.value[1];
        else if (result.reason instanceof ApiError && result.reason.status === 401) { onSessionExpired(); return; }
        else setError('Sync status could not be refreshed. Check the API and reload connections.');
      }
      setJobs(next);
      let completed = false;
      for (const [id, records] of Object.entries(next)) {
        const state = records[0]?.state ?? '';
        if (['queued', 'running'].includes(priorJobs.current[id]) && !['queued', 'running'].includes(state)) completed = true;
        priorJobs.current[id] = state;
      }
      if (completed) void reload();
      timer = setTimeout(() => void poll(), 5000);
    }
    void poll();
    return () => { abort.abort(); clearTimeout(timer); };
  }, [connections, workspace, preview, onSessionExpired, reload]);

  async function add(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = event.currentTarget, values = new FormData(form);
    setBusy('new'); setError(''); setNotice('');
    try {
      await api('/connectors/shopify', { method: 'POST', headers, body: JSON.stringify({
        shop_domain: String(values.get('domain')).trim().toLowerCase(),
        country: String(values.get('country')).trim().toUpperCase(), auth_mode: values.get('auth_mode'),
      }) });
      form.reset(); setAdding(false); setNotice('Store saved. Run its credential setup command, then verify the connection.');
      await reload();
    } catch (err) { setError(err instanceof Error ? err.message : 'Could not add the store.'); }
    finally { setBusy(''); }
  }

  async function action(c: Connection, name: 'check' | 'sync' | 'paused' | 'disconnected' | 'pending_auth') {
    if (busy) return;
    setBusy(c.id); setError(''); setNotice('');
    try {
      if (name === 'check' || name === 'sync') {
        await api(`/connectors/shopify/${c.id}/${name}`, { method: 'POST', headers, timeoutMs: 60000 });
        setNotice(name === 'check' ? 'Shopify access verified. You can now run a sync.' : 'Sync queued. Progress appears on this store card.');
      } else {
        await api(`/connectors/shopify/${c.id}/state`, { method: 'POST', headers,
          body: JSON.stringify({ status: name, revision: c.revision }) });
        setNotice(name === 'disconnected' ? 'Local credentials removed and sync disabled. To revoke access at Shopify, uninstall the dedicated app.' : 'Connection status updated.');
      }
      await reload();
    } catch (err) {
      if (err instanceof ApiError && err.status === 401) onSessionExpired();
      else setError(err instanceof Error ? err.message : 'Connection action failed.');
    } finally { setBusy(''); }
  }

  const disabled = preview || demo || !!busy;
  return <><div className="page-heading"><div><span className="eyebrow">SALES CHANNELS</span><h1>Shopify connections</h1><p>Each store has its own access, currency, timezone and sync history.</p></div><button className="primary-button" disabled={disabled || !canManage} onClick={() => setAdding(!adding)}><Plus size={17} />Add store</button></div>
    <div className="quality-bar"><ShieldCheck size={18} /><strong>Read-only integration</strong><span>No customer names, emails or addresses imported</span></div>
    {error && <ErrorNotice message={error} retry={() => { setError(''); void reload(); }} />}
    {notice && <div className="connection-notice" role="status"><CircleCheck size={18} />{notice}</div>}
    {preview ? <EmptyState title="Connect your stores after signing in" detail="You can add all five stores here. Preview does not access Shopify or save connections." />
      : !canManage ? <EmptyState title="Connection management access required" detail="Choose your local integration workspace, or ask your administrator for connectors.manage access." />
      : <>{demo && <div className="error-notice"><TriangleAlert size={18} /><span>This demo workspace is read only. Run the local integration workspace setup command, refresh, and choose that workspace.</span></div>}
        {adding && <section className="panel connection-form"><h2>Add a Shopify store</h2><form onSubmit={add}><label>Store domain<input name="domain" placeholder="store-name.myshopify.com" required maxLength={80} pattern="[A-Za-z0-9-]+\.myshopify\.com" /></label><label>Store country (two-letter code)<input name="country" placeholder="IN, GB, US, FR, DE…" pattern="[A-Za-z]{2}" maxLength={2} required /></label><label>Authentication method<select name="auth_mode" required defaultValue=""><option value="" disabled>Choose an authentication method</option><option value="client_credentials">App and store in the same Shopify organization</option><option value="offline_token">Installed app with an offline Admin API token</option></select></label><p className="tiny">Client credentials require an app installed on a store in the same organization. For other merchants, obtain an offline token through approved OAuth installation. Secrets are configured in your terminal.</p><div className="inline-actions"><button className="primary-button" disabled={disabled}>Save store <ArrowRight size={16} /></button><button className="secondary-button" type="button" onClick={() => setAdding(false)}>Cancel</button></div></form></section>}
        {loading ? <p role="status">Loading connections…</p> : !connections.length ? <EmptyState title="Add your first Shopify store" detail="Install a dedicated app with read_orders, read_products, read_inventory and read_locations permissions, then add its store domain here." />
          : <div className="connection-grid">{connections.map(c => {
            const job = jobs[c.id]?.[0];
            const running = job && ['queued', 'running'].includes(job.state);
            return <section className="panel connection-card" key={c.id} aria-labelledby={`store-${c.id}`}><div className="connection-card-heading"><ShoppingBag size={24} /><div><h2 id={`store-${c.id}`}>{c.shop_name || c.shop_domain}</h2><p>{c.shop_domain}</p></div><span className="outline-badge">{c.status === 'connected' ? <CircleCheck size={14} /> : <TriangleAlert size={14} />}{c.status.replaceAll('_', ' ')}</span></div><dl><dt>Country / currency</dt><dd>{c.country} / {c.currency ?? 'Not verified'}</dd><dt>Timezone</dt><dd>{c.timezone ?? 'Not verified'}</dd><dt>Last complete sync</dt><dd><When value={c.last_success_at} tz={c.timezone ?? 'UTC'} /></dd><dt>Order window</dt><dd>Last 60 days · raw import</dd><dt>Authentication</dt><dd>{c.auth_mode === 'client_credentials' ? 'Client credentials' : 'Offline token'}</dd></dl>
              <div className="credential-instructions"><strong>Backend credential setup</strong><code>uv run python scripts/setup_shopify_credentials.py {c.id}</code><p className="tiny">Run from the project root. Inputs are hidden and saved encrypted locally.</p></div>
              {c.last_error && <p className="connection-error">Connection issue: {c.last_error}</p>}
              {job && <div className="job-status" role="status"><strong>Latest sync: {job.state}</strong><span>{job.produced_raw_count} new or changed raw records{job.params.stream ? ` · ${job.params.stream}` : ''}</span>{job.error_code && <span>{job.error_code} · Existing imported records are retained.</span>}</div>}
              <div className="connection-actions"><button className="secondary-button" disabled={disabled || running || c.status === 'paused' || c.status === 'disconnected'} onClick={() => void action(c, 'check')}><Link2 size={16} />{busy === c.id ? 'Please wait…' : 'Verify connection'}</button><button className="primary-button" disabled={disabled || running || c.status !== 'connected'} onClick={() => void action(c, 'sync')}><RefreshCw size={16} />{running ? 'Sync in progress' : 'Sync now'}</button><button className="text-button" disabled={disabled} onClick={() => void action(c, c.status === 'paused' || c.status === 'disconnected' ? 'pending_auth' : 'paused')}><Pause size={15} />{c.status === 'paused' || c.status === 'disconnected' ? 'Re-enable' : 'Pause'}</button><button className="text-button" disabled={disabled || c.status === 'disconnected'} onClick={() => void action(c, 'disconnected')}><Unplug size={15} />Disconnect locally</button></div></section>;
          })}</div>}
      </>}
    <div className="info-note"><TriangleAlert size={18} /><span>Manual sync imports products, variants, inventory and recent order records. Profit reporting, fees, full refund accounting, older-order backfills and automatic webhook updates are not implemented yet.</span></div>
    {!preview && canManage && <button className="text-button" onClick={() => void reload()} disabled={!!busy}><RefreshCw size={16} />Refresh connections</button>}
  </>;
}
