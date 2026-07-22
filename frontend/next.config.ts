import type { NextConfig } from "next";

/**
 * Same-origin proxy to `ontowiz-serve` (added by D1.0).
 *
 * WHY: the backend ships no CORS middleware — `OPTIONS /v1/context` returns 405 and no
 * `Access-Control-Allow-Origin` header is sent — so a browser cannot call it cross-origin
 * at all. Rather than have the FE depend on a BE server-config change, the browser talks
 * to a same-origin path and Next proxies it server-side. This also keeps the backend
 * origin OUT of the client bundle: `NEXT_PUBLIC_*` values are inlined at BUILD time, so a
 * baked absolute URL cannot be changed at deploy time. `ONTOWIZ_API_ORIGIN` is a plain
 * server-side var, read per request.
 *
 * Set `NEXT_PUBLIC_ONTOWIZ_API_URL=/api/ontowiz` to route the client through this proxy.
 */
const ONTOWIZ_API_ORIGIN =
  process.env.ONTOWIZ_API_ORIGIN ?? "http://127.0.0.1:8080";

const nextConfig: NextConfig = {
  async rewrites() {
    return [
      {
        source: "/api/ontowiz/:path*",
        destination: `${ONTOWIZ_API_ORIGIN}/:path*`,
      },
    ];
  },
};

export default nextConfig;
