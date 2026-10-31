export function ErrorBanner({ message = "Something went wrong" }) {
  return (
    <div
      data-testid="error-banner"
      role="alert"
      className="flex items-center gap-2 rounded-card border border-danger bg-bg-surface px-4 py-3 text-danger font-ui"
    >
      <span aria-hidden="true">⚠</span>
      <span>{message}</span>
    </div>
  );
}
