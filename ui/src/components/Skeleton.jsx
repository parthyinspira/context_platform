export function Skeleton({ shape = "row", count = 1 }) {
  const shapeClass =
    shape === "block" ? "h-20 w-full rounded-card" : "h-4 w-full rounded-control";
  return (
    <div data-testid="skeleton" aria-hidden="true" className="flex flex-col gap-2">
      {Array.from({ length: count }, (_, i) => (
        <div
          key={i}
          data-testid="skeleton-item"
          className={`motion-safe:animate-pulse bg-border-subtle ${shapeClass}`}
        />
      ))}
    </div>
  );
}
