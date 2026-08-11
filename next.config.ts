import type { NextConfig } from "next";

const isDevelopment = process.env.NODE_ENV === "development";

const nextConfig: NextConfig = {
  turbopack: {
    root: __dirname,
  },
  images: {
    unoptimized: true,
  },
  async headers() {
    return [{
      source: "/(.*)",
      headers: [
        { key: "X-Content-Type-Options", value: "nosniff" },
        { key: "Referrer-Policy", value: "strict-origin-when-cross-origin" },
        { key: "X-Frame-Options", value: "DENY" },
        { key: "Permissions-Policy", value: "camera=(), microphone=(), geolocation=(), payment=()" },
        {
          key: "Content-Security-Policy",
          value: `default-src 'self'; base-uri 'self'; frame-ancestors 'none'; form-action 'self'; object-src 'none'; img-src 'self' data: https:; connect-src 'self' https:; style-src 'self' 'unsafe-inline'; script-src 'self' 'unsafe-inline'${isDevelopment ? " 'unsafe-eval'" : ""}`,
        },
      ],
    }];
  },
};

export default nextConfig;
