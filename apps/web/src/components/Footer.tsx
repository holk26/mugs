export default function Footer() {
  return (
    <footer className="border-t border-neutral-200 bg-neutral-50">
      <div className="mx-auto max-w-6xl px-4 py-12">
        <p className="text-sm text-neutral-500">
          &copy; {new Date().getFullYear()} Recuerdo Momentos. Made for little artists and big hearts.
        </p>
      </div>
    </footer>
  );
}
