import express, { Request, Response } from 'express';
import { KinesisClient, PutRecordCommand } from "@aws-sdk/client-kinesis";
import { TelemetryEvent, TelemetryPayload } from "event-schemas";
import crypto from "crypto";

const app = express();
app.use(express.json());

// Initialize the AWS Kinesis Client (The Subject Channel)
const kinesis = new KinesisClient({ region: process.env.AWS_REGION || "us-east-1" });
const STREAM_NAME = process.env.KINESIS_STREAM_NAME || "cnh-telemetry-stream";

/**
 * Health Check Endpoint
 * Critical for Kubernetes/ECS container lifecycle orchestrators (Liveness/Readiness probes)
 */
app.get('/health', (req: Request, res: Response) => {
    res.status(200).json({ status: "UP", timestamp: new Date().toISOString() });
});

/**
 * Main Telemetry Ingestion Route (The Subject Publisher)
 * Receives POST payload metrics streaming from the distributed edge fleet,
 * validates the gate, and hands off to the Kinesis event bus asynchronously.
 */
app.post('/api/v1/telemetry', async (req: Request, res: Response) => {
    const payload = req.body as TelemetryPayload;

    // --- Validation Gate ---
    if (!payload.robotId || !payload.timestamp || !payload.metrics) {
        return res.status(400).json({ 
            error: "Bad Request", 
            message: "Missing required telemetry fields: robotId, timestamp, or metrics." 
        });
    }

    // --- Create standard event wrapper ---
    const event: TelemetryEvent = {
        eventId: crypto.randomUUID(),
        eventType: 'TELEMETRY_RECEIVED',
        emittedAt: new Date().toISOString(),
        data: payload
    };

    try {
        // Asynchronous hand-off to the event broker
        await kinesis.send(new PutRecordCommand({
            StreamName: STREAM_NAME,
            Data: Buffer.from(JSON.stringify(event)),
            // PartitionKey routing keeps matching vehicle sequences ordered within the same stream shard
            PartitionKey: payload.robotId 
        }));

        // Respond non-blocking with 202 Accepted per asynchronous ingestion standards
        return res.status(202).json({ 
            status: "Accepted", 
            eventId: event.eventId 
        });

    } catch (error) {
        console.error("Kinesis stream integration failure:", error);
        return res.status(500).json({ 
            error: "Internal Server Error", 
            message: "Failed to stream ingestion packet downstream." 
        });
    }
});

export default app;