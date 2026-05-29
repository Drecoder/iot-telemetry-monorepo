import express, { Request, Response } from 'express';
import { DynamoDBClient } from "@aws-sdk/client-dynamodb";
import { DynamoDBDocumentClient, PutCommand } from "@aws-sdk/lib-dynamodb";

const app = express();
app.use(express.json());

// Initialize the AWS DynamoDB Client using environment configurations
const client = new DynamoDBClient({ region: process.env.AWS_REGION || "us-east-1" });
const docClient = DynamoDBDocumentClient.from(client);

// Define strict typing for incoming robot IoT telemetry data packet strings
interface TelemetryPayload {
    robotId: string;
    timestamp: number;
    latitude: number;
    longitude: number;
    metrics: {
        speed: number;
        batteryLevel: number;
        cpuTemperature: number;
    };
}

/**
 * Health Check Endpoint
 * Critical for Kubernetes/ECS container lifecycle orchestrators (Liveness/Readiness probes)
 */
app.get('/health', (req: Request, res: Response) => {
    res.status(200).json({ status: "UP", timestamp: new Date().toISOString() });
});

/**
 * Main Telemetry Ingestion Route
 * Receives POST payload metrics streaming from the distributed edge fleet
 */
app.post('/