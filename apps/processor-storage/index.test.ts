import { processRecords } from "./index";
import { DynamoDBDocumentClient, PutCommand } from "@aws-sdk/lib-dynamodb";

// Complete mock implementation simulating AWS Client State
jest.mock("@aws-sdk/lib-dynamodb", () => {
  const mockSend = jest.fn();
  return {
    DynamoDBDocumentClient: {
      from: () => ({
        send: mockSend,
      }),
    },
    PutCommand: jest.fn().mockImplementation((args) => ({ input: args })),
  };
});

describe("Storage Observer - Record Processor", () => {
  let mockSend: jest.Mock;

  beforeEach(() => {
    jest.clearAllMocks();
    const client = DynamoDBDocumentClient.from({} as any);
    mockSend = client.send as jest.Mock;
  });

  it("should successfully decode an inbound stream event and write it to DynamoDB", async () => {
    const samplePayload = {
      robotId: "tractor-77",
      timestamp: 1780327859616,
      latitude: 41.8781,
      longitude: -87.6298,
      metrics: { speed: 12, batteryLevel: 85, cpuTemperature: 42 }
    };

    const base64Payload = Buffer.from(JSON.stringify(samplePayload)).toString("base64");
    const mockKinesisRecords = [
      { kinesis: { data: base64Payload, sequenceNumber: "4965412389100000000001" } } as any
    ];

    mockSend.mockResolvedValueOnce({});

    await processRecords(mockKinesisRecords);

    expect(mockSend).toHaveBeenCalledTimes(1);
    const executedCommandArgs = mockSend.mock.calls[0][0];
    expect(executedCommandArgs.input.TableName).toBe("FleetTelemetry");
    expect(executedCommandArgs.input.Item.robotId).toBe("tractor-77");
  });

  it("should absorb ConditionalCheckFailedException errors silently when handling a duplicate retry", async () => {
    const samplePayload = {
      robotId: "tractor-77",
      timestamp: 1780327859616,
      latitude: 41.8781,
      longitude: -87.6298,
      metrics: { speed: 12, batteryLevel: 85, cpuTemperature: 42 }
    };

    const base64Payload = Buffer.from(JSON.stringify(samplePayload)).toString("base64");
    const mockKinesisRecords = [
      { kinesis: { data: base64Payload, sequenceNumber: "4965412389100000000001" } } as any
    ];

    // Simulate DynamoDB identifying a record collision via our ConditionExpression rule
    const conditionalError = new Error("Conditional check failed");
    conditionalError.name = "ConditionalCheckFailedException";
    mockSend.mockRejectedValueOnce(conditionalError);

    // The handler should safely catch the exception and complete processing without crashing
    await expect(processRecords(mockKinesisRecords)).resolves.not.toThrow();
    expect(mockSend).toHaveBeenCalledTimes(1);
  });

  it("should catch and log errors gracefully when parsing invalid payloads", async () => {
    const invalidRecords = [
      { kinesis: { data: Buffer.from("~bwڱ;(").toString("base64"), sequenceNumber: "4965412389100000000002" } } as any
    ];

    await expect(processRecords(invalidRecords)).resolves.not.toThrow();
    expect(mockSend).not.toHaveBeenCalled();
  });
});