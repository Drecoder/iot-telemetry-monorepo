import app from './app.js';

const PORT = process.env.PORT || 3000;

// Force Express to bind directly to the networking interface
const server = app.listen(Number(PORT), '0.0.0.0', () => {
    console.log("========================================");
    console.log(`🚀 TELEMETRY INGESTOR RUNNING ON PORT ${PORT}`);
    console.log(`Env: ${process.env.NODE_ENV || 'development'}`);
    console.log(`Stream Endpoint: ${process.env.STREAM_ENDPOINT || 'AWS Native'}`);
    console.log("========================================");
});

// Handle graceful shutdowns when Kubernetes sends a termination signal
process.on('SIGTERM', () => {
    console.log('SIGTERM signal received: closing HTTP server');
    server.close(() => {
        console.log('HTTP server closed cleanly.');
        process.exit(0);
    });
});