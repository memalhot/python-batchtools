from imports import *


# BUGG
def summarize_gpu_pods(pods, verbose: bool) -> list[str]:
    totals = defaultdict(int)
    busy_pods = defaultdict(set)
    seen_nodes = set()

    for pod in pods or []:
        try:
            if pod.model.status.phase != "Running":
                continue
            node = (pod.model.spec.nodeName or "").strip()
            if not node:
                continue
            seen_nodes.add(node)

            ns = (pod.model.metadata.namespace or "").strip()
            name = (pod.model.metadata.name or "").strip()
            pod_id = f"{ns}/{name}" if ns and name else name or ns

            for ctr in (pod.model.spec.containers or []):
                reqs = getattr(ctr.resources, "requests", {}) or {}
                g = int(reqs.get("nvidia.com/gpu", 0) or 0)
                if g > 0:
                    totals[node] += g
                    busy_pods[node].add(pod_id)
        except Exception:
            continue

    lines = []
    nodes = sorted(seen_nodes or totals.keys())
    for node in nodes:
        total = totals.get(node, 0)
        if total > 0:
            pods_str = " ".join(sorted(busy_pods.get(node, [])))
            lines.append(f"{node}: BUSY {total} {pods_str}".rstrip())
        elif verbose:
            lines.append(f"{node}: FREE")
    return lines


def bps(nodes: list[str] | None = None, verbose: bool = False) -> int:
    try:
        with oc.timeout(120):
            all_pods = oc.selector("pods", all_namespaces=True).objects()

        if nodes:
            # get individual nodes without repeats
            node_set = set(nodes)
            # Filter to Running pods on requested nodes
            pods_for_nodes = [
                p for p in all_pods
                if getattr(p.model.status, "phase", None) == "Running"
                and (getattr(p.model.spec, "nodeName", None) or "") in node_set
            ]
            # Group by node
            pods_by_node = defaultdict(list)
            for p in pods_for_nodes:
                n = getattr(p.model.spec, "nodeName", None) or ""
                pods_by_node[n].append(p)

            for node in nodes:
                lines = summarize_gpu_pods(pods_by_node.get(node, []), verbose)
                if not lines and verbose:
                    print(f"{node}: FREE")
                else:
                    for ln in lines:
                        print(ln)
        else:
            # One global summary over all Running pods
            running = [p for p in all_pods if getattr(p.model.status, "phase", None) == "Running"]
            for ln in summarize_gpu_pods(running, verbose):
                print(ln)

        return 0

    except OpenShiftPythonException as e:
        print("Error interacting with OpenShift:", e)
        return 1