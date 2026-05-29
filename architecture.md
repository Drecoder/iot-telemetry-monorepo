# System Data Flow & Infrastructure Architecture

The following diagram illustrates the lifecycle of a telemetry data payload as it moves through the application validation layer and interacts with the provisioned AWS cloud infrastructure.

```mermaid
graph TD
    %% User/Client Layer
    Client([IoT Device / Client]) -->|POST /api/v1/telemetry| ExpressApp[Express Router]

    %% Application Core Layer (Node.js/Jest Verified)
    subgraph AppRuntime [Node.js v20 App Runtime]
        ExpressApp -->|Input Payload| ValGate{Validation Gate}
        ValGate -->|Invalid: 400 Bad Request| Client
        ValGate -->|Valid Payload| StorageController[Storage Controller]
    end

    %% Infrastructure Layer (Terraform Verified)
    subgraph InfraStack [AWS Cloud Infrastructure]
        StorageController -->|AWS SDK Store Command| DynamoDB[(DynamoDB Telemetry Table)]
        StorageController -.->|Mocked Error Injection| ErrHandler[500 Error Handler]
    end

    %% Response Loop
    DynamoDB -->|Success Write| StorageController
    StorageController -->|201 Created| Client
    ErrHandler -->|500 Internal Server Error| Client

    %% Component Styling
    style Client fill:#eceff1,stroke:#607d8b,stroke-width:2px
    style AppRuntime fill:#e8f5e9,stroke:#2e7d32,stroke-width:2px
    style InfraStack fill:#e3f2fd,stroke:#1565c0,stroke-width:2px
    style ValGate fill:#fff9c4,stroke:#fbc02d,stroke-width:2px
    style DynamoDB fill:#ffe0b2,stroke:#ef6c00,stroke-width:2px