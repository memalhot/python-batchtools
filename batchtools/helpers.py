import openshift_client as oc


def is_logged_in() -> bool:
    try:
        oc.invoke("whoami")
        return True
    except oc.OpenShiftPythonException:
        return False


def pretty_print(pod: oc.APIObject) -> str:
    formatted_logs: str = ""
    try:
        logs: dict[str, str] = pod.logs()
        # ⋆ ˚｡⋆୨୧˚ stringify and pretty print for readibility ⋆ ˚｡⋆୨୧˚
        formatted_logs = str(logs).replace("\\n", "\n")
    except oc.OpenShiftPythonException as e:
        print(f"Error occurred while retrieving logs: {e}")

    return formatted_logs


def oc_delete(obj_type: str, obj_name: str) -> None:
    try:
        print(f"Deleting {obj_type}/{obj_name}")
        oc.selector(f"{obj_type}/{obj_name}").delete()
    except oc.OpenShiftPythonException as e:
        print(f"Error occurred while deleting {obj_type}/{obj_name}: {e}")


def is_kueue_managed_job(job_obj) -> bool:
    """
    Returns True if the Job is managed by Kueue.
    Checks:
      1) Job has label 'kueue.x-k8s.io/queue-name'
      2) A Workload exists that either:
         - has an ownerReference pointing to this Job, or
         - has label job-name=<job-name>
    """
    try:
        md = job_obj.model.metadata
        labels = getattr(md, "labels", {}) or {}
        if "kueue.x-k8s.io/queue-name" in labels:
            return True

        job_name = md.name
        try:
            workloads = oc.selector("workloads").objects()
        except oc.OpenShiftPythonException:
            workloads = []

        for wl in workloads:
            wl_md = wl.model.metadata
            owners = getattr(wl_md, "ownerReferences", []) or []
            for o in owners:
                if (
                    getattr(o, "kind", "") == "Job"
                    and getattr(o, "name", "") == job_name
                ):
                    return True
            wl_labels = getattr(wl_md, "labels", {}) or {}
            if wl_labels.get("job-name") == job_name:
                return True
    except Exception:
        return False

    return False
