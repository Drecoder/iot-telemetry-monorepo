import { TelemetryEvent } from "event-schemas";

const CPU_TEMP_THRESHOLD = 85; // Celsius
const BATTERY_LOW_THRESHOLD = 15; // Percentage

/**
 * Processes a batch of records polled from the Kinesis stream.
 * Scans for threshold anomalies to trigger downstream engineering alerts.
 */
export async function processAlerts(records: any[]): Promise<void> {
  for (const record of records) {
    try {
      // Decode the base64 data stream envelope from Kinesis
      const rawData = Buffer.from(record.kinesis.data, 'base64').toString('utf-8');
      const event: TelemetryEvent = JSON.parse(rawData);
      
      const { robotId, metrics } = event.data;

      // Check Invariant 1: Engine / CPU Overheating
      if (metrics.cpuTemperature > CPU_TEMP_THRESHOLD) {
        console.warn(
          `[CRITICAL ALERT] Robot ${robotId} is overheating! Current Temp: ${metrics.cpuTemperature}°C (Threshold: ${CPU_TEMP_THRESHOLD}°C)`
        );
        // NOTE: In a real-world CNH production stack, you would emit an alert to Datadog/PagerDuty here
      }

      // Check Invariant 2: Low Battery Critical Operational Thresholds
      if (metrics.batteryLevel < BATTERY_LOW_THRESHOLD) {
        console.warn(
          `[LOW BATTERY] Robot ${robotId} needs charging. Current Level: ${metrics.batteryLevel}%`
        );
      }

    } catch (err) {
      console.error("Failed to parse stream record within alerts observer:", err);
    }
  }
}