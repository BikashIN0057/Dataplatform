import datetime as dt
import os
import requests
import streamlit as st


def _agent_api_ui(method, path, payload=None):
    token = ""
    base = "http://127.0.0.1:8808"
    try:
        token = st.secrets.get("REMEDIATION_SHARED_TOKEN", "")
        base = st.secrets.get("REMEDIATION_API_URL", "http://127.0.0.1:8808")
    except Exception:
        token = os.getenv("REMEDIATION_SHARED_TOKEN", "")
        base = os.getenv("REMEDIATION_API_URL", "http://127.0.0.1:8808")

    headers = {"X-Remediation-Token": token}
    if payload is None:
        r = requests.request(method, f"{base}{path}", headers=headers, timeout=120)
    else:
        r = requests.request(method, f"{base}{path}", headers=headers, json=payload, timeout=120)
    r.raise_for_status()
    return r.json()

def _agent_guess_issue_type(analysis_text):
    t = (analysis_text or "").lower()
    if "timeout" in t:
        return "dependency_timeout"
    if "crash" in t or "restart" in t or "oom" in t:
        return "crash_loop"
    if "down" in t or "inactive" in t:
        return "down"
    return "unhealthy"

def _agent_show_execution(exec_data):
    if not exec_data:
        st.info("No execution yet.")
        return

    st.markdown("#### Agent Execution Details")
    st.write(f"Dry run: `{exec_data.get('dry_run')}`")
    st.write(f"Success: `{exec_data.get('success')}`")

    steps = exec_data.get("steps", [])
    if steps:
        st.markdown("##### Step Results")
        for i, step in enumerate(steps, 1):
            title = f"Step {i}: {step.get('name', 'unnamed')} | rc={step.get('returncode', 'n/a')}"
            with st.expander(title):
                if step.get("command"):
                    st.code(step["command"], language="bash")
                st.json(step)

    validation = exec_data.get("validation", [])
    if validation:
        st.markdown("##### Validation Results")
        for i, step in enumerate(validation, 1):
            title = f"Validation {i}: {step.get('name', 'unnamed')} | ok={step.get('ok')}"
            with st.expander(title):
                if step.get("command"):
                    st.code(step["command"], language="bash")
                st.json(step)

