export default function DashboardLoading() {
  return (
    <div className="p-6 animate-pulse">
      <div className="h-7 w-48 bg-border rounded mb-2" />
      <div className="h-4 w-32 bg-border/60 rounded mb-8" />
      <div className="space-y-3">
        <div className="h-24 bg-border/40 rounded-lg" />
        <div className="h-24 bg-border/40 rounded-lg" />
        <div className="h-24 bg-border/40 rounded-lg" />
      </div>
    </div>
  );
}
