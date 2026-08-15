 # AIOS Python SDK

Public, offline-testable developer API for AIOS. The SDK exposes stable component contracts and a transport-injected `Client`; runtime policy, credentials, sandboxing, and side effects remain enforced by AIOS.

```python
from aios import Agent, AgentRequest, AgentResponse, Client

class ReviewAgent(Agent):
	id = "code-reviewer"

	def handle(self, request: AgentRequest) -> AgentResponse:
		return AgentResponse(f"Review: {request.input}")
```

Install locally with `pip install -e sdk/python`. The package has no backend dependency and can be tested with a small mock implementing `Transport`.
# AIOS SDK — Python

> **Trạng thái: chưa code (stub)** — sẽ được xây dựng trong M1/M2 theo plan.

SDK Python để viết Agent, Tool, Capability, Skill, Prompt, Workflow cho AIOS:
decorators (`@aios.tool`, `@aios.agent`, `@aios.workflow`) + base classes, dùng chung contract
schemas sinh từ `backend/contracts/`.

## Roadmap

- [ ] Contract schemas (generate từ backend) — M1
- [ ] `@aios.tool` / `@aios.agent` / `@aios.workflow` decorators — M2
- [ ] Skill pack manifest helpers — M2

Xem chi tiết: [`docs/PLAN.md`](../docs/PLAN.md)
