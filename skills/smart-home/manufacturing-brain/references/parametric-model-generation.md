# Parametric 3D Model Generation

Extracted from `/Users/charles/.hermes/skills/smart-home/manufacturing-brain/SKILL.md` on 2026-07-01T08:53:45.426287+00:00 to reduce root SKILL.md load while preserving detailed workflow content. The root skill keeps a progressive-loading pointer to this reference.

## Parametric 3D model generation (trimesh + manifold3d)

When modifying an existing functional printed model from user feedback, do not replace it with a simplified parametric substitute unless the user explicitly approves losing the original mechanism. Preserve the original function and part topology first; implement changes as targeted deltas (e.g. shallower blocker/ramp, one-at-a-time limiter, sliding cover) against the original mechanism, and label any simplified redesign as non-equivalent / do-not-print until reviewed.

When no existing .stl model matches the user's request and the geometry is parametrically describable (boxes, ramps, cylinders, CSG combinations), generate the mesh in code using trimesh creation primitives + boolean operations.

**CSG engine**: On this machine, `manifold3d` is the working CSG backend for trimesh. Neither `blender` nor `open3d` are in PATH. Always specify `engine='manifold'` in boolean calls. If manifold3d is missing, install with `pip3 install manifold3d`.

**Pattern**:
```python
import trimesh
outer = trimesh.creation.box(extents=(w, d, h))
inner = trimesh.creation.box(extents=(w-2*wall, d-wall, h-wall))
shell = trimesh.boolean.difference([outer, inner], engine='manifold')
feature = trimesh.creation.cylinder(radius=r, height=h)
result = trimesh.boolean.union([shell, feature], engine='manifold')
result.export('/path/output.stl')
```

**Diagnostic: face-normal angle distribution** — for functional parts with ramps/chutes/slopes, analyze face angles to verify dispensing geometry:
```python
normals = mesh.face_normals
angles = np.degrees(np.arccos(np.clip(np.abs(normals[:, 2]), 0, 1)))
# bins: flat(0-10), slight(10-25), moderate(25-45), steep(45-70), vertical(70-90)
```

Existing parametric generators:
- `manufacturing_calibration_cube.py` — 12mm calibration cube
- `manufacturing_lamp_base.py` — ribbed lamp base (v1/v2/v3)
- `manufacturing_lamp_shade.py` — diffuser shade (v1/v2/v3)
- `manufacturing_cigarette_box.py` — cigarette box with reduced-ramp, limiter, sliding lid
- `manufacturing_popup_cigarette_box_v4.py` — surgical popup cigarette-box repair after physical QA: support-light internal guide ribs, mated sliding-cover receiver grooves, and regular/slim limiter test inserts

Cigarette-box physical QA lessons:
- Do not solve anti-jam by adding a broad shallow internal ramp/liner if it creates dense internal supports or slow-cooling spaghetti; prefer small wall-connected chamfered guide ribs and verify `components == 1`.
- Sliding-cover fixes must modify both sides of the assembly: cover rails/stops plus matching receiver grooves/lead-in on the mating upper/body part. A rail-only cover is not a complete assembly design.
- Do not assume a universal cigarette diameter. Regular/thick and slim cigarettes need either a chosen throat variant or swappable/test limiter inserts; one fixed single-cigarette limiter cannot be optimal for both.
- Before full print, inspect slicer support preview layer-by-layer; avoid dense normal support inside the cigarette channel and curved/visible faces. Use tree/manual supports and support blockers unless a real floating island is proven.
