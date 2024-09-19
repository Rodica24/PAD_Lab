# Personal Finance Tracker

## Application suitability
A personal finance tracker involves multiple components such as user authentication, expense and income tracking or savings goal management. That's why I think this idea is a good fit for a microservices architecture, due to its requirement for individual development, scalability, and clear service boundaries. The separation into two different microservices (user and finance service) will ensures that each component can be managed and maintained independently while addressing the core functionalities of the application.

### Real-world examples
* **Mint**, utilizes microservices to manage various aspects of personal finance, including user authentication and financial data processing. 
* **YNAB** (You Need A Budget) also employs microservices to manage user accounts and financial tracking, allowing for modular development and scalable services.

## Service Boundaries
I plan on having two microservices and an API Gateway:
* User service: Handles user registration, login, authentication, and profile management.
* Finance service: Manages all financial data (income, expenses, and savings goals).
* API Gateway: Centralized access point for clients that routes incoming requests to User Service or Finance Service based on the request path.

## Technology Stack and Communication Patterns
## Data Management Design

## Deployment and Scaling
### Containerization 
Will use Docker to containerize both the User Service and Finance Service.
### Orchestration
Will use Kubernetes to orchestrate multiple instances of these services. This will allow my app to scale as more users register or track their finances.
