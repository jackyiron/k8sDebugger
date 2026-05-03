
# K8s Debugger

AI-Powered Kubernetes Node & Pod Debugging Tool for quick diagnosis of K8s cluster issues.

## Features

- **Node Debugging**: Quickly debug node issues with detailed status, conditions, resources, and events
- **Pod Debugging**: Comprehensive pod analysis including logs, events, container status, and resource usage
- **Service Debugging**: Service endpoints, selectors, and backend pod health
- **Gateway Debugging**: Ingress/Gateway routing, backend services, and controller status
- **AI-Powered Diagnostics**: Smart recommendations based on detected issues
- **Quick Health Check**: Fast cluster-wide health overview

## Installation

```bash
# Make the script executable
chmod +x k8s_debugger.py

# Or install kubectl if not already installed
curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"
chmod +x kubectl
sudo mv kubectl /usr/local/bin/
```

## Usage

```bash
# Make executable
chmod +x k8s_debugger.py

# Run tool
./k8s_debugger.py quick-check
```

### Debug a Node

```bash
./k8s_debugger.py node <node-name>
# Example:
./k8s_debugger.py node worker-node-1
```

### Debug a Pod

```bash
./k8s_debugger.py pod <pod-name> -n <namespace>
# Example:
./k8s_debugger.py pod my-app -n default
```

### Debug a Service

```bash
./k8s_debugger.py svc <service-name> -n <namespace>
# Example:
./k8s_debugger.py svc my-service -n default
```

### Debug an Ingress/Gateway

```bash
./k8s_debugger.py gateway <ingress-name> -n <namespace>
# Example:
./k8s_debugger.py gateway my-ingress -n default
```

### Cluster Analysis

```bash
./k8s_debugger.py cluster
# or
./k8s_debugger.py analyze
```

### JSON Output

```bash
./k8s_debugger.py quick-check -o json
```

## Commands

| Command | Description |
|---------|-------------|
| `quick-check` | Quick cluster health check |
| `node <name>` | Debug a specific node |
| `pod <name>` | Debug a specific pod |
| `svc <name>` | Debug a service |
| `gateway <name>` | Debug an Ingress/Gateway |
| `cluster` | Full cluster analysis |
| `analyze` | AI-powered cluster analysis |

## Output Format

The tool provides:
- **Node Status**: Conditions, resources, events
- **Pod Status**: Phase, containers, logs, events
- **AI Analysis**: Issues detected with smart recommendations

## Requirements

- Python 3.7+
- kubectl configured with cluster access
