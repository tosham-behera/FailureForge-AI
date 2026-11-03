from .schemas import Diagnosis


# Deterministic example diagnoses for offline UI testing; these are not AI results.
def diagnose_demo(logs: str) -> Diagnosis:
    low = logs.lower()
    if "eaddrinuse" in low or "address already in use" in low:
        return Diagnosis(
            failure_type="Port conflict", severity="medium", confidence="high",
            summary="The application could not start because its port is already occupied.",
            probable_root_cause="Another process is using the port your application is trying to bind.",
            evidence=["The logs include EADDRINUSE or 'address already in use'."],
            recommended_checks=[
                "Check which process is listening on the reported port.",
                "Confirm whether you accidentally started the application twice.",
                "Stop only the unwanted process or select another port, then restart the app.",
            ],
        )
    if "econnrefused" in low or "connection refused" in low:
        return Diagnosis(
            failure_type="Connection refused", severity="high", confidence="medium",
            summary="Your app attempted to connect to a service, but the connection was refused.",
            probable_root_cause="The target service may be down, listening on a different port, or unreachable at the configured address.",
            evidence=["The logs include ECONNREFUSED or 'connection refused'."],
            recommended_checks=[
                "Verify that the target service is running and listening on the expected port.",
                "Check the host and port configured in your environment variables.",
                "If using Docker, verify service names and networking before changing code.",
            ],
        )
    if "etimedout" in low or "timed out" in low or "timeout" in low:
        return Diagnosis(
            failure_type="Request timeout", severity="medium", confidence="medium",
            summary="A request took longer than the configured timeout.",
            probable_root_cause="The remote service may be slow, overloaded, or unreachable; more data is required.",
            evidence=["The logs mention a timeout."],
            recommended_checks=[
                "Measure the failing request duration and identify its dependency.",
                "Check service health, connectivity, and resource utilization.",
                "Review timeout settings only after investigating the slow operation.",
            ],
        )
    return Diagnosis(
        failure_type="Unknown", severity="low", confidence="low",
        summary="No known demo pattern matched these logs.",
        probable_root_cause="Insufficient information in offline demo mode.",
        evidence=["No EADDRINUSE, ECONNREFUSED, or timeout signature was found."],
        recommended_checks=[
            "Check earlier log lines for the original exception.",
            "Switch to Meta mode to attempt a model-based diagnosis after reviewing log privacy.",
        ],
    )
