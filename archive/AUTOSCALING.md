# Autoscaling DJL Embedding Service

## Overview

The DJL container can be autoscaled horizontally for CPU inference. GPU inference typically doesn't autoscale well (expensive, fixed resources), but CPU inference can scale to match load.

---

## CPU vs GPU Trade-offs

| Aspect | GPU (NVIDIA) | CPU (Autoscale) |
|--------|--------------|-----------------|
| **Throughput/instance** | ~3,000-5,000 chunks/sec | ~500-700 chunks/sec |
| **Cost/instance** | High (GPU required) | Low (commodity CPU) |
| **Scaling** | Vertical (bigger GPU) | Horizontal (add instances) |
| **Startup time** | 30-60s (model load) | 30-60s (model load) |
| **Use case** | Single large workload | Bursty / on-demand |

---

## Autoscaling Strategies

### 1. Docker Swarm (Simple)

```bash
# Initialize swarm
docker swarm init

# Deploy stack with replicas
docker stack deploy -c docker-compose.cpu.yml embed

# Scale up/down
docker service scale embed_djl-cpu=5
```

**Pros:**
- Simple built-in orchestration
- No external dependencies

**Cons:**
- Basic autoscaling (manual or script-based)
- No advanced metrics-based scaling

---

### 2. Kubernetes + HPA (Production)

**deployment.yaml:**
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: djl-cpu
spec:
  replicas: 2
  selector:
    matchLabels:
      app: djl-cpu
  template:
    metadata:
      labels:
        app: djl-cpu
    spec:
      containers:
      - name: djl
        image: deepjavalibrary/djl-serving:0.32.0-pytorch-cpu
        env:
        - name: SERVING_LOAD_MODELS
          value: djl://ai.djl.huggingface.pytorch/sentence-transformers/all-MiniLM-L6-v2
        - name: OMP_NUM_THREADS
          value: "4"
        resources:
          requests:
            cpu: "2"
            memory: "2Gi"
          limits:
            cpu: "4"
            memory: "4Gi"
        ports:
        - containerPort: 8080
        readinessProbe:
          httpGet:
            path: /ping
            port: 8080
          initialDelaySeconds: 60
          periodSeconds: 10
---
apiVersion: v1
kind: Service
metadata:
  name: djl-cpu
spec:
  selector:
    app: djl-cpu
  ports:
  - port: 8080
    targetPort: 8080
  type: LoadBalancer
---
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: djl-cpu-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: djl-cpu
  minReplicas: 2
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  behavior:
    scaleUp:
      stabilizationWindowSeconds: 60
      policies:
      - type: Percent
        value: 50
        periodSeconds: 60
    scaleDown:
      stabilizationWindowSeconds: 300
      policies:
      - type: Pods
        value: 1
        periodSeconds: 60
```

**Deploy:**
```bash
kubectl apply -f deployment.yaml

# Watch autoscaling
kubectl get hpa -w
```

**Pros:**
- Metrics-based autoscaling (CPU, custom metrics)
- Production-grade orchestration
- Rolling updates, health checks

**Cons:**
- Requires K8s cluster
- More complex setup

---

### 3. AWS ECS Fargate (Serverless)

**task-definition.json:**
```json
{
  "family": "djl-cpu-embedding",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "2048",
  "memory": "4096",
  "containerDefinitions": [
    {
      "name": "djl",
      "image": "deepjavalibrary/djl-serving:0.32.0-pytorch-cpu",
      "environment": [
        {
          "name": "SERVING_LOAD_MODELS",
          "value": "djl://ai.djl.huggingface.pytorch/sentence-transformers/all-MiniLM-L6-v2"
        },
        {
          "name": "OMP_NUM_THREADS",
          "value": "4"
        }
      ],
      "portMappings": [
        {
          "containerPort": 8080,
          "protocol": "tcp"
        }
      ],
      "healthCheck": {
        "command": ["CMD-SHELL", "curl -f http://localhost:8080/ping || exit 1"],
        "interval": 30,
        "timeout": 5,
        "retries": 3,
        "startPeriod": 60
      }
    }
  ]
}
```

**service.json (with autoscaling):**
```json
{
  "serviceName": "djl-cpu-service",
  "taskDefinition": "djl-cpu-embedding",
  "desiredCount": 2,
  "launchType": "FARGATE",
  "networkConfiguration": {
    "awsvpcConfiguration": {
      "subnets": ["subnet-xxx"],
      "securityGroups": ["sg-xxx"],
      "assignPublicIp": "ENABLED"
    }
  }
}
```

**Autoscaling:**
```bash
# Register scalable target
aws application-autoscaling register-scalable-target \
  --service-namespace ecs \
  --resource-id service/cluster-name/djl-cpu-service \
  --scalable-dimension ecs:service:DesiredCount \
  --min-capacity 2 \
  --max-capacity 10

