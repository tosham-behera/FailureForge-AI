# Safe Docker verification

These fixed samples do not repair or verify the real application and make no Meta requests.

| Scenario | Before | Predefined recovery | Required after evidence |
|---|---|---|---|
| port-conflict | EADDRINUSE on 4000 | Sample listens on 4001 | HTTP 200 and expected body |
| database-connectivity | ECONNREFUSED on loopback 54321 | Start simulated TCP dependency | Connected with expected reply |

The database fixture is not MySQL. Both phases run inside one isolated container.

Build commands and test commands are in [README](README.md). Images must already exist locally. After any diagnosis, select the scenario and click Verify Fix. The API accepts only the two literal scenario names. A successful run requires status passed, docker_ran true, matching before/after evidence and cleanup_succeeded true. Recorded runs are included in reports.

Isolation: argument arrays with shell execution disabled, pinned inspected local image IDs, no implicit pulls, no host mounts or published ports, network none, read-only filesystem, user 65534, all capabilities dropped, no-new-privileges, 0.5 CPU, 64 MiB memory with no extra swap, 32 PIDs, bounded logs and a shared concurrency lock. Cleanup runs in a finally block. No model-generated commands or uploaded content are accepted for execution.

CLI operations have five-second timeouts; polling is bounded. Cold/busy Docker may time out: ensure Docker is ready and explicitly retry. Failed cleanup is surfaced with the generated container name for manual inspection. Without RUN_DOCKER_TESTS=1 the two real integration tests skip. See [verification results](VERIFICATION.md).
