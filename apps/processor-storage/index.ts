import { KinesisStreamEvent, KinesisStreamRecord } from 'aws-lambda';
import { DynamoDBClient } from '@aws-sdk/client-dynamodb';
import { DynamoDBDocumentClient, PutCommand } from '@aws-sdk/lib-dynamodb';
import pino from 'pino';
import { TelemetryPayload } from '@iot-fleet/shared-types';

const logger = pino({ name: 'processor-storage' });
const ddbClient = new DynamoDBClient({ region: process.env.AWS_REGION || 'us-east-1' });
const docClient = DynamoDBDocumentClient.from(ddbClient);
const TABLE_NAME = process.env.TELEMETRY_TABLE_NAME || 'FleetTelemetry';

// 1. Primary AWS Lambda Entry Point
export const handler = async (event: KinesisStreamEvent): Promise<void> => {
  await processRecords(event.Records);
};

// 2. Named Export for Jest Unit Tests
export async function processRecords(records: KinesisStreamRecord[]): Promise<void> {
  logger.info(`Processing batch of ${records.length} records from Kinesis stream.`);

  for (const record of records) {
    let payload: TelemetryPayload;

    try {
      // Decode Base64 payload from Kinesis Stream
      const decodedData = Buffer.from(record.kinesis.data, 'base64').toString('utf-8');
      payload = JSON.parse(decodedData) as TelemetryPayload;
      
      // Strict structural validation before database mutation attempts
      if (!payload.robotId || payload.timestamp === undefined || payload.latitude === undefined) {
        throw new Error('Payload violates schema contract.');
      }
    } catch (error: any) {
      // ISOLATION LAYER: Poison messages must be logged and skipped.
      // Allowing an exception to throw here would freeze the Kinesis Shard.
      logger.error({ 
        msg: 'Poison message encountered. Skipping record to prevent shard blockage.', 
        sequenceNumber: record.kinesis.sequenceNumber,
        error: error.message 
      });
      continue;
    }

    try {
      // Write to DynamoDB with an explicit uniqueness constraint mapping
      await docClient.send(new PutCommand({
        TableName: TABLE_NAME,
        Item: {
          robotId: payload.robotId,
          timestamp: payload.timestamp,
          latitude: payload.latitude,
          longitude: payload.longitude,
          metrics: payload.metrics,
          processedAt: new Date().toISOString()
        },
        // IDEMPOTENCY ENGINE: Prevent duplicates if a network retry delivers the message again
        ConditionExpression: 'attribute_not_exists(robotId) AND attribute_not_exists(#ts)',
        ExpressionAttributeNames: {
          '#ts': 'timestamp'
        }
      }));
    } catch (error: any) {
      if (error.name === 'ConditionalCheckFailedException') {
        // Safe execution path: This indicates a message redelivery. Log and suppress.
        logger.warn({ 
          msg: 'Duplicate message retry caught safely via idempotency key.', 
          robotId: payload.robotId,
          timestamp: payload.timestamp 
        });
      } else {
        // Infrastructure failure (e.g., Throttle/Network Loss): Let it bubble up to trigger Kinesis retries
        logger.fatal({ msg: 'Downstream database write failed. Triggering stream backpressure retry.', error: error.message });
        throw error;
      }
    }
  }
}