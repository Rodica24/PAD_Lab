const express = require('express');
const axios = require('axios');
const { createServer } = require('http');
const { createProxyMiddleware } = require('http-proxy-middleware');
const CircuitBreaker = require('./circuitBreaker');
const serviceDiscovery = require('./serviceDiscovery');

// Initialize Express app
const app = express();
app.use(express.json());

// Register replicas for UserService and FinanceService
serviceDiscovery.register('UserService', [
  'http://localhost:5000',
  'http://localhost:5005',
  'http://localhost:5010'
]);

serviceDiscovery.register('FinanceService', [
  'http://localhost:5003',
  'http://localhost:5008',
  'http://localhost:5013'
]);

serviceDiscovery.register('FinanceWebSocketService', [
  'ws://localhost:5001',  // WebSocket instance 1
  'ws://localhost:5006',  // WebSocket instance 2
  'ws://localhost:5011'   // WebSocket instance 3
]);

// Circuit breaker instances
const userServiceCircuitBreaker = new CircuitBreaker(3, 10000);  // Trip after 3 failures, retry after 10 seconds
const financeServiceCircuitBreaker = new CircuitBreaker(3, 10000);

// Retry logic for circuit breaker
async function makeServiceRequest(circuitBreaker, serviceUrl, reqBody, retries = 3) {
    for (let attempt = 1; attempt <= retries; attempt++) {
        if (!circuitBreaker.canRequest()) {
            return { error: 'Service is temporarily unavailable due to repeated failures. Please try again later.' };
        }

        try {
            const response = await axios.post(serviceUrl, reqBody);
            circuitBreaker.reset();  // Reset breaker on success
            return response.data;
        } catch (error) {
            console.log(`Attempt ${attempt} failed for service: ${serviceUrl}`);
            circuitBreaker.recordFailure();  // Record failure on each error
            if (attempt === retries) {
                return { error: 'Service failed after 3 attempts.' };  // Give up after 3 attempts
            }
        }
    }
}

// Proxy for WebSocket connections to FinanceService (port 5001) - assuming single WebSocket endpoint for simplicity
const financeServiceProxy = createProxyMiddleware({
  target: 'http://localhost:5001',
  changeOrigin: true,
  ws: true,
});
app.use('/socket', financeServiceProxy);

// REST API Routes:

// Forward POST requests to FinanceService using Circuit Breaker and Round Robin Load Balancing
app.post('/finance/transactions', async (req, res) => {
  const financeServiceUrl = serviceDiscovery.getNextServiceUrl('FinanceService');
  if (!financeServiceUrl) {
    return res.status(500).json({ error: 'FinanceService is unavailable' });
  }

  const result = await makeServiceRequest(financeServiceCircuitBreaker, `${financeServiceUrl}/transactions`, req.body);

  if (result.error) {
    return res.status(500).json(result);  // Send error response if circuit breaker is tripped
  }

  res.status(200).json(result);  // Success response
});

// Forward POST requests to UserService using Circuit Breaker and Round Robin Load Balancing
app.post('/register', async (req, res) => {
  const userServiceUrl = serviceDiscovery.getNextServiceUrl('UserService');
  if (!userServiceUrl) {
    return res.status(500).json({ error: 'UserService is unavailable' });
  }

  const result = await makeServiceRequest(userServiceCircuitBreaker, `${userServiceUrl}/register`, req.body);

  if (result.error) {
    return res.status(500).json(result);  // Send error response if circuit breaker is tripped
  }

  res.status(200).json(result);  // Success response
});

// Login request with WebSocket URL in the response and Circuit Breaker logic
app.post('/login', async (req, res) => {
  const userServiceUrl = serviceDiscovery.getNextServiceUrl('UserService');
  const websocketUrl = serviceDiscovery.getNextServiceUrl('FinanceWebSocketService');  // Get WebSocket instance

  const result = await makeServiceRequest(userServiceCircuitBreaker, `${userServiceUrl}/login`, req.body);

  if (result.error) {
    return res.status(500).json(result);  // Send error response if circuit breaker is tripped
  }

  res.status(200).json({
    ...result,
    websocket_url: websocketUrl  // Include WebSocket URL in the response
  });
});

// Status endpoint for the API Gateway
app.get('/status', (req, res) => {
  res.json({ status: 'API Gateway is running', uptime: process.uptime() });
});

// Status endpoint for Service Discovery
app.get('/discovery/status', async (req, res) => {
  const serviceStatus = await serviceDiscovery.checkServices();
  res.json({ status: 'Service Discovery is running', services: serviceStatus });
});

// Start the HTTP server for WebSocket and REST API
const server = createServer(app);

// Start the API Gateway on port 5002
const PORT = process.env.PORT || 5002;
server.listen(PORT, () => {
  console.log(`API Gateway running on http://localhost:${PORT}`);
});