def _render_agent_activity_panel(service_name, analysis_text):
    st.markdown("---")
    st.subheader("Agent Activity & Admin Approval")
    st.caption("Agent request is created first. Admin approval happens only when you click 'Admin Approve and Execute' below.")

    current_service = service_name or st.session_state.get("selected_service") or "grafana"
    default_issue = _agent_guess_issue_type(analysis_text)

    default_evidence = {
        "source": "logs_page",
        "service_name": current_service,
        "container_name": current_service,
        "compose_service": current_service,
        "analysis_excerpt": (analysis_text or "")[:2000],
    }

    ctop1, ctop2 = st.columns([1, 1])

    runtime = ctop1.selectbox(
        "Runtime",
        ["systemd", "docker", "docker-compose"],
        key="agent_runtime_ui"
    )

    issue_options = ["unhealthy", "down", "crash_loop", "dependency_timeout"]
    issue_type = ctop2.selectbox(
        "Issue type",
        issue_options,
        index=issue_options.index(default_issue),
        key="agent_issue_type_ui"
    )

    service_name = st.text_input(
        "Service for agent request",
        value=current_service,
        key="agent_service_name_ui"
    )

    approved_by = st.text_input(
        "Approved by (admin name)",
        value=st.session_state.get("agent_approved_by_ui", "admin"),
        key="agent_approved_by_ui"
    )

    evidence_text = st.text_area(
        "Evidence JSON sent to agent",
        value=json.dumps(default_evidence, indent=2),
        height=180,
        key="agent_evidence_ui"
    )

    c1, c2, c3, c4 = st.columns(4)

    if c1.button("Create Agent Request", key="agent_create_request_btn", use_container_width=True):
        try:
            evidence = json.loads(evidence_text) if evidence_text.strip() else {}
            evidence.setdefault("service_name", service_name)
            evidence.setdefault("container_name", service_name)
            evidence.setdefault("compose_service", service_name)

            resp = _agent_api_ui(
                "POST",
                "/incidents/propose",
                {
                    "service": service_name,
                    "runtime": runtime,
                    "issue_type": issue_type,
                    "node": "local",
                    "evidence": evidence,
                },
            )
            st.session_state["agent_incident_id_ui"] = resp["incident_id"]
            st.success(f"Agent request created: {resp['incident_id']}")
            st.json(resp)
        except Exception as e:
            st.exception(e)

    incident_id = st.session_state.get("agent_incident_id_ui", "")
    incident = None

    if incident_id:
        try:
            incident = _agent_api_ui("GET", f"/incidents/{incident_id}")
            st.info(
                f"Incident ID: {incident['id']} | Status: {incident['status']} | Risk: {incident['risk']} | Service: {incident['service']}"
            )
        except Exception as e:
            st.exception(e)

    if c2.button("Refresh Agent Status", key="agent_refresh_status_btn", use_container_width=True):
        if incident_id:
            try:
                incident = _agent_api_ui("GET", f"/incidents/{incident_id}")
                st.session_state["agent_last_result_ui"] = incident
                st.success("Agent status refreshed.")
                st.json(incident)
            except Exception as e:
                st.exception(e)
        else:
            st.warning("Create an agent request first.")

    if c3.button("Dry Run Agent Request", key="agent_dry_run_btn", use_container_width=True):
        if incident_id:
            try:
                resp = _agent_api_ui(
                    "POST",
                    f"/incidents/{incident_id}/approve",
                    {"approved_by": approved_by, "dry_run": True},
                )
                st.session_state["agent_last_result_ui"] = resp
                st.success("Dry run completed.")
                st.json(resp)
            except Exception as e:
                st.exception(e)
        else:
            st.warning("Create an agent request first.")

    if c4.button("Admin Approve and Execute", key="agent_approve_execute_btn", use_container_width=True):
        if incident_id:
            try:
                resp = _agent_api_ui(
                    "POST",
                    f"/incidents/{incident_id}/approve",
                    {"approved_by": approved_by, "dry_run": False},
                )
                st.session_state["agent_last_result_ui"] = resp
                st.success(f"Execution sent with admin approval by: {approved_by}")
                st.json(resp)
            except Exception as e:
                st.exception(e)
        else:
            st.warning("Create an agent request first.")

    if incident:
        with st.expander("Agent Proposed Runbook", expanded=True):
            remedy = incident.get("remedy", {})
            steps = remedy.get("steps", [])
            validation = remedy.get("validation", [])

            st.write(f"Runbook ID: `{remedy.get('id', 'n/a')}`")
            st.write(f"Title: `{remedy.get('title', 'n/a')}`")
            st.write(f"Risk: `{incident.get('risk', 'n/a')}`")

            if steps:
                st.markdown("##### Planned Steps")
                for i, step in enumerate(steps, 1):
                    st.write(f"{i}. {step.get('name', 'unnamed')}")
                    if step.get("command"):
                        st.code(step["command"], language="bash")

            if validation:
                st.markdown("##### Validation Checks")
                for i, step in enumerate(validation, 1):
                    st.write(f"{i}. {step.get('name', 'unnamed')}")
                    if step.get("command"):
                        st.code(step["command"], language="bash")

    last = st.session_state.get("agent_last_result_ui")
    if last:
        _agent_show_execution(last.get("execution") if isinstance(last, dict) else None)

    with st.expander("Recent Agent Requests"):
        try:
            incidents = _agent_api_ui("GET", "/incidents")
            st.json(incidents)
        except Exception as e:
            st.exception(e)

