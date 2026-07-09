export default function Footer() {
  return (
    <footer className="mt-auto">
      <div className="bg-earth py-14 text-cream">
        <div className="section">
          <div className="flex flex-col items-start justify-between gap-6 md:flex-row md:items-center">
            <div>
              <p className="font-serif text-2xl">Join our community</p>
              <p className="mt-1 text-sm text-cream/70">
                Get early access to new designs and a little inspiration in your inbox.
              </p>
            </div>
            <form className="flex w-full gap-2 md:w-auto" onSubmit={(e) => e.preventDefault()}>
              <input
                type="email"
                placeholder="your@email.com"
                className="flex-1 rounded-full border border-cream/20 bg-cream/10 px-4 py-2.5 text-sm text-cream placeholder:text-cream/50 outline-none transition focus:border-clay md:w-64"
              />
              <button className="rounded-full bg-cream px-5 py-2.5 text-sm font-semibold text-earth transition hover:bg-sand">
                Subscribe
              </button>
            </form>
          </div>
        </div>
      </div>

      <div className="bg-cream py-12">
        <div className="section">
          <div className="grid gap-10 sm:grid-cols-2 lg:grid-cols-4">
            <div>
              <p className="font-serif text-lg text-earth">Recuerdo Momentos</p>
              <p className="mt-3 text-sm leading-relaxed text-stone">
                Custom ceramic mugs printed with children's drawings. A keepsake for every little artist.
              </p>
            </div>
            <div>
              <p className="text-sm font-semibold text-earth">Shop</p>
              <ul className="mt-3 space-y-2 text-sm text-stone">
                <li>
                  <a href="/products" className="transition hover:text-earth">
                    All mugs
                  </a>
                </li>
                <li>
                  <a href="/cart" className="transition hover:text-earth">
                    Cart
                  </a>
                </li>
              </ul>
            </div>
            <div>
              <p className="text-sm font-semibold text-earth">Company</p>
              <ul className="mt-3 space-y-2 text-sm text-stone">
                <li>
                  <a href="#how-it-works" className="transition hover:text-earth">
                    How it works
                  </a>
                </li>
                <li>
                  <a href="/" className="transition hover:text-earth">
                    About
                  </a>
                </li>
              </ul>
            </div>
            <div>
              <p className="text-sm font-semibold text-earth">Stay in touch</p>
              <p className="mt-2 text-sm text-stone">
                Questions? Email us at{' '}
                <a href="mailto:hello@recuerdomomentos.com" className="text-earth underline underline-offset-4">
                  hello@recuerdomomentos.com
                </a>
              </p>
            </div>
          </div>
          <div className="mt-12 border-t border-earth/10 pt-6 text-sm text-stone">
            © {new Date().getFullYear()} Recuerdo Momentos. All rights reserved.
          </div>
        </div>
      </div>
    </footer>
  );
}
