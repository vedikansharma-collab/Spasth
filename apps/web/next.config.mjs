/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  transpilePackages: ['@policy-estimator/types', '@policy-estimator/schemas'],
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: 'http://localhost:4000/api/:path*',
      },
      {
        source: '/storage/:path*',
        destination: 'http://localhost:4000/storage/:path*',
      },
    ];
  },
};

export default nextConfig;
