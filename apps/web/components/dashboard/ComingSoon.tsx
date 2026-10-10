export function ComingSoon({ title }: { title: string }) {
  return (
    <div>
      <h1 className="text-2xl font-extrabold text-navy-900">{title}</h1>
      <div className="mt-6 flex h-64 items-center justify-center rounded-2xl border-2 border-dashed border-navy-100 bg-white text-sm font-medium text-navy-300">
        Coming soon
      </div>
    </div>
  );
}
