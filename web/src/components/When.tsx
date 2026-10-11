export function When({ value, tz }: { value: string | null; tz: string }) {
  if (!value) return <span>Not yet</span>;
  const date = new Date(value);
  if (!Number.isFinite(date.getTime())) return <span>Unavailable</span>;
  try {
    return <time dateTime={value} title={`${value} · ${tz}`}>{new Intl.DateTimeFormat('en', {
      dateStyle: 'medium', timeStyle: 'short', timeZone: tz,
    }).format(date)}</time>;
  } catch { return <time dateTime={value}>{value}</time>; }
}
