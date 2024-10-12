class CircuitBreaker {
  constructor(maxFailures, resetTimeout) {
      this.maxFailures = maxFailures;  // Maximum allowed failures before tripping
      this.resetTimeout = resetTimeout;  // Timeout before trying again after tripping
      this.failures = 0;  // Current number of consecutive failures
      this.lastAttemptTime = 0;  // Timestamp of the last failed attempt
      this.state = 'CLOSED';  // Circuit breaker states: CLOSED, OPEN, HALF_OPEN
  }

  // Function to check if the circuit breaker should allow a request
  canRequest() {
      const currentTime = Date.now();
      
      if (this.state === 'OPEN') {
          // Check if enough time has passed since the circuit breaker tripped
          if (currentTime - this.lastAttemptTime >= this.resetTimeout) {
              this.state = 'HALF_OPEN';  // Try sending requests again
              return true;
          }
          return false;  // Do not allow requests if timeout has not passed
      }

      return true;  // Allow requests if the circuit breaker is CLOSED or HALF_OPEN
  }

  // Function to handle a failed request
  recordFailure() {
      this.failures += 1;
      this.lastAttemptTime = Date.now();

      if (this.failures >= this.maxFailures) {
          this.state = 'OPEN';  // Trip the circuit breaker
          console.log(`Circuit breaker tripped. Too many failures (${this.failures} consecutive failures).`);
      }
  }

  // Function to reset the failure count (success case)
  reset() {
      this.failures = 0;
      this.state = 'CLOSED';
      console.log('Circuit breaker reset. Service is now available.');
  }
}

module.exports = CircuitBreaker;
