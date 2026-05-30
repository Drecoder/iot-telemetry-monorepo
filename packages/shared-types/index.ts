/**
 * Core Core Metric Attributes emitted from the robot edge physical layers
 */
export interface RobotMetrics {
    speed: number;            // Current ground velocity (e.g., meters per second or km/h)
    batteryLevel: number;     // Remaining battery capacity percentage (0 to 100)
    cpuTemperature: number;   // Processor temperature in Celsius for hardware safety monitoring
}

/**
 * Global Invariant IoT Telemetry Packet Schema
 * Distributed systems rely on this exact contract for end-to-end event stream parsing
 */
export interface TelemetryPayload {
    robotId: string;          // Globally unique identity string (DynamoDB Partition Key)
    timestamp: number;        // Epoch Unix millisecond timestamp when event occurred (DynamoDB Sort Key)
    latitude: number;         // High-precision WGS 84 coordinate geometry latitude
    longitude: number;        // High-precision WGS 84 coordinate geometry longitude
    metrics: RobotMetrics;    // Internal system telemetry health and processing characteristics
}

/**
 * System Ingestion Event response status wrappers
 */
export type IngestionStatus = 'ACCEPTED' | 'REJECTED' | 'RATE_LIMITED';

export interface IngestionResponse {
    status: IngestionStatus;
    processedAt?: string;     // ISO-8601 string confirming storage write finalization
    error?: string;           // Optional diagnostic string populated during 400/500 faults
}