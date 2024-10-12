const axios = require('axios');

class ServiceDiscovery {
  constructor() {
    this.services = {};    // Store services and their replicas
    this.indexes = {};     // Store the current round-robin index for each service
  }

  // Register multiple replicas of a service
  register(serviceName, replicas) {
    this.services[serviceName] = replicas;  // Store an array of replicas
    this.indexes[serviceName] = 0;  // Initialize round-robin index for the service
  }

  // Get the next replica of the service using Round Robin
  getNextServiceUrl(serviceName) {
    const replicas = this.services[serviceName];
    if (!replicas || replicas.length === 0) {
      return null;  // No replicas registered
    }

    // Get the current index and fetch the service URL
    const currentIndex = this.indexes[serviceName];
    const serviceUrl = replicas[currentIndex];

    // Update the index for the next request (round-robin logic)
    this.indexes[serviceName] = (currentIndex + 1) % replicas.length;

    return serviceUrl;
  }

  // Optional: Health check for registered services
  async checkServices() {
    const serviceStatus = {};

    for (const serviceName in this.services) {
      serviceStatus[serviceName] = await Promise.all(
        this.services[serviceName].map(async (url) => {
          try {
            const response = await axios.get(`${url}/status`);  // Try to fetch the status of each service
            return { url, status: 'available', details: response.data };
          } catch (error) {
            return { url, status: 'unavailable' };
          }
        })
      );
    }

    return serviceStatus;
  }

  // Manually unregister a service if needed
  unregister(serviceName) {
    delete this.services[serviceName];
    delete this.indexes[serviceName];
  }
}

module.exports = new ServiceDiscovery();
