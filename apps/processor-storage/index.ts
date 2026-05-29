import { DynamoDBClient } from "@aws-sdk/client-dynamodb";
import { DynamoDBDocumentClient, PutCommand } from "@aws-sdk/lib-dynamodb";
import pino from "pino";

interface TelemetryEvent {
  eventId: string;
  data: {
    deviceId: string;
    timestamp: string;
    metrics: Record<string, any>;
  };
}

const logger = pino({
  level: process.env.LOG_LEVEL || "info",
  formatters: {
    level: (label) => ({ severity: label.toUpperCase() }), // Aligns cleanly with Datadog/CloudWatch standards
  },
});

const ddbClient = new DynamoDBClient({ region: "us-east-1" });
const docClient = DynamoDBDocumentClient.from(ddbClient);

// This function processes batched records polled from your infrastructure stream
export async function processRecords(records: any[]) {
  for (const record of records) {
    let eventId: string | undefined;
    let robotId: string | undefined;
    try {
      // Decode the stream event payload
      const rawData = Buffer.from(record.kinesis.data, 'base64').toString('utf-8');
      const event: TelemetryEvent = JSON.parse(rawData);

      // Write to DynamoDB Table
      eventId = event.eventId;
      robotId = event.data.deviceId;
      
      await docClient.send(new PutCommand({
        TableName: "DynamoDB-Telemetry-Table",
        Item: {
          DeviceId: event.data.deviceId,
          Timestamp: event.data.timestamp,
          EventId: event.eventId,
          Metrics: event.data.metrics,
          ProcessedAt: new Date().toISOString()
        }
      }));
      
      logger.info({ eventId, robotId }, "Telemetry event successfully persisted to DynamoDB storage.");
    } catch (err) {
     logger.error({ 
        err: { message: err instanceof Error ? err.message : String(err), stack: err instanceof Error ? err.stack : undefined }, 
        eventId: eventId || undefined, 
        robotId: robotId || undefined
      }, "Abrupt failure encountered while processing stream observer record.");
    }
  }
}