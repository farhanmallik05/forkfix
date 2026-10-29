/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  async rewrites() {
    return [
      {
        source: "/api/:path*",
        // Keep browser calls same-origin. Configure FORKFIX_BACKEND_URL on
        // hosted deployments; Docker Compose points this at the backend
        // service while local development defaults to localhost.
        destination: `${process.env.FORKFIX_BACKEND_URL || "http://localhost:8000"}/api/:path*`,
      },
    ]
  },
}

module.exports = nextConfig
