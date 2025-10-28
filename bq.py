from imports import *

def bq(args) -> int:
    try:
        clusterqueues = oc.selector("clusterqueue").objects()
        if not clusterqueues:
            print("No ClusterQueues found.")
            return 0

        for cq in clusterqueues:
            cq_dict = cq.as_dict() if hasattr(cq, "as_dict") else cq.model.to_dict()
            meta = cq_dict.get("metadata", {})
            spec = cq_dict.get("spec", {})
            status = cq_dict.get("status", {})

            # calculate total GPUs across resourceGroups/flavors
            total_gpu = 0
            for rg in spec.get("resourceGroups", []) or []:
                for flav in rg.get("flavors", []) or []:
                    for res in flav.get("resources", []) or []:
                        if res.get("name") == "nvidia.com/gpu":
                            try:
                                total_gpu += int(res.get("nominalQuota", 0))
                            except (TypeError, ValueError):
                                continue

            admitted = status.get("admittedWorkloads", 0)
            pending = status.get("pendingWorkloads", 0)
            reserving = status.get("reservingWorkloads", 0)
            queueing = spec.get("queueingStrategy", "")

            print(
                f"{meta.get('name', '')}\t"
                f"admitted: {admitted}\t"
                f"pending: {pending}\t"
                f"reserved: {reserving}\t"
                f"GPUs: {total_gpu}\t"
                f"{queueing}"
            )

    except OpenShiftPythonException as e:
        print("Error occurred while retrieving ClusterQueues:")
        print(e)
        traceback.print_exc()
        return 1