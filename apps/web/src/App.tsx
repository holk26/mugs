import { useEffect, useState } from 'react';
import {
  Link,
  Outlet,
  RouterProvider,
  createRootRoute,
  createRoute,
  createRouter,
} from '@tanstack/react-router';
import Header from './components/Header';
import Footer from './components/Footer';
import ProductCard from './components/ProductCard';
import ProductDetail from './components/ProductDetail';
import CartDrawer from './components/CartDrawer';
import CheckoutForm from './components/CheckoutForm';
import ClearCart from './components/ClearCart';
import { getProduct, listProducts, type Product } from './lib/api';

function Shell() {
  return (
    <div className="flex min-h-screen flex-col">
      <Header />
      <main className="flex-1">
        <Outlet />
      </main>
      <Footer />
    </div>
  );
}

function ProductsGrid() {
  const [products, setProducts] = useState<Product[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    let active = true;
    listProducts()
      .then(({ results }) => {
        if (!active) return;
        setProducts(results);
      })
      .catch((err) => {
        if (!active) return;
        setError(err instanceof Error ? err.message : 'Unable to load products');
      })
      .finally(() => {
        if (!active) return;
        setLoading(false);
      });
    return () => {
      active = false;
    };
  }, []);

  if (loading) {
    return <p className="mt-10 text-sm text-stone-500">Loading products...</p>;
  }

  if (error) {
    return <p className="mt-10 text-sm text-red-600">{error}</p>;
  }

  return (
    <div className="mt-10 grid gap-8 sm:grid-cols-2 lg:grid-cols-3">
      {products.map((product) => (
        <ProductCard key={product.id} product={product} />
      ))}
    </div>
  );
}

function HomePage() {
  return (
    <>
      <section className="px-4 py-20 text-center md:py-28">
        <div className="section">
          <div className="mx-auto max-w-3xl rounded-3xl border border-orange-100/70 bg-white/70 px-6 py-12 shadow-lg shadow-orange-100/60 backdrop-blur-sm md:px-10">
            <p className="text-sm font-semibold tracking-widest text-orange-600">Unique designs for lasting memories</p>
            <h1 className="mt-4 text-4xl font-semibold tracking-tight text-stone-900 md:text-6xl">
              Turn little drawings into lasting memories
            </h1>
            <p className="mt-6 text-lg leading-relaxed text-stone-600 md:text-xl">
              Upload your child's artwork and we will print it on a beautiful ceramic mug.
            </p>
            <div className="mt-10 flex flex-wrap items-center justify-center gap-4">
              <Link to="/products" className="btn-primary inline-flex">Shop mugs</Link>
              <a href="#how-it-works" className="btn-secondary inline-flex">How it works</a>
            </div>
          </div>
        </div>
      </section>

      <section className="section py-16 md:py-24">
        <div className="flex items-end justify-between">
          <div>
            <h2 className="text-2xl font-semibold tracking-tight text-stone-900 md:text-3xl">Our mugs</h2>
            <p className="mt-2 text-stone-500">Personalized with your child's own drawing.</p>
          </div>
          <Link to="/products" className="hidden text-sm font-medium text-orange-700 hover:underline md:block">
            View all
          </Link>
        </div>
        <ProductsGrid />
      </section>

      <section id="how-it-works" className="border-t border-orange-100/80 bg-gradient-to-br from-orange-50/70 via-amber-50/70 to-white px-4 py-16">
        <div className="section">
          <div className="grid gap-8 md:grid-cols-3">
            <div className="rounded-2xl bg-white p-6 shadow-sm">
              <p className="text-sm font-semibold uppercase tracking-wider text-orange-700">01</p>
              <h3 className="mt-3 text-lg font-semibold text-stone-900">Upload a drawing</h3>
              <p className="mt-2 text-sm leading-relaxed text-stone-500">
                Take a photo or scan your child's artwork and upload it on any product page.
              </p>
            </div>
            <div className="rounded-2xl bg-white p-6 shadow-sm">
              <p className="text-sm font-semibold uppercase tracking-wider text-orange-700">02</p>
              <h3 className="mt-3 text-lg font-semibold text-stone-900">We digitize it</h3>
              <p className="mt-2 text-sm leading-relaxed text-stone-500">
                Our team cleans the lines and prepares the image for a crisp ceramic print.
              </p>
            </div>
            <div className="rounded-2xl bg-white p-6 shadow-sm">
              <p className="text-sm font-semibold uppercase tracking-wider text-orange-700">03</p>
              <h3 className="mt-3 text-lg font-semibold text-stone-900">Shipped to you</h3>
              <p className="mt-2 text-sm leading-relaxed text-stone-500">
                The finished mug is packed with care and sent straight to your door.
              </p>
            </div>
          </div>
        </div>
      </section>
    </>
  );
}

