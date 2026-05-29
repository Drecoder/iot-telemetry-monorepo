import request from 'supertest';
import { KinesisClient, PutRecordCommand } from "@aws-sdk/client-kinesis";
import app from './app'; // Importing the refactored express instance from app.ts

// Mock the Kinesis Client (The Subject Event Bus Broker)
const mockKinesisSend = jest.fn();
jest.mock("@aws-sdk/client-kinesis", () => {
    return {
        KinesisClient: jest.fn().mockImplementation(() => ({
            send: (...args: any[]) => mockKinesisSend(...args) // Deferred execution bypasses initialization order blocks
        })),
        PutRecordCommand: jest.fn().mockImplementation((args) => args)
    };
});

describe('Telemetry API - Subject Ingestion Endpoint Unit Tests', () => {
    
    beforeEach(() => {
        jest.clearAllMocks();
    });

    it('should validate an inbound robot payload, stream it to Kinesis, and return a 202 Accepted', async () => {
        // Arrange: Simulate a successful asynchronous write metadata return from AWS Kinesis
        mockKinesisSend.mockResolvedValueOnce({ SequenceNumber: "496612345678901234567" });

        const validPayload = {
            robotId: "robot-xl-01",
            timestamp: 1716984000,
            latitude: 41.8781,
            longitude: -87.6298,
            metrics: { 
                speed: 12.5, 
                batteryLevel: 88, 
                cpuTemperature: 42 
            }
        };

        // Act: Invoke the endpoint via supertest agent
        const response = await request(app)
            .post('/api/v1/telemetry')
            .send(validPayload);

        // Assert: Verify HTTP non-blocking API specifications match design requirements
        expect(response.status).toBe(202);
        expect(response.body.status).toBe("Accepted");
        expect(response.body).toHaveProperty("eventId");

        // Assert: Verify the publisher hand-off interaction with the event broker
        expect(mockKinesisSend).toHaveBeenCalledTimes(1);
        
        const executedCommandArgs = mockKinesisSend.mock.calls[0][0];
        expect(executedCommandArgs.StreamName).toBe("cnh-telemetry-stream");
        expect(executedCommandArgs.PartitionKey).toBe("robot-xl-01"); // Sharded cleanly via identity fields

        // Assert: Verify internal wrapper structures match our shared event schema schemas
        const streamedEnvelope = JSON.parse(Buffer.from(executedCommandArgs.Data).toString('utf-8'));
        expect(streamedEnvelope.eventType).toBe("TELEMETRY_RECEIVED");
        expect(streamedEnvelope.eventId).toBe(response.body.eventId);
        expect(streamedEnvelope.data).toMatchObject(validPayload);
    });

    it('should reject edge payloads missing invariant identification mappings with a 400', async () => {
        const invalidPayload = {
            latitude: 41.8781,
            longitude: -87.6298
            // Missing robotId, timestamp, and metrics fields completely
        };

        const response = await request(app)
            .post('/api/v1/telemetry')
            .send(invalidPayload);

        // Assert: API Gate intercepts payload anomalies before triggering brokers
        expect(response.status).toBe(400);
        expect(response.body.error).toBe("Bad Request");
        expect(response.body.message).toContain("Missing required telemetry fields");
        expect(mockKinesisSend).not.toHaveBeenCalled();
    });

    it('should return a 500 error if the Kinesis event bus stream encounters an infrastructure failure', async () => {
        // Arrange: Simulate broker-side connection pool timeouts or stream capacity exceptions
        mockKinesisSend.mockRejectedValueOnce(new Error("Kinesis Stream KMSAccessDeniedException"));

        const validPayload = {
            robotId: "robot-xl-01",
            timestamp: 1716984000,
            metrics: { speed: 0, batteryLevel: 100, cpuTemperature: 35 }
        };

        // Act: Send request
        const response = await request(app)
            .post('/api/v1/telemetry')
            .send(validPayload);

        // Assert: System gracefully flags internal subsystem blockages
        expect(response.status).toBe(500);
        expect(response.body.error).toBe("Internal Server Error");
        expect(response.body.message).toContain("Failed to stream ingestion packet downstream.");
    });
});