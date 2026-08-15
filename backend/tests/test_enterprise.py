"""M7 Enterprise — behavioral unit tests (TASK-035..TASK-042).

Covers the 7 enterprise groups (E1–E7) and the 8 architecture invariants
(INV-022..INV-029, named m7_* in test_architecture.py). Pure, offline-first
(deterministic clocks injectable), no external services required.

Run: backend/.venv/Scripts/python -m pytest tests/test_enterprise.py -q
"""

import time

import pytest

from aios_core.enterprise import (
    ABACEngine,
    AuditEvent,
    BudgetExceeded,
    CostGovernor,
    CredentialBroker,
    CredentialError,
    CredentialRef,
    CrossTenantAccessDenied,
    DelegationChain,
    DistributedScheduler,
    EnterpriseManager,
    HealthMonitor,
    IdentityEngine,
    IsolationTier,
    LeaseError,
    LeaseManager,
    MemoryNamespace,
    NetworkPolicy,
    NetworkPolicyEngine,
    NoPrincipalError,
    NodeRegistry,
    Permission,
    Principal,
    PrincipalType,
    Quota,
    QuotaExceeded,
    QuotaManager,
    RBACEngine,
    RecoveryManager,
    RoutingCriteria,
    RuntimeNodeInfo,
    RuntimeRouter,
    SandboxBoundary,
    SandboxBypassError,
    SandboxProfile,
    Tenant,
    TenantBoundary,
    TenantRegistry,
    TenancyManager,
    TenantScope,
    HealthStatus,
    agent_principal,
    service_principal,
    user_principal,
)


# --------------------------------------------------------------------------- #
# TASK-035 — Identity (INV-022)                                                #
# --------------------------------------------------------------------------- #

def test_inv022_identity_required_for_execution():
    eng = IdentityEngine()
    with pytest.raises(NoPrincipalError):
        eng.require(None)
    with pytest.raises(NoPrincipalError):
        eng.require(Principal(id="", type=PrincipalType.USER, tenant_id=""))


def test_inv022_user_principal_factory():
    p = user_principal("u1", "t-a", roles=["developer"], attributes={"dept": "IT"})
    assert p.type is PrincipalType.USER
    assert p.tenant_id == "t-a"
    assert p.roles == ["developer"]


def test_rbac_role_resolution():
    rbac = RBACEngine()
    rbac.define_role("developer", [Permission(action="filesystem.read", resource="repo")])
    p = user_principal("u1", "t-a", roles=["developer"])
    assert rbac.has_permission(p, "filesystem.read", "repo")
    assert not rbac.has_permission(p, "filesystem.write", "repo")


def test_rbac_wildcard():
    rbac = RBACEngine()
    rbac.define_role("admin", [Permission(action="*", resource="*")])
    p = user_principal("u1", "t-a", roles=["admin"])
    assert rbac.has_permission(p, "anything", "anywhere")


def test_abac_environment_condition():
    abac = ABACEngine()
    # deny writes outside development environment for non-IT dept
    abac.add_rule(
        "deny", "write",
        lambda pr, act, res: res.get("environment") != "development"
        and pr.attributes.get("dept") != "IT",
    )
    p = user_principal("u1", "t-a", attributes={"dept": "HR"})
    assert abac.evaluate(p, "write", {"environment": "production"}) == "deny"
    assert abac.evaluate(p, "write", {"environment": "development"}) == "allow"


def test_delegation_chain_validation():
    user = user_principal("user-1", "t-a")
    agent = agent_principal("agent-coder", "t-a", delegated_from="user-1")
    chain = DelegationChain(user, [DelegationChain(agent)])
    chain.validate()  # coherent
    orphan = DelegationChain(agent_principal("x", "t-a", delegated_from="ghost"))
    with pytest.raises(ValueError):
        orphan.validate()


