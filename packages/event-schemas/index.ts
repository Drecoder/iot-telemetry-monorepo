export interface TelemetryPayload {
  robotId: string;
  timestamp: string;
  metrics: {
    speed?: number;
    engineTemp?: number;
    latitude?: number;
    longitude?: number;
    fuelLevel?: number;
    batteryLevel?: number;    
    cpuTemperature?: number;  
  };
}

export interface TelemetryEvent {
  eventId: string;
  eventType: 'TELEMETRY_RECEIVED';
  emittedAt: string;
  data: TelemetryPayload;
}