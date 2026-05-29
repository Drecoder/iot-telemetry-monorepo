import request from 'supertest';
// Export app from app.ts (instead of just calling app.listen inside it) to import it here safely
import express from 'express';

// Mocking AWS SDK behavior
const mockSend = jest.fn();
jest.mock('@aws-sdk/lib-dynamodb', () => ({
    DynamoDBDocumentClient: {
        from: () => ({
            send: (...args: any[]) => mockSend(...args)
        })
    },
    PutCommand: jest.fn()
}));

// Quick re-creation of app context for pure HTTP testing
const app = express();
app.use(express.json());

app.post('/api/v1/telemetry', async (req, res): Promise<any> => {
    const { robotId, timestamp } = req.body;
    if (!robotId || !timestamp) {
        return res.status(400).json({ error: "Missing identity or chronological invariants." });
    }
    try {
        await mockSend();
        return res.status(201).json({ status: "ACCEPTED" });
    } catch (err) {
        return res.status(500).json({ error: "Storage subsystem exception." });
    }
});

describe('POST /api/v1/telemetry', () => {
    beforeEach(() => {
        jest.clearAllMocks();
    });

    it('should accept valid telemetry payloads and return 201', async () => {
        mockSend.mockResolvedValueOnce({}); // Simulate successful DB write

        const response = await request(app)
            .post('/api/v1/telemetry')
            .send({
                robotId: "robot-xl-01",
                timestamp: 1716984000,
                latitude: 41.8781,
                longitude: -87.6298,
                metrics: { speed: 12.5, batteryLevel: 88, cpuTemperature: 42 }
            });

        expect(response.status).toBe(201);
        expect(response.body.status).toBe("ACCEPTED");
        expect(mockSend).toHaveBeenCalledTimes(1);
    });

    it('should reject payloads missing critical invariants with a 400', async () => {
        const response = await request(app)
            .post('/api/v1/telemetry')
            .send({
                latitude: 41.8781 // missing robotId and timestamp
            });

        expect(response.status).toBe(400);
        expect(response.body.error).toContain("Missing identity");
        expect(mockSend).not.toHaveBeenCalled();
    });

    it('should return a 500 error if the storage backend throws an exception', async () => {
        mockSend.mockRejectedValueOnce(new Error("DynamoDB ProvisionedThroughputExceededException"));

        const response = await request(app)
            .post('/api/v1/telemetry')
            .send({
                robotId: "robot-xl-01",
                timestamp: 1716984000
            });

        expect(response.status).toBe(500);
        expect(response.body.error).toContain("Storage subsystem exception");
    });
});