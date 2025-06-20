"""Agent performance metrics definition"""

from prometheus_client import Counter, Histogram, Gauge

# Task processing metrics
TASK_PROCESSING_TIME = Histogram(
    "agent_task_processing_seconds",
    "Time spent processing tasks",
    ["agent_name", "task_type"],
    buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0, 60.0]
)

TASK_COUNTER = Counter(
    "agent_tasks_total",
    "Total number of tasks processed",
    ["agent_name", "task_type", "status"]
)

# Memory usage metrics
MEMORY_USAGE = Gauge(
    "agent_memory_usage_bytes",
    "Memory usage in bytes",
    ["agent_name"]
)

SHARED_MEMORY_SIZE = Gauge(
    "agent_shared_memory_size",
    "Number of entries in shared memory",
    ["agent_name"]
)

# LLM call metrics
LLM_CALLS = Counter(
    "agent_llm_calls_total",
    "Total number of LLM API calls",
    ["agent_name", "model", "status"]
)

LLM_TOKENS = Counter(
    "agent_llm_tokens_total",
    "Total number of tokens used",
    ["agent_name", "model", "token_type"]  # token_type: prompt/completion
)

LLM_LATENCY = Histogram(
    "agent_llm_latency_seconds",
    "LLM API call latency",
    ["agent_name", "model"],
    buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0]
)

# Agent status metrics
AGENT_STATUS = Gauge(
    "agent_status",
    "Current agent status",
    ["agent_name", "status"]  # status: running/idle/error
)

AGENT_ERRORS = Counter(
    "agent_errors_total",
    "Total number of agent errors",
    ["agent_name", "error_type"]
)

# Performance metrics
TASK_SUCCESS_RATE = Gauge(
    "agent_task_success_rate",
    "Task success rate",
    ["agent_name"]
)

RESPONSE_QUALITY = Gauge(
    "agent_response_quality",
    "Response quality score",
    ["agent_name", "metric_type"]  # metric_type: accuracy/relevance/completeness
)

# Resource usage metrics
CPU_USAGE = Gauge(
    "agent_cpu_usage_percent",
    "CPU usage percentage",
    ["agent_name"]
)

DISK_IO = Counter(
    "agent_disk_io_bytes_total",
    "Total disk I/O in bytes",
    ["agent_name", "operation"]  # operation: read/write
)

# Context metrics
CONTEXT_SIZE = Gauge(
    "agent_context_size_bytes",
    "Context size in bytes",
    ["agent_name", "context_type"]  # context_type: agent/global
)

CONTEXT_UPDATES = Counter(
    "agent_context_updates_total",
    "Total number of context updates",
    ["agent_name", "context_type", "operation"]  # operation: get/set/update
)