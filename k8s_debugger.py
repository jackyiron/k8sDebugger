#!/usr/bin/env python3
"""
K8s Debugger - AI-Powered Kubernetes Node & Pod Debugging Tool

A fast debugging tool for Kubernetes clusters that helps quickly diagnose
issues with nodes and pods using AI-powered diagnostics.

Usage:
    python k8s_debugger.py <command> [options]
    
Commands:
    node <node-name>     Debug a specific node
    pod <pod-name>      Debug a specific pod (in namespace)
    svc <svc-name>     Debug a service (in namespace)
    gateway <name>    Debug an ingress/gateway (in namespace)
    cluster            Debug entire cluster
    analyze           AI-powered issue analysis
    quick-check       Quick health check of cluster

Examples:
    python k8s_debugger.py node worker-node-1
    python k8s_debugger.py pod my-app -n default
    python k8s_debugger.py quick-check
"""

import argparse
import json
import subprocess
import sys
from datetime import datetime
from typing import Optional, Dict, Any, List

# ANSI colors for terminal output
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    
    @staticmethod
    def status_ok(msg: str) -> str:
        return f"{Colors.GREEN}✓{Colors.ENDC} {msg}"
    
    @staticmethod
    def status_warn(msg: str) -> str:
        return f"{Colors.WARNING}⚠{Colors.ENDC} {msg}"
    
    @staticmethod
    def status_fail(msg: str) -> str:
        return f"{Colors.FAIL}✗{Colors.ENDC} {msg}"
    
    @staticmethod
    def header(msg: str) -> str:
        return f"{Colors.HEADER}{Colors.BOLD}{msg}{Colors.ENDC}"