from datetime import datetime, timedelta, timezone
from collections import Counter

try:
    from confluent_kafka.admin import AdminClient, NewTopic

    KAFKA_BOOTSTRAP = os.getenv("KAFKA_BOOTSTRAP", "10.155.38.64:9092")
    admin = AdminClient({"bootstrap.servers": KAFKA_BOOTSTRAP})

    def create_topic_if_not_exists(topic: str, partitions: int = 3, replication: int = 1):
        md = admin.list_topics(timeout=10)
        if topic in md.topics and md.topics[topic].error is None:
            return {"topic": topic, "status": "EXISTS"}
        new_topic = NewTopic(topic=topic, num_partitions=partitions, replication_factor=replication)
        fs = admin.create_topics([new_topic])
        try:
            fs[topic].result()
            return {"topic": topic, "status": "CREATED"}
        except Exception as exc:
            return {"topic": topic, "status": "ERROR", "error": str(exc)}
except Exception:
    def create_topic_if_not_exists(topic: str, partitions: int = 3, replication: int = 1):
        return {"topic": topic, "status": "ERROR", "error": "confluent_kafka is not available in this environment"}

GRAFANA_BASE = os.getenv("GRAFANA_BASE_URL", "http://10.155.38.64:3000")
LOKI_BASE = os.getenv("LOKI_BASE_URL", "http://10.155.38.64:3100")
OBS_AI_API_URL = os.getenv("OBS_AI_API_URL", "http://localhost:8088")
LLM_PROVIDER_DEFAULT = os.getenv("LLM_PROVIDER_DEFAULT", "auto")

LOKI_RETENTION_PERIOD = os.getenv("LOKI_RETENTION_PERIOD", "7d")
LOKI_ARCHIVAL_MECHANISM = os.getenv("LOKI_ARCHIVAL_MECHANISM", "Not configured")
LOKI_PURGING_MECHANISM = os.getenv("LOKI_PURGING_MECHANISM", "Retention-based deletion")

TIME_RANGES = {
    "Last 15 min": 15 * 60,
    "Last 1 hour": 60 * 60,
    "Last 6 hours": 6 * 60 * 60,
    "Last 24 hours": 24 * 60 * 60,
}

SERVICE_LOG_QUERIES = {
    "kafka": ['{service_name="kafka-control-api"}'],

    "grafana": ['{service_name="obs-grafana"}'],

    "prometheus": ['{service_name="obs-prometheus"}'],

    "loki": ['{service_name="obs-loki"}'],

    "minio": ['{service_name="obs-alloy"}'],

    "spark": ['{service_name="obs-alloy"}']
}

def _ns(dt: datetime) -> str:
    return str(int(dt.timestamp() * 1_000_000_000))

