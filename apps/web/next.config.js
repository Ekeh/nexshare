/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  // The app never uses next/image (every image is a plain <img> — see
  // no-img-element lint warnings), so Next's built-in Image Optimization
  // API route is dead weight we get zero benefit from. Disabling it closes
  // off a critical, unauthenticated RCE (GHSA-2xp9-vwfh-vxw4, AVIF-related)
  // that has no fix within the 14.x line — the real patch requires
  // Next 15.5.24+/16.x, a major upgrade out of scope here.
  images: { unoptimized: true },
  async rewrites() {
    const apiUrl = process.env.API_URL || "http://localhost:8000";
    return [
      { source: "/api/:path*", destination: `${apiUrl}/api/:path*` },
      { source: "/uploads/:path*", destination: `${apiUrl}/uploads/:path*` },
    ];
  },
};

module.exports = nextConfig;