# Create scaling policy
aws application-autoscaling put-scaling-policy \
  --policy-name djl-cpu-scaling \
  --service-namespace ecs \
  --resource-id service/cluster-name/djl-cpu-service \
  --scalable-dimension ecs:service:DesiredCount \
  --policy-type TargetTrackingScaling \
  --target-tracking-scaling-policy-configuration \
    'TargetValue=70.0,PredefinedMetricSpecification={PredefinedMetricType=ECSServiceAverageCPUUtilization}'
```

**Pros:**
- Serverless (no cluster management)
- Pay-per-use
- Native AWS integration

**Cons:**
- AWS-specific
- Cold start for scale-from-zero
- More expensive than EC2 at scale

---

### 4. Cloud Run / Azure Container Instances (Serverless)

**Google Cloud Run:**
```bash
# Deploy
gcloud run deploy djl-cpu \
  --image=deepjavalibrary/djl-serving:0.32.0-pytorch-cpu \
  --platform=managed \
  --region=us-central1 \
  --memory=4Gi \
  --cpu=4 \
  --min-instances=1 \
  --max-instances=10 \
  --set-env-vars="SERVING_LOAD_MODELS=djl://ai.djl.huggingface.pytorch/sentence-transformers/all-MiniLM-L6-v2" \
  --timeout=300s
```

**Pros:**
- Simplest serverless option
- Scale-to-zero supported
- Very fast autoscaling

**Cons:**
- Cold start penalty (~30-60s for model load)
- Max 4 vCPU per instance (less throughput/instance)

---

## Load Balancing the Python Pipeline

When using multiple DJL instances, you need a load balancer. Two approaches:

### Option A: External Load Balancer

Use nginx, HAProxy, or cloud LB in front of DJL instances.

**nginx.conf:**
```nginx
upstream djl_backend {
    least_conn;
    server djl-cpu-1:8080 max_fails=3 fail_timeout=30s;
    server djl-cpu-2:8080 max_fails=3 fail_timeout=30s;
    server djl-cpu-3:8080 max_fails=3 fail_timeout=30s;
}

server {
    listen 8080;
    location / {
        proxy_pass http://djl_backend;
        proxy_next_upstream error timeout http_502 http_503;
        proxy_connect_timeout 5s;
        proxy_read_timeout 60s;
    }
}
```

**Pipeline points to load balancer:**
```bash
DJL_URL=http://nginx:8080/predictions/all-MiniLM-L6-v2
```

### Option B: Client-Side Load Balancing

Modify `embed_pipeline.py` to round-robin across multiple DJL endpoints:

```python
class DJLEmbedderPool:
    """Client-side load balancing across multiple DJL instances."""

    def __init__(self, djl_urls: list[str], batch_size: int):
        self.embedders = [DJLEmbedder(url, batch_size) for url in djl_urls]
        self.idx = 0

    def encode(self, texts: list[str]) -> list[list[float]]:
        embedder = self.embedders[self.idx]
        self.idx = (self.idx + 1) % len(self.embedders)
        return embedder.encode(texts)
```

**Config:**
```bash
DJL_URLS=http://djl-1:8080/predictions/model,http://djl-2:8080/predictions/model
```

---

## Performance Estimates

### Single GPU Instance
- Throughput: ~3,000-5,000 chunks/sec
- Cost: $1-3/hour (p3.2xlarge)
- Scaling: Limited (1-2 GPUs per node)

### Autoscaled CPU (5 instances)
- Throughput: ~3,000-3,500 chunks/sec (700/instance × 5)
- Cost: $0.50-1/hour (5 × c5.xlarge)
- Scaling: Elastic (2-20 instances)

**Recommendation:**
- **GPU** for sustained, high-throughput workloads (24/7 indexing)
- **CPU autoscaling** for bursty, on-demand workloads

---

## Migration Path

1. **Start with GPU** — Validate pipeline, measure baseline
2. **Add CPU variant** — Test with `docker-compose.cpu.yml`
3. **Deploy to K8s/ECS** — Add HPA with 2-10 replicas
4. **Monitor and tune** — Adjust min/max replicas, CPU targets

---

## Next Steps

- [ ] Test CPU throughput: `docker-compose -f docker-compose.cpu.yml up`
- [ ] Benchmark CPU vs GPU: Run `test_local.py` against both
- [ ] Choose orchestration: K8s (prod) or ECS (serverless) or Swarm (simple)
- [ ] Add load balancer if using multiple instances
- [ ] Monitor autoscaling metrics (CPU, request latency, queue depth)