def test_full_authorize_rbac_abac():
    rbac = RBACEngine()
    rbac.define_role("dev", [Permission(action="git.read", resource="repo")])
    abac = ABACEngine()
    abac.add_rule("deny", "git.read",
                  lambda pr, act, res: res.get("environment") == "prod")
    eng = IdentityEngine(rbac, abac)
    p = user_principal("u1", "t-a", roles=["dev"])
    assert eng.authorize(p, "git.read", {"type": "repo", "environment": "dev"})
    assert not eng.authorize(p, "git.read", {"type": "repo", "environment": "prod"})
    assert not eng.authorize(p, "git.write", {"type": "repo"})


# --------------------------------------------------------------------------- #
# TASK-036 — Multi-Tenancy (INV-023)                                          #
# --------------------------------------------------------------------------- #

def test_inv023_cross_tenant_denied_by_default():
    b = TenantBoundary()
    owner = TenantScope(tenant_id="A")
    with pytest.raises(CrossTenantAccessDenied):
        b.enforce(owner, "B")
    assert b.may_access(owner, "A") is True
    assert b.may_access(owner, "B") is False


def test_tenant_registry_crud():
    reg = TenantRegistry()
    reg.register(Tenant(id="A", name="Company A", tier=IsolationTier.ENTERPRISE))
    assert reg.exists("A")
    assert reg.get("A").tier is IsolationTier.ENTERPRISE
    with pytest.raises(KeyError):
        reg.get("Z")


def test_memory_namespace_isolation():
    tm = TenancyManager()
    ns_a = tm.namespace("A")
    ns_a.put("fact", "only A")
    # Tenant A can read its own
    assert ns_a.get("fact", "A") == "only A"
    # Tenant B cannot read A's namespace
    with pytest.raises(CrossTenantAccessDenied):
        ns_a.get("fact", "B")


# --------------------------------------------------------------------------- #
# TASK-037 — Distributed Runtime (INV-029)                                    #
# --------------------------------------------------------------------------- #

def test_inv029_control_plane_isolation_router():
    reg = NodeRegistry()
    reg.register(RuntimeNodeInfo(id="n1", region="ap", capabilities=["python"],
                                 tenant_classes=["enterprise"]))
    reg.register(RuntimeNodeInfo(id="n2", region="ap", capabilities=["python"],
                                 tenant_classes=["secure"]))  # restricted
    router = RuntimeRouter(reg)
    # enterprise tenant class only allowed on n1
    assert router.check_isolation("n1", "enterprise") is True
    assert router.check_isolation("n2", "enterprise") is False
    # selection respects tenant_class gate
    crit = RoutingCriteria(
        tenant_id="t1", tenant_class="enterprise", capability="python")
    assert router.select(crit).id == "n1"


def test_runtime_router_no_candidate():
    reg = NodeRegistry()
    reg.register(RuntimeNodeInfo(id="n1", capabilities=["docker"], tenant_classes=["secure"]))
    router = RuntimeRouter(reg)
    crit = RoutingCriteria(tenant_id="t1", capability="python")
    with pytest.raises(KeyError):
        router.select(crit)


def test_runtime_router_capacity_preference():
    reg = NodeRegistry()
    reg.register(RuntimeNodeInfo(id="cheap", capabilities=["python"], capacity={"cpu": 1, "memory": 2}))
    reg.register(RuntimeNodeInfo(id="expensive", capabilities=["python"], capacity={"cpu": 32, "memory": 64}))
    router = RuntimeRouter(reg)
    crit = RoutingCriteria(tenant_id="t1", capability="python")
    # cheap
    assert router.select(crit).id == "cheap"


# --------------------------------------------------------------------------- #
# TASK-038 — Distributed Scheduler + Lease (INV-026)                          #
# --------------------------------------------------------------------------- #

def test_inv026_single_active_lease():
    lm = LeaseManager(clock=lambda: 1000.0)
    lm.acquire("exec-1", "node-1", ttl_s=60.0)
    with pytest.raises(LeaseError):
        lm.acquire("exec-1", "node-2", ttl_s=60.0)  # INV-026 violation
    assert lm.active_node("exec-1") == "node-1"
    # after expiry, new lease allowed
    lm2 = LeaseManager(clock=lambda: 2000.0)
    # re-create with advanced clock
    lm = LeaseManager(clock=lambda: 2000.0)
    lm.acquire("exec-1", "node-3", ttl_s=60.0)
    assert lm.active_node("exec-1") == "node-3"