function ProductsPage() {
  return (
    <section className="section py-12 md:py-20">
      <h1 className="text-3xl font-semibold tracking-tight text-stone-900 md:text-4xl">Shop mugs</h1>
      <p className="mt-3 text-lg text-stone-500">Personalized with your child's own drawing.</p>
      <ProductsGrid />
    </section>
  );
}

function ProductPage() {
  const { handle } = productRoute.useParams();
  const [product, setProduct] = useState<Product | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    let active = true;
    getProduct(handle)
      .then((value) => {
        if (!active) return;
        setProduct(value);
      })
      .catch((err) => {
        if (!active) return;
        setError(err instanceof Error ? err.message : 'Unable to load product');
      })
      .finally(() => {
        if (!active) return;
        setLoading(false);
      });

    return () => {
      active = false;
    };
  }, [handle]);

  if (loading) {
    return <section className="section py-12 md:py-20"><p className="text-sm text-stone-500">Loading product...</p></section>;
  }

  if (error || !product) {
    return <section className="section py-12 md:py-20"><p className="text-sm text-red-600">{error || 'Product not found'}</p></section>;
  }

  return <ProductDetail product={product} />;
}

function CartPage() {
  return (
    <section className="section py-12 md:py-20">
      <h1 className="text-3xl font-semibold tracking-tight text-stone-900 md:text-4xl">Your cart</h1>
      <div className="mt-8 max-w-2xl rounded-3xl border border-stone-100 bg-white p-6 shadow-sm md:p-8">
        <CartDrawer isOpen={true} onClose={() => {}} inline />
      </div>
    </section>
  );
}

function CheckoutPage() {
  return <CheckoutForm />;
}

function ThanksPage() {
  const search = thanksRoute.useSearch();

  return (
    <>
      {search.order && <ClearCart />}
      <section className="section py-24 text-center md:py-32">
        <div className="mx-auto max-w-xl">
          <h1 className="text-3xl font-semibold tracking-tight text-stone-900 md:text-4xl">
            Thank you for your order!
          </h1>
          <p className="mt-6 text-lg leading-relaxed text-stone-600">
            We will carefully digitize the drawing and send you updates by email.
          </p>
          {search.order && (
            <p className="mt-4 text-sm text-stone-500">
              Order reference: <span className="font-medium text-stone-900">{search.order}</span>
            </p>
          )}
          <Link to="/products" className="btn-primary mt-10 inline-flex">
            Continue shopping
          </Link>
        </div>
      </section>
    </>
  );
}

const rootRoute = createRootRoute({ component: Shell });

const indexRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/',
  component: HomePage,
});

const productsRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/products',
  component: ProductsPage,
});

const productRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/products/$handle',
  component: ProductPage,
});

const cartRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/cart',
  component: CartPage,
});

const checkoutRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/checkout',
  component: CheckoutPage,
});

const thanksRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/thanks',
  validateSearch: (search: Record<string, unknown>) => ({
    order: typeof search.order === 'string' ? search.order : undefined,
  }),
  component: ThanksPage,
});

const routeTree = rootRoute.addChildren([
  indexRoute,
  productsRoute,
  productRoute,
  cartRoute,
  checkoutRoute,
  thanksRoute,
]);

const router = createRouter({ routeTree });

declare module '@tanstack/react-router' {
  interface Register {
    router: typeof router;
  }
}

export function App() {
  return <RouterProvider router={router} />;
}
