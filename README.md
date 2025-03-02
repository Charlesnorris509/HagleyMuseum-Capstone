# HagleyMuseum-Capstone

## Description
This project is a capstone for the Hagley Museum, implemented entirely in Python. It aims to be a custom API built on the BlackBaud SKY API to retrieve OLTP data for safe storage and future backup through cloud-based OLAP Solutions.

## Architecture

The project follows a distributed, event-driven architecture consisting of several loosely coupled components:

### Key Components

1. **API Gateway (FastAPI)** - Handles incoming HTTP requests and routes them to appropriate services
2. **Authentication Service** - Manages authentication with the Blackbaud SKY API
3. **Event-Driven Data Sync Services** - Specialized services for syncing different entity types:
   - Customer Sync Service
   - Event Sync Service
   - Wristband Sync Service
   - Parking Pass Sync Service
4. **Database Service** - Abstracts database interactions
5. **Message Broker (RabbitMQ)** - Provides event-based communication between services
6. **Worker Service** - Processes messages from the queue independently of the API
7. **Scheduler Service** - Manages periodic tasks and job scheduling

### Benefits of This Architecture

- **Scalability** - Each component can be scaled independently based on load
- **Fault Tolerance** - If one component fails, others can continue to operate
- **Loose Coupling** - Services communicate through messages, reducing dependencies
- **Maintainability** - Smaller, focused components are easier to understand and maintain
- **Extensibility** - New features can be added by creating new services or extending existing ones

## Setup and Installation

### Prerequisites
- Docker and Docker Compose
- Python 3.8 or higher (for local development only)
- MySQL 8.0 (handled by Docker)
- RabbitMQ (handled by Docker)

### Environment Setup

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/HagleyMuseum-Capstone.git
   cd HagleyMuseum-Capstone
   ```

2. Set up environment variables by creating a `.env` file in the API directory:
   ```
   BLACKBAUD_SUBSCRIPTION_KEY=your_subscription_key_here
   BLACKBAUD_CLIENT_ID=your_client_id_here
   BLACKBAUD_CLIENT_SECRET=your_client_secret_here
   DB_HOST=db
   DB_USER=root
   DB_PASSWORD=password
   DB_NAME=FireworksDB
   BB_CONFIG_PATH=API/resources/app_secrets.json
   RABBITMQ_HOST=rabbitmq
   RABBITMQ_PORT=5672
   RABBITMQ_USER=guest
   RABBITMQ_PASS=guest
   ```

3. Update API credentials in `API/resources/app_secrets.json` and `API/resources/app_secrets.ini`

### Running with Docker Compose

Start all services:
```
docker-compose up -d
```

This will start:
- The FastAPI gateway on port 8000
- Multiple worker instances for asynchronous processing
- RabbitMQ for messaging (management UI available on port 15672)
- MySQL database on port 3306

### Development Setup

For local development without Docker:

1. Create a virtual environment and install dependencies:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. Start the API:
   ```
   uvicorn API.OLAP.API:app --reload --host 0.0.0.0 --port 8000
   ```

3. In another terminal, start the worker:
   ```
   python -m API.services.worker
   ```

## API Endpoints

- `GET /` - API status check
- `POST /sync/all` - Trigger synchronization of all data
- `POST /sync/customer` - Sync a specific customer
- `POST /sync/events` - Sync events for a date range

## Architecture Diagram

```
┌─────────────┐     ┌───────────────┐
│             │     │               │
│ API Gateway ├─────► Auth Service  │
│   (FastAPI) │     │               │
│             │     └───────────────┘
└──────┬──────┘
       │                ┌───────────────┐
       │                │               │
       ▼                │  Scheduler    │
┌─────────────┐         │   Service     │
│             │         │               │
│  Message    │         └───────┬───────┘
│   Broker    │                 │
│ (RabbitMQ)  │                 ▼
│             │         ┌───────────────┐
└──────┬──────┘         │               │
       │                │ Event-Driven  │
       ▼                │    Tasks      │
┌─────────────┐         │               │
│             │         └───────────────┘
│   Worker    │
│  Service(s) │
│             │
└──────┬──────┘
       │
       ▼
┌─────────────┐    ┌────────────────┐
│             │    │                │
│  Database   ◄────┤  Data Storage  │
│   Service   │    │   (MySQL)      │
│             │    │                │
└─────────────┘    └────────────────┘
```