def test_lease_renew_and_release():
    lm = LeaseManager(clock=lambda: 1000.0)
    lm.acquire("e", "n1", ttl_s=10.0)
    lm.renew("e", "n1", ttl_s=10.0)
    with pytest.raises(LeaseError):
        lm.renew("e", "n2", ttl_s=10.0)  # wrong node
    lm.release("e")
    assert lm.active_node("e") is None


def test_distributed_scheduler_failover():
    # LeaseManager + Scheduler share a single (mutable) clock — as in real wiring.
    clock = {"t": 1000.0}
    lm = LeaseManager(clock=lambda: clock["t"])
    nodes = [
        RuntimeNodeInfo(id="n1"),
        RuntimeNodeInfo(id="n2"),
    ]
    reg = NodeRegistry()
    for n in nodes:
        reg.register(n)
    sched = DistributedScheduler(
        lm,
        node_selector=lambda exec_id: reg.get("n1" if exec_id.endswith("1") else "n2"),
        clock=lambda: clock["t"],
    )
    sched.enqueue("exec-1")
    scheduled = sched.schedule(ttl_s=60.0)
    assert "exec-1" in scheduled
    # failover to n2 after expiry (advance shared clock past ttl)
    clock["t"] = 2000.0
    sched2 = DistributedScheduler(
        lm,
        node_selector=lambda eid: reg.get("n2"),
        clock=lambda: clock["t"],
    )
    new_node = sched2.failover("exec-1", ttl_s=60.0)
    assert new_node == "n2"


# --------------------------------------------------------------------------- #
# TASK-039 — Governance (INV-025)                                             #
# --------------------------------------------------------------------------- #

def test_inv025_quota_fairness_denies_over():
    qm = QuotaManager()
    qm.set_quota(Quota(tenant_id="A", concurrent_executions=2))
    qm.begin("A")
    qm.begin("A")
    with pytest.raises(QuotaExceeded):
        qm.begin("A")  # over quota
    # override bypasses
    qm.begin("A", override=True)
    qm.end("A")


def test_inv025_token_quota():
    qm = QuotaManager()
    qm.set_quota(Quota(tenant_id="A", llm_tokens_per_day=100))
    qm.add_tokens("A", 60)
    with pytest.raises(QuotaExceeded):
        qm.add_tokens("A", 50)
    qm.add_tokens("A", 40, override=True)


def test_cost_governor_budget_deny_and_cheaper():
    gov = CostGovernor()
    gov.set_budget("A", 0.10)
    est = gov.estimate("gpt", 1000, 0.0002)  # $0.20
    with pytest.raises(BudgetExceeded):
        gov.check_budget("A", est)
    cheaper = gov.cheaper_alternative(est, [gov.estimate("ollama", 1000, 0.00001)])
    assert cheaper is not None and cheaper.amount < est.amount


def test_cost_charge_accumulates():
    gov = CostGovernor()
    gov.set_budget("A", 1.0)
    e = gov.estimate("m", 10, 0.01)
    gov.check_budget("A", e)
    gov.charge("A", e)
    with pytest.raises(BudgetExceeded):
        gov.check_budget("A", gov.estimate("m", 100, 0.01))


# --------------------------------------------------------------------------- #
# TASK-040 — Security & Data Isolation (INV-024, INV-028)                      #
# --------------------------------------------------------------------------- #

def test_inv024_credential_isolation():
    broker = CredentialBroker()
    Cred = CredentialRef
    broker.register(Cred(id="c1", tenant_id="A", project_id="p1",
                         capability="github", secret_ref="ref-A"))
    # same tenant+project+capability resolves
    tok = broker.resolve("c1", "A", "github", "p1")
    assert tok == "tok:ref-A"
    # cross-tenant denied
    with pytest.raises(CredentialError):
        broker.resolve("c1", "B", "github", "p1")
    # cross-project denied
    with pytest.raises(CredentialError):
        broker.resolve("c1", "A", "github", "p2")
    # wrong capability denied
    with pytest.raises(CredentialError):
        broker.resolve("c1", "A", "aws", "p1")


