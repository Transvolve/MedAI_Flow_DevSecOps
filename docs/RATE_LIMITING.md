# Rate Limiting Implementation

This project implements distributed rate limiting using Redis as a backend store, ensuring consistent rate limiting across multiple application instances.

## Configuration

Rate limiting can be configured through environment variables:

```env
# Rate Limiting Settings
RATE_LIMIT_PER_MINUTE=60  # Default requests per minute
RATE_LIMIT_BURST=5        # Allow bursts of requests

# Redis Configuration
REDIS_URL=redis://localhost:6379/0  # Redis connection URL
REDIS_POOL_SIZE=10                  # Connection pool size
REDIS_TIMEOUT=5                     # Operation timeout (seconds)
REDIS_SSL=false                     # Enable SSL for Redis
REDIS_PASSWORD=                     # Optional Redis password
```

## Implementation Details

The rate limiting implementation uses:
- `slowapi` for rate limiting logic
- Redis for distributed state management
- Connection pooling for performance
- Fail-open configuration for high availability

### Headers

Rate limit information is exposed through standard headers:
- `X-RateLimit-Limit`: Maximum requests per window
- `X-RateLimit-Remaining`: Remaining requests in current window
- `X-RateLimit-Reset`: Time until the rate limit resets

### Security Considerations

1. **Redis Security:**
   - Use Redis AUTH in production
   - Enable SSL for Redis connections
   - Implement proper network segmentation
   - Regular security patches

2. **Rate Limit Bypass Prevention:**
   - IP-based rate limiting
   - Header validation
   - Load balancer configuration

## Local Development

1. Start Redis:
```bash
docker run --name redis -p 6379:6379 -d redis:alpine
```

2. Configure application:
```bash
export REDIS_URL="redis://localhost:6379/0"
```

3. Verify rate limiting:
```bash
# Should succeed
curl -i http://localhost:8000/api/v1/health

# Should return 429 Too Many Requests after limit exceeded
for i in {1..61}; do curl -i http://localhost:8000/api/v1/health; done
```

## Production Deployment

For production environments:

1. Use managed Redis service (e.g., Azure Cache for Redis)
2. Enable SSL and authentication
3. Configure appropriate rate limits
4. Monitor Redis metrics
5. Set up alerts for rate limit breaches

## Monitoring

The implementation provides:
- Structured logging of rate limit events
- Prometheus metrics (if enabled)
- Request tracking via X-Request-ID
- Performance timing headers