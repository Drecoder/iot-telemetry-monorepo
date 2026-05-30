import { processRecords } from "./index";
import { DynamoDBDocumentClient, PutCommand } from "@aws-sdk/lib-dynamodb";

// Mock the AWS DynamoDB Document Client
jest.mock("@aws-sdk/lib-dynamodb", () => {
  const mockSend = jest.fn();
  return {
    DynamoDBDocumentClient: {
      from: () => ({
        send: mockSend,
      }),
    },
    PutCommand: jest.fn().mockImplementation((args) => args),
  };
});

describe("Storage Observer - Record Processor", () => {
  let mockSend: jest.Mock;

  beforeEach(() => {
    jest.clearAllMocks();
    // Grab our mocked send function to spy on assertions
    const client = DynamoDBDocumentClient.from({} as any);
    mockSend = client.send as jest.Mock;
  });

  it("should successfully decode an inbound stream event and write it to DynamoDB", async () => {
    // 1. Mock a standard Kinesis event wrapper containing our TelemetryEvent
    const sampleEvent = {
      eventId: "test-uuid-1234",
      eventType: "TELEMETRY_RECEIVED",
      emittedAt: "2026-05-29T11:00:00.000Z",
      data: {
        robotId: "tractor-77",
        timestamp: "2026-05-29T11:00:00.000Z",
        metrics: { speed: 12, engineTemp: 95 },
      },
    };

    // Kinesis encodes payloads in Base64
    const base64Payload = Buffer.from(JSON.stringify(sampleEvent)).toString(
      "base64",
    );

    const mockKinesisRecords = [
      {
        kinesis: {
          data: base64Payload,
        },
      },
    ];

    // 2. Execute the Observer logic
    await processRecords(mockKinesisRecords);

    // 3. Assertions
    expect(mockSend).toHaveBeenCalledTimes(1);

    // Check that PutCommand was called with the correctly mapped DynamoDB parameters
    const executedCommandArgs = mockSend.mock.calls[0][0];
    expect(executedCommandArgs.TableName).toBe("DynamoDB-Telemetry-Table");
    expect(executedCommandArgs.Item).toMatchObject({
      RobotId: "tractor-77",
      EventId: "test-uuid-1234",
      Metrics: { speed: 12, engineTemp: 95 },
    });
  });

 it("should catch and log errors gracefully when parsing invalid payloads", async () => {
  // 1. Setup an intentionally broken payload structure
  const invalidRecords = [{ kinesis: { data: "not-valid-base64-json" } }];

  // 2. Assert that the function handles the internal JSON panic internally without throwing
  await expect(processRecords(invalidRecords)).resolves.not.toThrow();

  // 3. Assert that the invalid payload never caused a database write payload downstream
  expect(mockSend).not.toHaveBeenCalled();
});
});