def _iso(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")

def build_grafana_logs_url(service: str) -> str:
    return f"{GRAFANA_BASE}/explore"

def loki_ready():
    try:
        r = requests.get(f"{LOKI_BASE}/ready", timeout=3)
        return r.status_code == 200, f"HTTP {r.status_code}"
    except Exception as exc:
        return False, str(exc)

def fetch_logs_from_loki(service: str, seconds: int, limit: int = 400):
    queries = SERVICE_LOG_QUERIES.get(service.lower(), [f'{{job="{service.lower()}"}}'])
    end_dt = datetime.now(timezone.utc)
    start_dt = end_dt - timedelta(seconds=seconds)

    seen = set()
    collected = []
    used_query = None
    last_error = None

    for query in queries:
        used_query = query
        try:
            r = requests.get(
                f"{LOKI_BASE}/loki/api/v1/query_range",
                params={"query": query, "start": _ns(start_dt), "end": _ns(end_dt), "limit": str(limit), "direction": "BACKWARD"},
                timeout=20,
            )
            r.raise_for_status()
            payload = r.json()
            for stream in payload.get("data", {}).get("result", []):
                for _, line in stream.get("values", []):
                    item = line.strip()
                    if item and item not in seen:
                        seen.add(item)
                        collected.append(item)
            if collected:
                break
        except Exception as exc:
            last_error = str(exc)

    return collected[:limit], used_query, last_error, start_dt, end_dt

def classify_levels(lines):
    c = Counter()
    for line in lines:
        s = line.lower()
        if "unhealthy" in s:
            c["unhealthy"] += 1
        elif "healthy" in s:
            c["healthy"] += 1
        if "error" in s or s.startswith("error"):
            c["error"] += 1
        if "info" in s or s.startswith("info"):
            c["info"] += 1
        if "warn" in s or s.startswith("warn") or "warning" in s:
            c["warn"] += 1
    return c

def call_summary_api(query: str, start_dt: datetime, end_dt: datetime, provider: str):
    payload = {
        "query": query,
        "start": _iso(start_dt),
        "end": _iso(end_dt),
        "limit": 200,
        "provider": provider
    }
    r = requests.post(f"{OBS_AI_API_URL}/summarize", json=payload, timeout=120)
    r.raise_for_status()
    return r.json()

def render_housekeeping():
    st.subheader("Loki Housekeeping")
    c1, c2, c3 = st.columns(3)
    c1.metric("Retention Period", LOKI_RETENTION_PERIOD)
    c2.metric("Archival Mechanism", LOKI_ARCHIVAL_MECHANISM)
    c3.metric("Purging Mechanism", LOKI_PURGING_MECHANISM)

    ok, msg = loki_ready()
    if ok:
        st.success(f"Loki ready: {msg}")
    else:
        st.error(f"Loki not ready: {msg}")

    st.markdown("""
### Cleanup Notes
- **Retention Period** controls how long Loki keeps logs.
- **Archival Mechanism** describes where older logs are moved, if configured.
- **Purging Mechanism** describes how expired logs are removed.
""")

def render_kafka_helper():

    try:
        _render_agent_activity_panel(
            selected_service if "selected_service" in locals() else st.session_state.get("selected_service", "grafana"),
            str(locals().get("analysis_result", locals().get("ai_result", "")))
        )
    except Exception as e:
        st.error(f"Agent panel failed: {e}")

    with st.expander("Kafka Topic Utility"):
        topic = st.text_input("Kafka topic name", value="demo-topic")
        partitions = st.number_input("Partitions", min_value=1, value=3, step=1)
        replication = st.number_input("Replication factor", min_value=1, value=1, step=1)
        if st.button("Create Topic If Not Exists"):
            st.json(create_topic_if_not_exists(topic, int(partitions), int(replication)))

def render_counts(counts):
    c1, c2, c3, c4, c5 = st.columns(5)
    c2.metric("Unhealthy", counts.get("unhealthy", 0))
    c3.metric("Error", counts.get("error", 0))
    c4.metric("Info", counts.get("info", 0))
    c5.metric("Warn", counts.get("warn", 0))

def page_logs():
    st.title("Logs")
    render_housekeeping()
    st.divider()

    services_list = ["kafka", "minio", "spark", "prometheus", "grafana", "loki"]
    now = dt.datetime.now().replace(second=0, microsecond=0)
    default_start = now - dt.timedelta(hours=1)

    col1, col2 = st.columns(2)
    with col1:
        selected_services = st.multiselect("Select Service(s)", services_list, default=["kafka"])
    with col2:
        limit = st.number_input("Log Limit", min_value=100, max_value=5000, value=500, step=100)

    col3, col4 = st.columns(2)
    with col3:
        start_date = st.date_input("Start Date", value=default_start.date())
        start_time = st.time_input("Start Time", value=default_start.time().replace(second=0, microsecond=0), step=60)
    with col4:
        end_date = st.date_input("End Date", value=now.date())
        end_time = st.time_input("End Time", value=now.time().replace(second=0, microsecond=0), step=60)

    start_dt = dt.datetime.combine(start_date, start_time).replace(second=0, microsecond=0)
    end_dt = dt.datetime.combine(end_date, end_time).replace(second=0, microsecond=0)

    if selected_services:
        st.markdown(f"[Open Grafana Logs Dashboard]({build_grafana_logs_url(selected_services[0])})")

    if st.button("Load Logs"):
        if not selected_services:
            st.warning("Please select at least one service.")
            st.stop()

        if end_dt <= start_dt:
            st.error("End date/time must be greater than start date/time.")
            st.stop()

        all_lines = []
        last_error = None
        used_queries = []

        for service in selected_services:
            lines, used_query, err, _, _ = fetch_logs_from_loki(service, TIME_RANGES["Last 1 hour"])
            all_lines.extend(lines)
            if used_query:
                used_queries.append(f"{service}: {used_query}")
            if err:
                last_error = err

        counts = classify_levels(all_lines)
        render_counts(counts)
        st.caption("Loki queries used: " + (" | ".join(used_queries) if used_queries else "N/A"))

        if last_error and not all_lines:
            st.warning(f"Loki query returned no logs. Last error seen: {last_error}")

        if all_lines:
            with st.expander("Sample Log Lines", expanded=True):
                st.code("\n".join(all_lines[:int(limit)]), language="text")
        else:
            st.info("No logs found for the selected services and time range.")

    st.divider()
    st.subheader("Analyze Logs with AI")

    ai_provider = st.selectbox(
        "Choose AI Provider for Analysis",
        ["auto", "ollama", "openai"],
        index=["auto", "ollama", "openai"].index(LLM_PROVIDER_DEFAULT if LLM_PROVIDER_DEFAULT in {"auto", "ollama", "openai"} else "auto"),
        key="logs_ai_provider"
    )

    if st.button("Analyze Logs and Get Exact Remedy", type="primary"):
        if not selected_services:
            st.warning("Select at least one service first")
            st.stop()
        lines, used_query, last_error, start_dt, end_dt = fetch_logs_from_loki(selected_services[0], TIME_RANGES["Last 1 hour"])

        if last_error and not lines:
            st.warning(f"Loki query returned no logs. Last error seen: {last_error}")

        if not lines:
            st.info("No logs available to analyze.")
        else:
            counts = classify_levels(lines)
            render_counts(counts)
            st.caption(f"Loki query used: {used_query or 'N/A'}")

            try:
                with st.spinner(f"Analyzing logs with provider: {ai_provider}"):
                    data = call_summary_api(used_query, start_dt, end_dt, ai_provider)

                st.markdown("### Log Summary")
                st.write(data.get("summary", "No summary returned."))

                st.markdown("### Exact Error")
                st.write(data.get("root_cause", "No root cause returned."))

                st.markdown("### Remedy Steps")
                remedy = data.get("remedy", "")
                if isinstance(remedy, list):
                    for idx, step in enumerate(remedy, 1):
                        st.write(f"{idx}. {step}")
                else:
                    st.write(remedy or "No remedy returned.")

                st.markdown("### Confidence")
                st.write(data.get("confidence", "unknown"))

                if data.get("patterns"):
                    with st.expander("Detected patterns"):
                        st.json(data.get("patterns"))

                if data.get("runbooks"):
                    with st.expander("Matched runbooks"):
                        st.json(data.get("runbooks"))

                st.caption(f"Provider requested: {data.get('selected_provider', ai_provider)} | Provider used: {data.get('provider_used', 'unknown')}")

                if data.get("llm_error"):
                    st.warning(f"LLM fallback was used: {data.get('llm_error')}")

            except Exception as exc:
                st.error(f"AI analysis failed: {exc}")

            with st.expander("Sample Log Lines"):
                st.code("\n".join(lines[:120]), language="text")

    st.divider()
    render_kafka_helper()



import os
import requests

def _remediation_api(method, path, payload=None):
    token = ""
    base = "http://127.0.0.1:8808"
    try:
        token = st.secrets.get("REMEDIATION_SHARED_TOKEN", "")
        base = st.secrets.get("REMEDIATION_API_URL", "http://127.0.0.1:8808")
    except Exception:
        token = os.getenv("REMEDIATION_SHARED_TOKEN", "")
        base = os.getenv("REMEDIATION_API_URL", "http://127.0.0.1:8808")

    headers = {"X-Remediation-Token": token}
    if payload is None:
        r = requests.request(method, f"{base}{path}", headers=headers, timeout=120)
    else:
        r = requests.request(method, f"{base}{path}", headers=headers, json=payload, timeout=120)
    r.raise_for_status()
    return r.json()

def _render_remediation_agent_ui():
    st.markdown("---")
    st.subheader("Remediation Agent")

    default_service = (
        st.session_state.get("selected_service")
        or st.session_state.get("service_name")
        or "grafana"
    )

    service_name = st.text_input(
        "Service for remediation",
        value=default_service,
        key="remediation_service_name",
    )

    runtime = st.selectbox(
        "Runtime",
        ["systemd", "docker", "docker-compose"],
        key="remediation_runtime",
    )

    issue_type = st.selectbox(
        "Issue type",
        ["unhealthy", "down", "crash_loop", "dependency_timeout"],
        key="remediation_issue_type",
    )

    evidence_text = st.text_area(
        "Evidence",
        value='{"source":"logs_page"}',
        height=120,
        key="remediation_evidence",
    )

    c1, c2, c3 = st.columns(3)

    if c1.button("Create Remediation Incident", key="rem_create_incident", use_container_width=True):
        try:
            import json
            evidence = json.loads(evidence_text) if evidence_text.strip() else {}
            evidence.setdefault("service_name", service_name)
            evidence.setdefault("container_name", service_name)
            evidence.setdefault("compose_service", service_name)

            resp = _remediation_api(
                "POST",
                "/incidents/propose",
                {
                    "service": service_name,
                    "runtime": runtime,
                    "issue_type": issue_type,
                    "node": "local",
                    "evidence": evidence,
                },
            )
            st.session_state["remediation_incident_id"] = resp["incident_id"]
            st.success(f"Incident created: {resp['incident_id']}")
            st.json(resp)
        except Exception as e:
            st.exception(e)

    incident_id = st.session_state.get("remediation_incident_id", "")
    if incident_id:
        st.info(f"Incident ID: {incident_id}")

        if c2.button("Dry Run", key="rem_dry_run", use_container_width=True):
            try:
                resp = _remediation_api(
                    "POST",
                    f"/incidents/{incident_id}/approve",
                    {"approved_by": "admin", "dry_run": True},
                )
                st.session_state["remediation_last_result"] = resp
                st.json(resp)
            except Exception as e:
                st.exception(e)

        if c3.button("Approve and Execute", key="rem_execute", use_container_width=True):
            try:
                resp = _remediation_api(
                    "POST",
                    f"/incidents/{incident_id}/approve",
                    {"approved_by": "admin", "dry_run": False},
                )
                st.session_state["remediation_last_result"] = resp
                st.json(resp)
            except Exception as e:
                st.exception(e)

    if st.session_state.get("remediation_last_result"):
        st.markdown("#### Agent Result")
        st.json(st.session_state["remediation_last_result"])

    with st.expander("Recent Remediation Incidents"):
        try:
            incidents = _remediation_api("GET", "/incidents")
            st.json(incidents)
        except Exception as e:
            st.exception(e)


st.markdown("---")
st.warning("DEBUG: Direct Agent Panel")
try:
    _render_agent_activity_panel(
        selected_service if "selected_service" in locals() else st.session_state.get("selected_service", "grafana"),
        str(locals().get("analysis_result", locals().get("ai_result", "")))
    )
except Exception as e:
    st.exception(e)

