import { useEffect, useRef, useState } from 'react';
import { ArrowLeft, ArrowRight, CalendarDays, ChartNoAxesCombined, ChevronDown, CircleHelp, Database, Filter, Layers3, Search, TriangleAlert, X } from 'lucide-react';
import { EmptyState } from '../components/ui';

const periods = ['Today', 'Yesterday', 'Month to date', 'This month (forecast)', 'Last month'];
const metrics = ['Sales', 'Orders / Units', 'Refunds & returns', 'Advertising cost', 'Gross profit', 'Net profit'];
const views = ['Tiles', 'Chart', 'P&L', 'Map', 'Trends'];

export function Dashboard() {
  const [channel, setChannel] = useState('All channels');
  const [period, setPeriod] = useState('Month to date');
  const [view, setView] = useState('Tiles');
  const [tableView, setTableView] = useState('Products');
  const [search, setSearch] = useState('');
  const [lineage, setLineage] = useState('');
  const dialog = useRef<HTMLDialogElement>(null);
  const tiles = useRef<HTMLDivElement>(null);
  useEffect(() => {
    if (lineage) dialog.current?.showModal();
  }, [lineage]);
  function closeDrawer() { dialog.current?.close(); setLineage(''); }

  return <><div className="page-heading"><div><span className="eyebrow">BUSINESS OVERVIEW</span><h1>Profit dashboard</h1><p>Your performance across every sales channel.</p></div><span className="outline-badge"><Layers3 size={15} />Unified view</span></div>
    <section className="filters" aria-label="Dashboard filters"><div className="channel-chips" role="group" aria-label="Sales channels">{['All channels', 'Amazon', 'Shopify', 'B2B'].map(c => <button key={c} aria-pressed={channel === c} onClick={() => setChannel(c)}>{c}</button>)}</div>
      <div className="filter-actions"><label className="period-select"><CalendarDays size={17} /><span className="sr-only">Reporting period</span><select value={period} onChange={e => setPeriod(e.target.value)}>{periods.map(p => <option key={p}>{p}</option>)}</select></label><button className="secondary-button" disabled><Filter size={16} />Filters</button></div></section>
    <div className="quality-bar"><TriangleAlert size={18} /><strong>No reporting data</strong><span>Sources not connected</span><span>COGS unavailable</span><button className="text-button" onClick={() => setLineage('Data quality')}>Data quality <ArrowRight size={14} /></button></div>
    <div className="view-tabs" role="group" aria-label="Dashboard view">{views.map(v => <button key={v} onClick={() => setView(v)} aria-pressed={view === v}>{v}</button>)}</div>
    {view === 'Tiles' && <div className="tile-navigation"><span>Period overview</span><div className="inline-actions"><button className="icon-button" aria-label="Scroll to previous period" onClick={() => tiles.current?.scrollBy({ left: -272 })}><ArrowLeft size={17} /></button><button className="icon-button" aria-label="Scroll to next period" onClick={() => tiles.current?.scrollBy({ left: 272 })}><ArrowRight size={17} /></button></div></div>}
    {view === 'Tiles' ? <div className="tile-grid" ref={tiles}>{periods.map(p => <section className={`period-tile ${p === period ? 'selected-period' : ''}`} key={p} aria-label={`${p} profit metrics`}><div className="tile-heading"><h2>{p}</h2>{p.includes('forecast') ? <span className="metric-flag">Estimate</span> : <span className="metric-flag">Missing</span>}</div>
      <div className="tile-metrics">{metrics.map(metric => <div className={`metric ${metric === 'Net profit' ? 'net-profit' : ''}`} key={metric}><span>{metric}</span><strong aria-label={`${metric}: data unavailable`}>—</strong></div>)}</div>
      <button className="tile-more" onClick={() => setLineage(`${p} · ${channel}`)}>More details<ChevronDown size={16} /></button></section>)}</div>
      : <section className="panel visualization-empty"><ChartNoAxesCombined size={30} /><EmptyState title={`${view} data is not available yet`} detail={`${period} · ${channel}. This view will use server-calculated reporting data when its API is built.`} /></section>}
    <section className="panel data-table"><div className="table-toolbar"><div className="table-tabs" role="group" aria-label="Record type">{['Products', 'Order Items'].map(t => <button key={t} aria-pressed={tableView === t} onClick={() => setTableView(t)}>{t}</button>)}</div><label className="search-field"><Search size={17} /><span className="sr-only">Search {tableView.toLowerCase()}</span><input placeholder={`Search ${tableView.toLowerCase()}…`} value={search} onChange={e => setSearch(e.target.value)} /></label></div>
      <div className="table-scroll"><table><caption className="sr-only">{tableView} for {channel} in {period}</caption><thead><tr>{[tableView === 'Products' ? 'Product' : 'Order item', 'Channel', 'Units', 'Returns', 'Sales', 'Ads', 'Gross profit', 'Net profit', 'Margin'].map((col, index) => <th key={col} scope="col" className={index > 1 ? 'numeric' : ''}>{col}</th>)}</tr></thead><tbody><tr><td colSpan={9}><EmptyState title={search ? 'No searchable records yet' : `No ${tableView.toLowerCase()} to display`} detail="Channel ingestion and the reporting API are still being built. Financial values will remain missing until source data is available." /></td></tr></tbody></table></div>
      <div className="table-footer"><span>No source records loaded</span><span>{channel} · {period}</span></div></section>
    <div className="info-note"><CircleHelp size={17} /><span>Amounts, margins and channel totals will come from the API. This interface performs no financial calculations.</span></div>
    <dialog ref={dialog} className="lineage-dialog" onClose={() => setLineage('')} onClick={e => { if (e.target === e.currentTarget) closeDrawer(); }} aria-labelledby="lineage-title"><div className="drawer-header"><span className="eyebrow">PROVENANCE & COMPLETENESS</span><button className="icon-button" onClick={closeDrawer} aria-label="Close details"><X size={21} /></button></div><h2 id="lineage-title">{lineage}</h2><p className="muted">Understand the source behind each number.</p><div className="drawer-status"><TriangleAlert size={19} /><strong>Missing · No reporting API</strong></div><dl><dt>Sources</dt><dd>Not connected</dd><dt>Last sync</dt><dd>Unavailable</dd><dt>Calculation status</dt><dd>Not computed</dd><dt>Reporting currency & timezone</dt><dd>Pending workspace configuration</dd></dl><div className="info-note"><Database size={19} /><span>Source records, calculation versions and reconciliation flags will appear here when ingestion and reporting are implemented.</span></div><button className="secondary-button" onClick={closeDrawer}>Close details</button></dialog>
  </>;
}
