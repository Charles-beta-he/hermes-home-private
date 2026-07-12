# Web4 / Agentic Web research brief

Applicability: use when a user asks about Web 4.0, agentic web, autonomous AI on the web, Semantic Web-to-LLM-agent lineage, or comparisons between Web4-style visions and an Agent OS/control plane such as Hermes.

Anti-conditions: do not treat “Web 4.0” as a finalized W3C standard or as synonymous with blockchain/metaverse. Separate policy/industry narrative from implemented protocols and standards.

## Anchor definition

The most citable current policy definition is the European Commission communication COM(2023)442 final, “An EU initiative on Web 4.0 and virtual worlds: a head start in the next technological transition” (11 July 2023). It frames Web 4.0 as the expected fourth generation of the Web where advanced artificial and ambient intelligence, IoT, trusted blockchain transactions, virtual worlds, and XR integrate digital and real objects/environments so they communicate with each other and blend physical/digital experiences.

Use this as a grounding quote/source before broad synthesis, but label it as a policy definition rather than a universal technical standard.

## Explain the lineage clearly

A concise taxonomy that avoids common confusion:

1. Web 1.0: human-readable documents, hyperlinks, publishing/browsing.
2. Web 2.0: platforms, social/UGC, cloud APIs, network effects, platform-owned identity/data/distribution.
3. Web 3.0 has two meanings that must be disambiguated:
   - W3C/Semantic Web lineage: machine-readable linked data, RDF/OWL/SPARQL, knowledge representation.
   - Crypto/Web3 lineage: decentralized identity/assets/transactions/governance, wallets, smart contracts.
4. Web 4.0 / Agentic Web: user goals are delegated to agents; semantic/capability layers make services machine-operable; identity/authorization/payment/receipts make actions trustworthy; IoT/XR/digital twins connect web agents to physical/spatial environments.

Short synthesis: Web4 = Web3 data/identity/value sovereignty + Semantic Web machine-understandable meaning + LLM/tool-using autonomous agents + IoT/XR/digital-twin physical-world interfaces.

## Autonomous AI core claims

When asked for “自主性 AI” in Web4, organize around these claims:

- Goal-entry replaces page/app-entry: users express outcomes; agents plan and execute across services.
- Machine-operable services replace human-only pages: schemas, tool contracts, service capabilities, constraints, prices, failure modes, and verification become first-class.
- Agents become delegated actors, not just recommenders: they can plan, negotiate, call tools/APIs, request authority, and verify results.
- Identity/authorization/liability become central: who is represented, what scope is allowed, whether spending/signing/sending is authorized, and how action receipts/audits work.
- The web expands into physical/spatial environments: IoT, AR/XR, robots, vehicles, manufacturing, healthcare simulation, and city/industrial digital twins.
- Agent-to-agent protocols become necessary: capability discovery, delegation, negotiation, result proof, dispute handling, and revocation.
- System intelligence matters more than model intelligence alone: model + memory + tools + state + policy + evidence + rollback + governance.

## Core works to cite

Semantic Web / machine-readable web:
- Tim Berners-Lee, James Hendler, Ora Lassila, “The Semantic Web”, Scientific American, 2001.
- W3C Semantic Web Activity and standards: RDF, RDFS, OWL, SPARQL.
- James Hendler’s work connecting agents and the Semantic Web.

Classical agent theory:
- Michael Wooldridge & Nicholas Jennings, “Intelligent Agents: Theory and Practice”, 1995.
- Michael Wooldridge, An Introduction to MultiAgent Systems.
- Stuart Russell & Peter Norvig, Artificial Intelligence: A Modern Approach.
- Yoav Shoham, “Agent-Oriented Programming”, 1993.
- Pattie Maes, “Agents that Reduce Work and Information Overload”, 1994.
- Stan Franklin & Art Graesser, “Is it an Agent, or just a Program?”, 1996.
- Hyacinth Nwana, “Software Agents: An Overview”, 1996.

Identity/value/trust:
- W3C DID Core.
- W3C Verifiable Credentials.
- Satoshi Nakamoto, Bitcoin whitepaper, 2008.
- Vitalik Buterin, Ethereum whitepaper, 2013/2014.
- Christopher Allen, “The Path to Self-Sovereign Identity”, 2016.

LLM/tool-using agents:
- ReAct: Synergizing Reasoning and Acting in Language Models, 2022.
- Toolformer, 2023.
- Generative Agents, 2023.
- Voyager, 2023.
- WebGPT, WebArena, MiniWoB, OSWorld, SWE-bench, GAIA as task/evaluation references.
- Engineering frameworks/protocols: MCP, OpenAPI/tool schemas, LangGraph, AutoGen, CrewAI, Assistants-like runtimes.

## Agent OS comparison checklist

For comparing an Agent OS/control plane to Web4, score gaps along these axes:

1. Semantic/capability graph: Are tools/services/data/objects described in a machine-understandable ontology with constraints and verification?
2. Identity/authority/payment: Are DID/VC/OAuth/wallet/payment/contract scopes native and auditable?
3. Action ledger: Are delegated actions recorded with subject, authority, target, risk, evidence, receipts, and rollback path?
4. Agent-to-agent protocol: Can it discover capabilities, delegate, negotiate, verify, reject, and dispute with external agents?
5. Physical/spatial layer: Does it model devices, sensors, location, XR context, robots, or digital twins as first-class state?
6. Long-running mission runtime: Can it operate goals over days/weeks with budgets, stage gates, evidence, human decisions, and recovery?
7. Economic layer: Does it support bounded purchase, escrow, subscriptions, service markets, and spending authority?
8. UX/governance: Can ordinary users inspect, revoke, and understand permissions, timelines, failures, and receipts?
9. Evaluation harness: Does it measure task success, safety, authority violations, cost, latency, rollback, and evidence completeness?

Useful framing: many current agents are “personal/developer control planes”; Web4 Agent OS requires that control plane plus open semantic services, identity/payment/trust substrate, physical-world interfaces, and interoperable agent protocols.

## Pitfalls

- Do not collapse Web4 into “metaverse”; XR/virtual worlds are one interface layer, while the deeper shift is the agent-operated web.
- Do not collapse Web4 into blockchain; blockchain/DID/VC/payment are trust/value mechanisms, not the full architecture.
- Do not claim Semantic Web failed completely; its standards and ideas reappear in schemas, knowledge graphs, linked data, tool contracts, and agent-readable services.
- Do not claim LLM agents alone solve Web4; without authority, verification, and service contracts, they are brittle automation.
- When comparing Hermes or another Agent OS, distinguish existing local control-plane capabilities from missing open-web substrate capabilities.