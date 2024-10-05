const express = require('express');
const axios = require('axios');
const redis = require('redis');

const app = express();
const cache = redis.createClient();

const USER_SERVICE_URL = 'http://localhost:5000';
const FINANCE_SERVICE_URL = 'http://localhost:5001';

// Connect to Redis and handle errors
cache.on('error', (err) => {
  console.log('Redis Client Error', err);
});

(async () => {
  // Await Redis connection
  await cache.connect();
})();

const CACHE_EXPIRY_TIME = 60; // Cache expiry time in seconds

// Middleware to parse JSON bodies
app.use(express.json());

// Status endpoint for the API Gateway
app.get('/status', (req, res) => {
  res.status(200).json({ status: 'API Gateway is running' });
});

// Get user info with caching
app.get('/get_user/:user_id', async (req, res) => {
  const { user_id } = req.params;

  try {
    const cachedUser = await cache.get(`user:${user_id}`);
    if (cachedUser) {
      return res.status(200).json({ source: 'cache', data: JSON.parse(cachedUser) });
    }

    const response = await axios.get(`${USER_SERVICE_URL}/users/${user_id}`);

    if (response.headers['content-type'].includes('application/json')) {
      const user = response.data;

      await cache.setEx(`user:${user_id}`, CACHE_EXPIRY_TIME, JSON.stringify(user));

      return res.status(200).json({ source: 'service', data: user });
    } else {
      return res.status(500).json({ error: 'Invalid response from User Service' });
    }
  } catch (error) {
    return res.status(500).json({ error: 'User service error', details: error.message });
  }
});

// Register a new user
app.post('/register', async (req, res) => {
  try {
    const response = await axios.post(`${USER_SERVICE_URL}/register`, req.body);
    return res.status(response.status).json(response.data);
  } catch (error) {
    return res.status(500).json({ error: 'User service error', details: error.message });
  }
});

// Login a user
app.post('/login', async (req, res) => {
  try {
    const response = await axios.post(`${USER_SERVICE_URL}/login`, req.body);
    return res.status(response.status).json(response.data);
  } catch (error) {
    return res.status(500).json({ error: 'User service error', details: error.message });
  }
});

// Get transaction info with caching
app.get('/get_transaction/:transaction_id', async (req, res) => {
  const { transaction_id } = req.params;

  // Try to get the transaction from cache
  try {
    const cachedTransaction = await cache.get(`transaction:${transaction_id}`);
    if (cachedTransaction) {
      return res.status(200).json({ source: 'cache', data: JSON.parse(cachedTransaction) });
    }

    // If transaction is not in cache, call the finance service
    const response = await axios.get(`${FINANCE_SERVICE_URL}/transactions/${transaction_id}`);
    const transaction = response.data;

    // Store the transaction data in cache with expiry time
    await cache.setEx(`transaction:${transaction_id}`, CACHE_EXPIRY_TIME, JSON.stringify(transaction));

    return res.status(200).json({ source: 'service', data: transaction });
  } catch (error) {
    return res.status(500).json({ error: 'Finance service error', details: error.message });
  }
});

// Create a new transaction
app.post('/transactions', async (req, res) => {
  try {
    const response = await axios.post(`${FINANCE_SERVICE_URL}/transactions`, req.body);
    return res.status(response.status).json(response.data);
  } catch (error) {
    return res.status(500).json({ error: 'Finance service error', details: error.message });
  }
});

// Start the API Gateway server
const PORT = process.env.PORT || 5002;
app.listen(PORT, () => {
  console.log(`API Gateway running on port ${PORT}`);
});
