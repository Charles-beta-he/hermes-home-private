# Mobile Projection Bootstrap Readiness

## Scope / Applicability / Anti-conditions

Scope: PWA/RN/mobile companion apps that consume server/Gateway-generated `ContextCard` / `EvidenceSpan` projections and expose enterprise readiness or beta gates.

Applicability: use when a mobile app has multiple entry surfaces (PWA, React Native shell, WebView, desktop/web-ui operator console), needs offline/local answers, or shows readiness based on Gateway sync state.

Anti-conditions:
- Do not use this for purely visual navigation entry cards with no sync/readiness behavior.
- Do not treat this pattern as authorization to write canonical facts from mobile.
- Do not mark enterprise/production readiness from demo fixtures, `sampleData`, static UI copy, or a reachable Gateway with zero projection data.
- Keep project-specific paths, ports, profile names, and release IDs in the project profile/ledger, not in this reference.

## Core Rule

Mobile companion readiness must be derived from the real projection lifecycle, not from UI wiring alone:

```text
Gateway / server authority
→ bootstrap / device status / sync policy
→ changes / projection objects
→ local projection store
→ local retrieval / answer / handoff
→ readiness gate readback
```

`bootstrap` tells the client whether it is allowed/current enough to sync; `changes` supplies the evidence projection. A client that can reach `bootstrap` but receives no cards/spans is connected, but it is not evidence-ready.

## Recommended Contract

Expose a tiny shared projection-bootstrap helper per runtime, or a shared package if both PWA and RN can consume it.

Minimum result shape:

```ts
type ProjectionSyncState = 'idle' | 'synced' | 'empty' | 'wipe_required' | 'offline' | 'error';

interface MobileProjection {
  cards: ContextCard[];
  spans: EvidenceSpan[];
}

interface ProjectionBootstrapResult {
  state: ProjectionSyncState;
  latestRevision: number;
  syncedAt: string;
  projection: MobileProjection;
  message: string;
}
```

Enterprise readiness mapping:

```text
Gateway reachable + cards/spans > 0  -> contextProjection: verified
Gateway reachable + cards/spans = 0  -> contextProjection: planned/empty, not verified
Gateway unreachable                  -> contextProjection: planned/offline, not verified
Encrypted local store verified       -> localEncryptedPersistence: verified
Device install not actually proven   -> rnDeviceInstall: human_gate/planned
Rollback proof missing               -> releaseRollback: planned
Local artifact + readback + rollback steps -> releaseRollback: verified (local proof only; not deploy/publish)
```

After applying changes, report device sync health separately from facts:

```ts
interface DeviceStatePayload {
  appliedRevision: number;
  localDbVersion?: number;
  storageUsage?: number;
}
```

`deviceState` writeback may upload sync metadata only (`appliedRevision`, DB/schema version, storage usage, status). It must not upload local `ContextCard` / `EvidenceSpan` bodies or turn mobile into a canonical fact writer.

## Implementation Sequence

1. Write RED tests before implementation:
   - client calls `/sync/bootstrap` before `/sync/changes`;
   - cards/spans from changes become explicit local projection;
   - no projection data keeps `contextProjection` non-verified;
   - local projection metadata is persisted as local state, not canonical fact state;
   - demo/sample fixtures never satisfy production readiness.
2. Implement the bootstrap helper:
   - normalize base URL;
   - send device ID headers;
   - parse `requiredClientAction` / revoked device into `wipe_required`;
   - fetch changes only after bootstrap succeeds;
   - convert only known projection change types (`context_card`, `evidence_span`).
3. Connect PWA:
   - replace direct `changes(0)` calls with bootstrap + changes;
   - update readiness UI from returned readiness, not static defaults;
   - seed demo data only under explicit demo/dev opt-in.
4. Connect RN:
   - store projection plus sync metadata in the local thread/envelope;
   - make local assistant turns use `thread.projection` by default;
   - surface sync state/counts on a diagnostics/details surface;
   - do not put projection branching in every screen.
5. Add device-state writeback:
   - after applying a projection, POST applied revision and local storage/schema metadata;
   - keep writeback best-effort if the projection itself succeeded;
   - never include local fact bodies or sample fixtures in device-state payloads.
6. Add local rollback proof before promotion claims:
   - verify built artifacts exist and are hashable;
   - record readback evidence and at least three rollback steps;
   - mark as local rollback proof only unless a real deployment/publish channel was actually exercised.
7. Verify:
   - focused tests for bootstrap helper, device-state writeback, rollback manifest, and RN projection helper;
   - full workspace tests/build;
   - native lint/Jest;
   - live local Gateway smoke: device pairing/register, bootstrap readback, changes readback, deviceState writeback.

## Pitfalls

1. **Static readiness trap**: rendering an entry/readiness panel and setting `contextProjection=verified` without live projection data creates a false enterprise gate.
2. **Changes-before-bootstrap trap**: directly calling changes can skip device status, wipe/reauth signals, sync policy, and latest revision metadata.
3. **Gateway-reachable equals evidence-ready trap**: a healthy Gateway with zero projection objects still cannot answer evidence-bound questions.
4. **Fixture promotion trap**: sample cards/spans are useful for tests/demo mode but must never satisfy production projection readiness.
5. **Mobile second-source trap**: synced projection is a local read-only cache. Mobile may draft/handoff, but canonical facts/memory/tasks remain server/agent authority.
6. **Thread overwrite trap in RN**: when merging projection metadata into a conversation/thread state, preserve existing messages, history, queued handoffs, artifacts, and retry metadata.
7. **Device-state as fact-upload trap**: `deviceState`/heartbeat endpoints are for applied revision, schema/storage health, and required client action. If they include local evidence/fact bodies, the mobile client has become an unauthorized writer.
8. **Rollback proof as release trap**: a local rollback manifest proves artifacts/readbacks/steps are present; it is not a deploy, publish, App Store/TestFlight rollout, or native binary rollback unless those channels were actually exercised and read back.

## Verification Checklist

- [ ] Bootstrap runs before changes.
- [ ] Device status and required client action are interpreted.
- [ ] Context readiness is verified only when projection objects exist.
- [ ] Empty/unreachable Gateway is represented as empty/offline/planned, not production-ready.
- [ ] RN/PWA local answer paths read explicit projection and do not import sample fixtures implicitly.
- [ ] Full tests/build plus native lint/Jest pass after wiring.
- [ ] A live Gateway smoke proves pair/register + bootstrap + changes + deviceState readback when claiming sync integration.
- [ ] Device-state writeback contains sync-health metadata only, not local fact/evidence bodies.
- [ ] Rollback proof distinguishes local artifact/readback/steps from real deployment/publish/native-binary rollback.
