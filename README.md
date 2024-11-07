# Personal Finance Tracker

In order to run the project install and run Docker. After that run the following commands:
```
docker-compose build
docker-compose up
```

## Application suitability
A personal finance tracker involves multiple components such as user authentication, expense and income tracking or savings goal management. That's why I think this idea is a good fit for a microservices architecture, due to its requirement for individual development, scalability, and clear service boundaries. Microservices allow each component to evolve independently. The separation into two different microservices (user and finance service) will ensures that each component can be managed and maintained independently while addressing the core functionalities of the application.

### Real-world examples
* **Mint**, utilizes microservices to manage various aspects of personal finance, including user authentication and financial data processing. 
* **YNAB** (You Need A Budget) also employs microservices to manage user accounts and financial tracking, allowing for modular development and scalable services.

## Service Boundaries
I plan on having two microservices and an API Gateway:
* User service: This microservice will handle user registration, login, authentication, and profile management. It is responsible for securing user data and generating JWT tokens for session management.
* Finance service: This microservice will handle the financial data of users. It will manage the income, expenses, savings goals, and support the group savings challenge, which will leverage WebSocket communication for real-time updates.
* API Gateway: Centralized access point for clients that routes incoming requests to User Service or Finance Service based on the request path. The gateway will also manage caching to improve performance and reduce the load on services.

![image](https://github.com/user-attachments/assets/221a8cd6-bbef-4a38-9912-a1439daf3fe4)


## Technology Stack and Communication Patterns
### Service 1: User Service (Python)

#### Framework: 
FastAPI (for building APIs with Python)
#### Database: 
PostgreSQL, SQLite
#### Authentication: 
JWT (JSON Web Tokens)

### Service 2: Finance Service (Python)
#### Framework:
Flask
#### Database:
PostgreSQL, SQLite

### API Gateway
Framework: Express.js (Node.js) to serve as a central entry point for external clients and route requests to appropriate microservices

### Communication Patterns
#### RESTful APIs:
Used for HTTP communication between external clients and the User Service, as well as for basic interactions with the Financial Service.
#### gRPC:
Internal communication between the services will use gRPC. This protocol is faster and more efficient than REST, especially when handling internal, high-volume service-to-service communication.
#### WebSocket:
WebSockets will be used for the group savings challenge feature. Clients will open WebSocket connections to the Finance Service, receiving real-time updates on the group's savings progress.
#### Caching:
The API Gateway will manage the Redis cache. It will store frequently requested data such as user profiles and financial summaries.


## Data Management Design
### User service endpoints:
**1. POST /user/register - Registers a new user**
#### Body   
```json
{
  "username": "string",
  "email": "string",
  "password": "string"
}
```
#### Response
```json
{
  "message": "User registered successfully",
  "userId": "integer"
}
```

**2. POST /user/login - Authenticates a user and returns a token**
#### Body 
```json
{
  "email": "string",
  "password": "string"
}
```
#### Response
```json
{
  "token": "string",
  "userId": "integer"
}
```

**3. GET /user/{id} - Retrieves a user’s profile**
#### Response
```json
{
  "userId": "integer",
  "username": "string",
  "email": "string"
}
```

### Finance service endpoints:
**1. POST /income - Adds a new income record for a user**
#### Body 
```json
{
  "userId": "integer",
  "amount": "float",
  "source": "string",
  "date": "string (ISO 8601 format)"
}
```
#### Response
```json
{
  "message": "Income added successfully",
  "incomeId": "integer"
}
```

**2. GET /income/{userId} - Retrieves all income records for a specific user**
#### Response
```json
{
  "incomes": [
    {
      "incomeId": "integer",
      "amount": "float",
      "source": "string",
      "date": "string"
    }
  ]
}
```

**3. POST /expense - Adds a new expense for a user.**
#### Body 
```json
{
  "userId": "integer",
  "amount": "float",
  "category": "string",
  "date": "string (ISO 8601 format)"
}
```
#### Response
```json
{
  "message": "Expense added successfully",
  "expenseId": "integer"
}
```

**4. GET /expense/{userId} - Retrieves all expense records for a specific user**
#### Response
```json
{
  "expenses": [
    {
      "expenseId": "integer",
      "amount": "float",
      "category": "string",
      "date": "string"
    }
  ]
}
```

**5. POST /savings - Sets a new savings goal for a user**
#### Body 
```json
{
  "userId": "integer",
  "goal": "float",
  "targetDate": "string (ISO 8601 format)"
}
```
#### Response
```json
{
  "message": "Savings goal set successfully",
  "savingsId": "integer"
}
```

**6. GET /savings/{userId} - Retrieves the savings goals for a specific user**
#### Response
```json
{
  "savingsGoals": [
    {
      "savingsId": "integer",
      "goal": "float",
      "targetDate": "string"
    }
  ]
}
```
**7. WebSocket /ws/group-savings/{group_id}/updates - Real-time updates for group savings contributions**
#### Body
```json
{
  "user_id": "int",
  "contribution_amount": "float",
  "message": "string",
  "timestamp": "string (ISO 8601 format)"
}
```



   

## Deployment and Scaling
### Containerization 
Each microservice will be packaged in a separate Docker container.

## Updated Architecture:
![Untitled Diagram drawio (4)](https://github.com/user-attachments/assets/b6638c30-cc7f-41a5-a6e9-f4acea6f6d04)

The improved diagram with the new components added consists of:

The **Saga Coordinator**, added to the API Gateway, manages complex transactions that take longer and involve multiple services, especially in the Finance Service. It ensures that all parts of a transaction are eventually consistent without needing a strict 2-phase commit.

**Consistent Hashing for Cache (Redis)**, the Redis Cache now uses consistent hashing to distribute data across cache nodes. This setup ensures that data remains accessible even if individual nodes fail, improving scalability and fault tolerance. It helps with load distribution and high availability of frequently accessed data.

**User Database Replication** (Master-Slave Setup), the User Database has been set up with a master-replica (slave) configuration. The "User DBMaster" node serves as the main data source, while "User DBSlave1" and "User DBSlave2" provide redundancy. This setup improves high availability, as replicas can take over in case the master node fails, ensuring continuous data accessibility.

A **Staging Area and Data Warehouse** have been added to the architecture for data analysis and reporting. Data from the User and Finance databases is periodically extracted, transformed, and loaded (ETL) into the warehouse, allowing for efficient reporting without impacting operational performance. 

The **ELK Stack** has been added to provide centralized logging and monitoring across all services. Each service sends logs to Logstash, which processes and stores them in Elasticsearch. Kibana enables visualization and analysis of these logs, making it easier to monitor system health, troubleshoot issues, and gain insights into usage patterns.