class K8sDebugger:
    """AI-Powered K8s Debugger for nodes and pods."""
    
    def __init__(self, namespace: str = "default"):
        self.namespace = namespace
        self.context = self._get_context()
    
    def _run_kubectl(self, *args: str) -> Dict[str, Any]:
        """Run kubectl command and return JSON output."""
        cmd = ["kubectl", "--request-timeout=30s"] + list(args)
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=60
            )
            if result.returncode != 0:
                return {"error": result.stderr, "success": False}
            return {"success": True, "output": result.stdout}
        except subprocess.TimeoutExpired:
            return {"error": "Command timed out", "success": False}
        except FileNotFoundError:
            return {"error": "kubectl not found", "success": False}
        except Exception as e:
            return {"error": str(e), "success": False}
    
    def _get_context(self) -> str:
        """Get current Kubernetes context."""
        result = self._run_kubectl("config", "current-context")
        if result.get("success"):
            return result["output"].strip()
        return "unknown"
    
    def get_nodes(self) -> List[Dict[str, Any]]:
        """Get all nodes with their status."""
        result = self._run_kubectl("get", "nodes", "-o", "json")
        if not result.get("success"):
            return []
        
        import json
        try:
            data = json.loads(result["output"])
            return data.get("items", [])
        except:
            return []
    
    def get_pods(self, namespace: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get all pods in namespace."""
        ns = namespace or self.namespace
        result = self._run_kubectl("get", "pods", "-n", ns, "-o", "json")
        if not result.get("success"):
            return []
        
        import json
        try:
            data = json.loads(result["output"])
            return data.get("items", [])
        except:
            return []
    
    def debug_node(self, node_name: str) -> Dict[str, Any]:
        """Debug a specific node - comprehensive analysis."""
        print(f"{Colors.header('🔍 Debugging Node:')} {node_name}")
        print(f"{Colors.CYAN}Context:{Colors.ENDC} {self.context}\n")
        
        issues = []
        warnings = []
        
        # 1. Get node details
        result = self._run_kubectl("get", "node", node_name, "-o", "json")
        if not result.get("success"):
            return {"error": f"Failed to get node: {result.get('error')}"}
        
        import json
        node = json.loads(result["output"])
        
        # 2. Check node conditions
        conditions = node.get("status", {}).get("conditions", [])
        print(Colors.header("📊 Node Conditions:"))
        
        critical_conditions = ["Ready", "MemoryPressure", "DiskPressure", "PIDPressure", "NetworkReady"]
        
        for cond in conditions:
            cond_type = cond.get("type", "Unknown")
            status = cond.get("status", "Unknown")
            message = cond.get("message", "")
            reason = cond.get("reason", "")
            
            if status == "True":
                print(Colors.status_ok(f"{cond_type}: {status}"))
            else:
                if cond_type in critical_conditions:
                    issues.append(f"Node {cond_type} is {status}: {message}")
                    print(Colors.status_fail(f"{cond_type}: {status} - {message}"))
                else:
                    warnings.append(f"Node {cond_type} is {status}")
                    print(Colors.status_warn(f"{cond_type}: {status}"))
        
        print()
        
        # 3. Node resources
        allocatable = node.get("status", {}).get("allocatable", {})
        capacity = node.get("status", {}).get("capacity", {})
        
        print(Colors.header("💻 Resource Status:"))
        for resource in ["cpu", "memory", "pods"]:
            cap = capacity.get(resource, "N/A")
            alloc = allocatable.get(resource, "N/A")
            print(f"  {resource.capitalize()}: {alloc} (allocatable) / {cap} (capacity)")
        
        print()
        
        # 4. Node events
        print(Colors.header("📋 Recent Events:"))
        events_result = self._run_kubectl("get", "events", "--field-selector=involvedObject.name=" + node_name, 
                                   "--sort-by=.lastTimestamp", "-o", "json")
        if events_result.get("success"):
            try:
                events = json.loads(events_result["output"]).get("items", [])[-5:]
                for event in events:
                    event_type = event.get("type", "Normal")
                    msg = event.get("message", "")
                    count = event.get("count", 1)
                    print(f"  [{event_type}] {msg} (count: {count})")
            except:
                print("  No recent events")
        
        print()
        
        # 5. AI Analysis
        return self._ai_analyze_node(node, issues, warnings)
    
    def debug_pod(self, pod_name: str, namespace: Optional[str] = None) -> Dict[str, Any]:
        """Debug a specific pod - comprehensive analysis."""
        ns = namespace or self.namespace
        
        print(f"{Colors.header('🔍 Debugging Pod:')} {pod_name}")
        print(f"{Colors.CYAN}Namespace:{Colors.ENDC} {ns}")
        print(f"{Colors.CYAN}Context:{Colors.ENDC} {self.context}\n")
        
        issues = []
        warnings = []
        
        # 1. Get pod details
        result = self._run_kubectl("get", "pod", pod_name, "-n", ns, "-o", "json")
        if not result.get("success"):
            return {"error": f"Failed to get pod: {result.get('error')}"}
        
        import json
        pod = json.loads(result["output"])
        
        # 2. Pod status
        pod_status = pod.get("status", {})
        phase = pod_status.get("phase", "Unknown")
        reason = pod_status.get("reason", "")
        message = pod_status.get("message", "")
        
        print(Colors.header("📊 Pod Status:"))
        print(f"  Phase: {phase}")
        if reason:
            print(f"  Reason: {reason}")
        if message:
            print(f"  Message: {message}")
        
        # Check for issues
        if phase == "Pending":
            issues.append(f"Pod is Pending: {message}")
            print(Colors.status_fail(f"  ⚠ Pod is Pending: {message}"))
        elif phase == "Failed":
            issues.append(f"Pod Failed: {message}")
            print(Colors.status_fail(f"  ⚠ Pod Failed: {message}"))
        elif phase == "CrashLoopBackOff":
            issues.append("Pod is in CrashLoopBackOff state")
            print(Colors.status_fail(f"  ⚠ Pod is in CrashLoopBackOff"))
        else:
            print(Colors.status_ok(f"  Phase: {phase}"))
        
        print()
        
        # 3. Container status
        containers = pod.get("spec", {}).get("containers", [])
        container_statuses = pod_status.get("containerStatuses", [])
        
        print(Colors.header("� containers Status:"))
        for cont in containers:
            cont_name = cont.get("name", "unknown")
            image = cont.get("image", "unknown")
            
            # Find matching status
            status = next((c for c in container_statuses if c.get("name") == cont_name), {})
            
            state = status.get("state", {})
            if state.get("running"):
                print(Colors.status_ok(f"  {cont_name}: Running"))
            elif state.get("waiting"):
                wait_reason = state["waiting"].get("reason", "Unknown")
                print(Colors.status_warn(f"  {cont_name}: Waiting ({wait_reason})"))
                warnings.append(f"Container {cont_name} is waiting: {wait_reason}")
            elif state.get("terminated"):
                exit_code = state["terminated"].get("exitCode", 0)
                print(f"  {cont_name}: Terminated (exit code: {exit_code})")
                if exit_code != 0:
                    issues.append(f"Container {cont_name} terminated with exit code {exit_code}")
                    print(Colors.status_fail(f"    ⚠ Exit code: {exit_code}"))
        
        print()
        
        # 4. Pod resource requests/limits
        print(Colors.header("💻 Resource Requests:"))
        for cont in containers:
            resources = cont.get("resources", {})
            requests = resources.get("requests", {})
            limits = resources.get("limits", {})
            
            print(f"  {cont.get('name')}:")
            print(f"    Requests: {requests}")
            print(f"    Limits: {limits}")
        
        print()
        
        # 5. Pod events
        print(Colors.header("📋 Recent Events:"))
        events_result = self._run_kubectl("get", "events", "-n", ns, 
                                        "--field-selector=involvedObject.name=" + pod_name,
                                        "--sort-by=.lastTimestamp", "-o", "json")
        if events_result.get("success"):
            try:
                events = json.loads(events_result["output"]).get("items", [])[-5:]
                for event in events:
                    event_type = event.get("type", "Normal")
                    msg = event.get("message", "")
                    print(f"  [{event_type}] {msg}")
            except:
                print("  No recent events")
        
        print()
        
        # 6. Get pod logs (last 50 lines)
        print(Colors.header("📝 Pod Logs (last 50 lines):"))
        logs_result = self._run_kubectl("logs", pod_name, "-n", ns, "--tail=50")
        if logs_result.get("success"):
            print(logs_result["output"][:2000])  # Limit output
        else:
            print(f"  Could not get logs: {logs_result.get('error')}")
        
        print()
        
        # 7. AI Analysis
        return self._ai_analyze_pod(pod, issues, warnings)
    
    def _ai_analyze_node(self, node: Dict, issues: List, warnings: List) -> Dict[str, Any]:
        """AI-powered node analysis."""
        print(Colors.header("🤖 AI Analysis:"))
        
        analysis = {
            "node": node.get("metadata", {}).get("name", "unknown"),
            "issues": issues,
            "warnings": warnings,
            "recommendations": []
        }
        
        # Analyze issues and provide recommendations
        if not issues and not warnings:
            print(Colors.status_ok("Node appears healthy! No issues detected."))
            analysis["recommendations"].append("Node is healthy. Continue monitoring.")
        else:
            for issue in issues:
                print(Colors.status_fail(f"  Issue: {issue}"))
                
                # Provide specific recommendations based on issue
                if "NotReady" in issue:
                    analysis["recommendations"].append(
                        "1. Check kubelet status: kubectl describe node <node-name>"
                    )
                    analysis["recommendations"].append(
                        "2. Check kubelet logs: journalctl -u kubelet -n 100"
                    )
                    analysis["recommendations"].append(
                        "3. Verify node has sufficient resources"
                    )
                elif "MemoryPressure" in issue:
                    analysis["recommendations"].append(
                        "1. Check for memory-intensive pods: kubectl top pods"
                    )
                    analysis["recommendations"].append(
                        "2. Increase node memory or reduce pod limits"
                    )
                elif "DiskPressure" in issue:
                    analysis["recommendations"].append(
                        "1. Clean up unused images: docker system prune"
                    )
                    analysis["recommendations"].append(
                        "2. Check disk usage on node"
                    )
        
        for warning in warnings:
            print(Colors.status_warn(f"  Warning: {warning}"))
        
        if analysis["recommendations"]:
            print()
            print(Colors.header("💡 Recommendations:"))
            for rec in analysis["recommendations"]:
                print(f"  • {rec}")
        
        print()
        return analysis
    
    def _ai_analyze_pod(self, pod: Dict, issues: List, warnings: List) -> Dict[str, Any]:
        """AI-powered pod analysis."""
        print(Colors.header("🤖 AI Analysis:"))
        
        pod_name = pod.get("metadata", {}).get("name", "unknown")
        namespace = pod.get("metadata", {}).get("namespace", "default")
        
        analysis = {
            "pod": pod_name,
            "namespace": namespace,
            "issues": issues,
            "warnings": warnings,
            "recommendations": []
        }
        
        if not issues and not warnings:
            print(Colors.status_ok("Pod appears healthy! No issues detected."))
            analysis["recommendations"].append("Pod is healthy. Continue monitoring.")
        else:
            for issue in issues:
                print(Colors.status_fail(f"  Issue: {issue}"))
                
                # Provide specific recommendations
                if "Pending" in issue:
                    analysis["recommendations"].append(
                        "1. Check insufficient resources: kubectl describe pod <pod> -n <ns>"
                    )
                    analysis["recommendations"].append(
                        "2. Check node capacity: kubectl get nodes -o wide"
                    )
                elif "Failed" in issue:
                    analysis["recommendations"].append(
                        "1. Check pod events: kubectl describe pod <pod> -n <ns>"
                    )
                    analysis["recommendations"].append(
                        "2. Check image exists: kubectl get pod <pod> -n <ns> -o yaml | grep image"
                    )
                elif "CrashLoopBackOff" in issue:
                    analysis["recommendations"].append(
                        "1. Check application logs: kubectl logs <pod> -n <ns>"
                    )
                    analysis["recommendations"].append(
                        "2. Check previous logs: kubectl logs --previous <pod> -n <ns>"
                    )
                elif "exit code" in issue.lower():
                    analysis["recommendations"].append(
                        "1. Check application configuration"
                    )
                    analysis["recommendations"].append(
                        "2. Verify environment variables are set correctly"
                    )
        
        for warning in warnings:
            print(Colors.status_warn(f"  Warning: {warning}"))
        
        if analysis["recommendations"]:
            print()
            print(Colors.header("💡 Recommendations:"))
            for rec in analysis["recommendations"]:
                print(f"  • {rec}")
        
        print()
        return analysis
    
    def debug_service(self, svc_name: str, namespace: Optional[str] = None) -> Dict[str, Any]:
        """Debug a specific service - comprehensive analysis."""
        ns = namespace or self.namespace
        
        print(f"🔍 Debugging Service: {svc_name}")
        print(f"Namespace: {ns}")
        print(f"Context: {self.context}\n")
        
        issues = []
        warnings = []
        
        # 1. Get service details
        result = self._run_kubectl("get", "svc", svc_name, "-n", ns, "-o", "json")
        if not result.get("success"):
            return {"error": f"Failed to get service: {result.get('error')}"}
        
        import json
        svc = json.loads(result["output"])
        
        # 2. Service specification
        spec = svc.get("spec", {})
        svc_type = spec.get("type", "ClusterIP")
        cluster_ip = spec.get("clusterIP", "None")
        external_ip = spec.get("externalIPs", [])
        ports = spec.get("ports", [])
        
        print(Colors.header("📊 Service Status:"))
        print(f"  Type: {svc_type}")
        print(f"  ClusterIP: {cluster_ip}")
        if external_ip:
            print(f"  External IPs: {external_ip}")
        print(f"  Ports: {ports}")
        
        print()
        
        # 3. Check endpoints
        print(Colors.header("🔗 Endpoints:"))
        ep_result = self._run_kubectl("get", "endpoints", svc_name, "-n", ns, "-o", "json")
        if ep_result.get("success"):
            try:
                ep_data = json.loads(ep_result["output"])
                subsets = ep_data.get("subsets", [])
                if not subsets:
                    issues.append("Service has no endpoints - no pods are backing this service")
                    print(Colors.status_fail("  No endpoints found - no pods are backing this service"))
                else:
                    print(Colors.status_ok("  Endpoints found"))
                    for subset in subsets:
                        addresses = subset.get("addresses", [])
                        ports = subset.get("ports", [])
                        print(f"    Addresses: {len(addresses)} endpoint(s)")
                        print(f"    Ports: {ports}")
            except:
                print("  Could not parse endpoints")
        
        print()
        
        # 4. Check selector
        selector = spec.get("selector", {})
        if selector:
            print(Colors.header("🎯 Selector:"))
            print(f"  {selector}")
            
            # Find pods matching selector
            selector_str = ",".join([f"{k}={v}" for k, v in selector.items()])
            pods_result = self._run_kubectl("get", "pods", "-n", ns, "-l", selector_str, "-o", "json")
            if pods_result.get("success"):
                try:
                    pods_data = json.loads(pods_result["output"])
                    matching_pods = pods_data.get("items", [])
                    ready_pods = 0
                    for pod in matching_pods:
                        phase = pod.get("status", {}).get("phase")
                        if phase == "Running":
                            ready_pods += 1
                    
                    if ready_pods == 0:
                        warnings.append(f"No pods matching selector {selector_str} are running")
                        print(Colors.status_warn(f"  {len(matching_pods)} pods match selector, {ready_pods} are ready"))
                    else:
                        print(Colors.status_ok(f"  {ready_pods}/{len(matching_pods)} pods are ready"))
                except:
                    print("  Could not check matching pods")
        else:
            print(Colors.header("🎯 Selector:"))
            print("  No selector (headless service)")
        
        print()
        
        # 5. Service events
        print(Colors.header("📋 Recent Events:"))
        events_result = self._run_kubectl("get", "events", "-n", ns, 
                                        "--field-selector=involvedObject.name=" + svc_name,
                                        "--sort-by=.lastTimestamp", "-o", "json")
        if events_result.get("success"):
            try:
                events = json.loads(events_result["output"]).get("items", [])[-5:]
                for event in events:
                    event_type = event.get("type", "Normal")
                    msg = event.get("message", "")
                    print(f"  [{event_type}] {msg}")
            except:
                print("  No recent events")
        
        print()
        
        # 6. AI Analysis
        return self._ai_analyze_service(svc, issues, warnings)
    
    def _ai_analyze_service(self, svc: Dict, issues: List, warnings: List) -> Dict[str, Any]:
        """AI-powered service analysis."""
        print(Colors.header("🤖 AI Analysis:"))
        
        svc_name = svc.get("metadata", {}).get("name", "unknown")
        namespace = svc.get("metadata", {}).get("namespace", "default")
        
        analysis = {
            "service": svc_name,
            "namespace": namespace,
            "issues": issues,
            "warnings": warnings,
            "recommendations": []
        }
        
        if not issues and not warnings:
            print(Colors.status_ok("Service appears healthy! No issues detected."))
            analysis["recommendations"].append("Service is healthy. Continue monitoring.")
        else:
            for issue in issues:
                print(Colors.status_fail(f"  Issue: {issue}"))
                
                if "no endpoints" in issue.lower():
                    analysis["recommendations"].append(
                        "1. Check if pods are running: kubectl get pods -n <ns>"
                    )
                    analysis["recommendations"].append(
                        "2. Verify pod labels match service selector"
                    )
                    analysis["recommendations"].append(
                        "3. Check pod readiness: kubectl describe pod <pod> -n <ns>"
                    )
        
        for warning in warnings:
            print(Colors.status_warn(f"  Warning: {warning}"))
        
        if analysis["recommendations"]:
            print()
            print(Colors.header("💡 Recommendations:"))
            for rec in analysis["recommendations"]:
                print(f"  • {rec}")
        
        print()
        return analysis
    
    def debug_gateway(self, gateway_name: str, namespace: Optional[str] = None) -> Dict[str, Any]:
        """Debug an Ingress or Gateway - comprehensive analysis."""
        ns = namespace or self.namespace
        
        print(f"🔍 Debugging Ingress/Gateway: {gateway_name}")
        print(f"Namespace: {ns}")
        print(f"Context: {self.context}\n")
        
        issues = []
        warnings = []
        
        # 1. Try Ingress first, then Gateway
        result = self._run_kubectl("get", "ingress", gateway_name, "-n", ns, "-o", "json")
        ingress_class = "ingress"
        
        if not result.get("success"):
            # Try Gateway (Istio or Kubernetes Gateway API)
            result = self._run_kubectl("get", "gateway", gateway_name, "-n", ns, "-o", "json")
            ingress_class = "gateway"
        
        if not result.get("success"):
            return {"error": f"Failed to get ingress/gateway: {result.get('error')}"}
        
        import json
        gw = json.loads(result["output"])
        
        # 2. Gateway specification
        spec = gw.get("spec", {}, {})
        
        print(Colors.header("📊 Gateway Status:"))
        print(f"  Type: {ingress_class.capitalize()}")
        
        if ingress_class == "ingress":
            ingress_class_name = spec.get("ingressClassName", "")
            if ingress_class_name:
                print(f"  Ingress Class: {ingress_class_name}")
        else:
            gateway_class = spec.get("gatewayClassName", "")
            if gateway_class:
                print(f"  Gateway Class: {gateway_class}")
        
        print()
        
        # 3. Check address/hostname
        print(Colors.header("🌐 Addresses:"))
        if ingress_class == "ingress":
            hosts = spec.get("rules", [])
            if hosts:
                for rule in hosts:
                    host = rule.get("host", "*")
                    paths = rule.get("http", {}).get("paths", [])
                    print(f"  Host: {host}")
                    for path in paths:
                        path_str = path.get("path", "/")
                        backend = path.get("backend", {})
                        if backend.get("service"):
                            svc_name = backend["service"].get("name", "unknown")
                            svc_port = backend["service"].get("port", {})
                            print(f"    Path: {path_str} -> Service: {svc_name}")
            else:
                print("  No rules defined")
        else:
            # Gateway listeners
            listeners = spec.get("listeners", [])
            for listener in listeners:
                name = listener.get("name", "unknown")
                protocol = listener.get("protocol", "unknown")
                port = listener.get("port", "unknown")
                print(f"  Listener: {name} ({protocol}:{port})")
        
        print()
        
        # 4. Check if backend services exist
        print(Colors.header("🔗 Backend Services:"))
        if ingress_class == "ingress":
            for rule in hosts:
                paths = rule.get("http", {}).get("paths", [])
                for path in paths:
                    backend = path.get("backend", {})
                    if backend.get("service"):
                        svc_name = backend["service"].get("name", "unknown")
                        svc_port = backend["service"].get("port", {})
                        
                        # Check if service exists
                        svc_result = self._run_kubectl("get", "svc", svc_name, "-n", ns, "-o", "json")
                        if svc_result.get("success"):
                            print(Colors.status_ok(f"  Service {svc_name}: exists"))
                        else:
                            issues.append(f"Backend service {svc_name} does not exist")
                            print(Colors.status_fail(f"  Service {svc_name}: NOT FOUND"))
        else:
            print("  Gateway backend check not implemented")
        
        print()
        
        # 5. Check for ingress controller
        print(Colors.header("🎮 Ingress Controller:"))
        if ingress_class == "ingress" and ingress_class_name:
            # Check if ingress class exists
            ic_result = self._run_kubectl("get", "ingressclass", ingress_class_name, "-o", "json")
            if ic_result.get("success"):
                try:
                    ic_data = json.loads(ic_result["output"])
                    controller = ic_data.get("spec", {}).get("controller", "unknown")
                    print(f"  Controller: {controller}")
                except:
                    print("  Could not parse ingress class")
            else:
                print(Colors.status_warn(f"  Ingress class {ingress_class_name} not found"))
        
        print()
        
        # 6. Gateway events
        print(Colors.header("📋 Recent Events:"))
        events_result = self._run_kubectl("get", "events", "-n", ns, 
                                        "--field-selector=involvedObject.name=" + gateway_name,
                                        "--sort-by=.lastTimestamp", "-o", "json")
        if events_result.get("success"):
            try:
                events = json.loads(events_result["output"]).get("items", [])[-5:]
                for event in events:
                    event_type = event.get("type", "Normal")
                    msg = event.get("message", "")
                    print(f"  [{event_type}] {msg}")
            except:
                print("  No recent events")
        
        print()
        
        # 7. AI Analysis
        return self._ai_analyze_gateway(gw, issues, warnings, ingress_class)
    
    def _ai_analyze_gateway(self, gw: Dict, issues: List, warnings: List, gateway_type: str) -> Dict[str, Any]:
        """AI-powered gateway analysis."""
        print(Colors.header("🤖 AI Analysis:"))
        
        gw_name = gw.get("metadata", {}).get("name", "unknown")
        namespace = gw.get("metadata", {}).get("namespace", "default")
        
        analysis = {
            "gateway": gw_name,
            "namespace": namespace,
            "type": gateway_type,
            "issues": issues,
            "warnings": warnings,
            "recommendations": []
        }
        
        if not issues and not warnings:
            print(Colors.status_ok("Gateway appears healthy! No issues detected."))
            analysis["recommendations"].append("Gateway is healthy. Continue monitoring.")
        else:
            for issue in issues:
                print(Colors.status_fail(f"  Issue: {issue}"))
                
                if "does not exist" in issue.lower():
                    analysis["recommendations"].append(
                        "1. Check service name in ingress definition"
                    )
                    analysis["recommendations"].append(
                        "2. Verify backend service is created"
                    )
        
        for warning in warnings:
            print(Colors.status_warn(f"  Warning: {warning}"))
        
        if analysis["recommendations"]:
            print()
            print(Colors.header("💡 Recommendations:"))
            for rec in analysis["recommendations"]:
                print(f"  • {rec}")
        
        print()
        return analysis
    
    def quick_check(self) -> Dict[str, Any]:
        """Quick health check of cluster."""
        print(Colors.header("🚀 Quick Cluster Health Check"))
        print(f"{Colors.CYAN}Context:{Colors.ENDC} {self.context}")
        print(f"{Colors.CYAN}Time:{Colors.ENDC} {datetime.now().isoformat()}\n")
        
        issues = []
        
        # Check nodes
        print(Colors.header("📊 Nodes:"))
        nodes = self.get_nodes()
        healthy_nodes = 0
        
        for node in nodes:
            name = node.get("metadata", {}).get("name", "unknown")
            conditions = node.get("status", {}).get("conditions", [])
            
            ready = next((c for c in conditions if c.get("type") == "Ready"), {})
            if ready.get("status") == "True":
                print(Colors.status_ok(f"  {name}: Ready"))
                healthy_nodes += 1
            else:
                reason = ready.get("reason", "Unknown")
                print(Colors.status_fail(f"  {name}: NotReady ({reason})"))
                issues.append(f"Node {name} is not ready: {reason}")
        
        print()
        
        # Check pods
        print(Colors.header("📦 Pods:"))
        pods = self.get_pods()
        pod_issues = []
        
        for pod in pods:
            name = pod.get("metadata", {}).get("name", "unknown")
            namespace = pod.get("metadata", {}).get("namespace", "default")
            phase = pod.get("status", {}).get("phase", "Unknown")
            
            if phase != "Running" and phase != "Succeeded":
                pod_issues.append(f"{namespace}/{name}: {phase}")
        
        if pod_issues:
            for issue in pod_issues:
                print(Colors.status_fail(f"  {issue}"))
                issues.append(f"Pod {issue} is not running")
        else:
            print(Colors.status_ok(f"  All {len(pods)} pods are healthy"))
        
        print()
        
        # Summary
        print(Colors.header("📈 Summary:"))
        print(f"  Total Nodes: {len(nodes)}")
        print(f"  Healthy Nodes: {healthy_nodes}")
        print(f"  Total Pods: {len(pods)}")
        print(f"  Pod Issues: {len(pod_issues)}")
        
        if issues:
            print()
            print(Colors.status_fail(f"  Found {len(issues)} issues!"))
        else:
            print()
            print(Colors.status_ok("  Cluster is healthy!"))
        
        return {
            "healthy": len(issues) == 0,
            "total_nodes": len(nodes),
            "healthy_nodes": healthy_nodes,
            "total_pods": len(pods),
            "issues": issues
        }


def main():
    parser = argparse.ArgumentParser(
        description="K8s Debugger - AI-Powered Kubernetes Node & Pod Debugging Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python k8s_debugger.py quick-check
  python k8s_debugger.py node worker-node-1
  python k8s_debugger.py pod my-app -n default
  python k8s_debugger.py cluster
        """
    )
    
    parser.add_argument("command", help="Command to run",
                      choices=["node", "pod", "svc", "gateway", "cluster", "quick-check", "analyze"])
    parser.add_argument("target", nargs="?", help="Target name (node/pod/service/gateway name)")
    parser.add_argument("-n", "--namespace", default="default", 
                        help="Namespace for pod commands")
    parser.add_argument("-o", "--output", choices=["json", "text"], default="text",
                        help="Output format")
    
    args = parser.parse_args()
    
    # Initialize debugger
    debugger = K8sDebugger(namespace=args.namespace)
    
    # Execute command
    if args.command == "quick-check":
        result = debugger.quick_check()
    elif args.command == "node":
        if not args.target:
            print("Error: node name required")
            print("Usage: python k8s_debugger.py node <node-name>")
            sys.exit(1)
        result = debugger.debug_node(args.target)
    elif args.command == "pod":
        if not args.target:
            print("Error: pod name required")
            print("Usage: python k8s_debugger.py pod <pod-name> -n <namespace>")
            sys.exit(1)
        result = debugger.debug_pod(args.target, args.namespace)
    elif args.command == "svc":
        if not args.target:
            print("Error: service name required")
            print("Usage: python k8s_debugger.py svc <service-name> -n <namespace>")
            sys.exit(1)
        result = debugger.debug_service(args.target, args.namespace)
    elif args.command == "gateway":
        if not args.target:
            print("Error: gateway/ingress name required")
            print("Usage: python k8s_debugger.py gateway <gateway-name> -n <namespace>")
            sys.exit(1)
        result = debugger.debug_gateway(args.target, args.namespace)
    elif args.command == "cluster":
        result = debugger.quick_check()
    elif args.command == "analyze":
        # AI analysis of entire cluster
        print(Colors.header("🤖 AI-Powered Cluster Analysis"))
        nodes = debugger.get_nodes()
        pods = debugger.get_pods()
        
        # Get all issues
        cluster_issues = []
        
        for node in nodes:
            name = node.get("metadata", {}).get("name", "unknown")
            conditions = node.get("status", {}).get("conditions", [])
            ready = next((c for c in conditions if c.get("type") == "Ready"), {})
            if ready.get("status") != "True":
                cluster_issues.append(f"Node {name} is not ready")
        
        for pod in pods:
            name = pod.get("metadata", {}).get("name", "unknown")
            phase = pod.get("status", {}).get("phase", "Unknown")
            if phase not in ["Running", "Succeeded"]:
                cluster_issues.append(f"Pod {name} is {phase}")
        
        print(f"\nClusters have {len(cluster_issues)} issues")
        result = {"issues": cluster_issues}
    
    # Output result
    if args.output == "json":
        print(json.dumps(result, indent=2))
    
    return 0 if result.get("error") is None else 1


if __name__ == "__main__":
    sys.exit(main())