import { processAlerts } from "./index";

describe("Alerts Observer - Telemetry Anomaly Detection", () => {
  let consoleWarnSpy: jest.SpyInstance;

  beforeEach(() => {
    jest.clearAllMocks();
    // Spy on console.warn to check if alerts are firing
    consoleWarnSpy = jest.spyOn(console, "warn").mockImplementation(() => {});
  });

  afterEach(() => {
    consoleWarnSpy.mockRestore();
  });

  it("should sound the alarm when a robot exceeds the critical CPU temperature threshold", async () => {
    const criticalEvent = {
      eventId: "alert-uuid-1",
      eventType: "TELEMETRY_RECEIVED",
      emittedAt: new Date().toISOString(),
      data: {
        robotId: "harvester-99",
        timestamp: 1716984000,
        latitude: 42.0,
        longitude: -88.0,
        metrics: { speed: 5, batteryLevel: 50, cpuTemperature: 92 } // 92 > 85
      }
    };

    const records = [{ kinesis: { data: Buffer.from(JSON.stringify(criticalEvent)).toString("base64") } }];

    await processAlerts(records);

    expect(consoleWarnSpy).toHaveBeenCalledTimes(1);
    expect(consoleWarnSpy.mock.calls[0][0]).toContain("[CRITICAL ALERT] Robot harvester-99 is overheating!");
  });

  it("should trigger an alert when battery falls below operational thresholds", async () => {
    const lowBatteryEvent = {
      eventId: "alert-uuid-2",
      eventType: "TELEMETRY_RECEIVED",
      emittedAt: new Date().toISOString(),
      data: {
        robotId: "seeder-12",
        timestamp: 1716984000,
        latitude: 42.0,
        longitude: -88.0,
        metrics: { speed: 2, batteryLevel: 10, cpuTemperature: 40 } // 10 < 15
      }
    };

    const records = [{ kinesis: { data: Buffer.from(JSON.stringify(lowBatteryEvent)).toString("base64") } }];

    await processAlerts(records);

    expect(consoleWarnSpy).toHaveBeenCalledTimes(1);
    expect(consoleWarnSpy.mock.calls[0][0]).toContain("[LOW BATTERY] Robot seeder-12 needs charging");
  });

  it("should remain silent if metrics are running within safe operational parameters", async () => {
    const nominalEvent = {
      eventId: "alert-uuid-3",
      eventType: "TELEMETRY_RECEIVED",
      emittedAt: new Date().toISOString(),
      data: {
        robotId: "tractor-04",
        timestamp: 1716984000,
        latitude: 42.0,
        longitude: -88.0,
        metrics: { speed: 15, batteryLevel: 90, cpuTemperature: 55 } // All nominal
      }
    };

    const records = [{ kinesis: { data: Buffer.from(JSON.stringify(nominalEvent)).toString("base64") } }];

    await processAlerts(records);

    expect(consoleWarnSpy).not.toHaveBeenCalled();
  });
});