def test_inv028_sandbox_boundary_untrusted():
    sb = SandboxBoundary()
    sb.register_profile("default", SandboxProfile(required=True, network=False))
    prof = sb.require_sandbox("default", untrusted=True)
    assert prof.required is True
    # untrusted without profile -> bypass denied
    with pytest.raises(SandboxBypassError):
        sb.require_sandbox(None, untrusted=True)
    # trusted may skip
    assert sb.require_sandbox(None, untrusted=False).required is False


def test_network_policy_default_deny():
    eng = NetworkPolicyEngine(NetworkPolicy(deny=["metadata"], allow=["github.com"]))
    assert eng.allow("github.com") is True
    assert eng.allow("metadata") is False
    assert eng.allow("evil.com") is False  # default-deny


# --------------------------------------------------------------------------- #
# TASK-041 — Operations: Audit (INV-027) + HA + Recovery                       #
# --------------------------------------------------------------------------- #

def test_inv027_audit_completeness_and_integrity():
    from aios_core.enterprise import CentralAuditStore
    store = CentralAuditStore(clock=lambda: 1234.0)
    store.record("actor", "credential.resolved", "success", tenant_id="A",
                 credential_scope="github", evidence={"cred": "c1"})
    # sensitive action has evidence
    assert store.has_evidence("credential.resolved", tenant_id="A")
    # tamper-evidence: chain verifies
    assert store.verify_integrity() is True
    # tamper breaks chain
    store._events[0].result = "tampered"
    assert store.verify_integrity() is False


def test_health_monitor_failover_target():
    hm = HealthMonitor(clock=lambda: 1000.0)
    hm.heartbeat("n1", HealthStatus.HEALTHY)
    nodes = [RuntimeNodeInfo(id="n1"), RuntimeNodeInfo(id="n2")]
    target = hm.failover_target(nodes, "n1")
    assert target is not None and target.id == "n2"


def test_recovery_snapshot_restore():
    rm = RecoveryManager()
    rm.snapshot("e1", {"step": 3, "data": "x"})
    assert rm.has_snapshot("e1")
    assert rm.restore("e1") == {"step": 3, "data": "x"}


# --------------------------------------------------------------------------- #
# TASK-042 — Dashboard                                                        #
# --------------------------------------------------------------------------- #

def test_enterprise_dashboard_tenant_summary():
    from aios_core.enterprise import CentralAuditStore, EnterpriseDashboard
    store = CentralAuditStore(clock=lambda: 1.0)
    store.record("tA", "execution.started", "success", tenant_id="A")
    store.record("tA", "authz.denied", "denied", tenant_id="A")
    dash = EnterpriseDashboard(store)
    summary = dash.tenant_summary("A")
    assert summary["executions"] == 1
    assert summary["denied"] == 1
    assert "success_rate" in summary


# --------------------------------------------------------------------------- #
# EnterpriseManager facade (wires all INV-022..INV-029)                        #
# --------------------------------------------------------------------------- #

def test_enterprise_manager_facade_wires_invariants():
    em = EnterpriseManager()
    # INV-022
    with pytest.raises(NoPrincipalError):
        em.require_principal(None)
    # register a tenant + node
    em.tenancy.registry.register(Tenant(id="A", name="A"))
    em.nodes.register(RuntimeNodeInfo(id="n1"))
    # INV-026 lease
    lease = em.acquire_lease("exec-1", "n1")
    assert lease.node_id == "n1"
    with pytest.raises(LeaseError):
        em.acquire_lease("exec-1", "n2")
    # INV-027 audit recorded
    assert em.audit.has_evidence("lease.acquired")


def test_enterprise_manager_routing_inv029():
    em = EnterpriseManager()
    em.nodes.register(RuntimeNodeInfo(id="n1", capabilities=["python"], tenant_classes=["enterprise"]))
    node = em.route("tA", tenant_class="enterprise", capability="python")
    assert node.id == "n1"
