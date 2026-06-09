# Parametric CSG Modeling with trimesh + manifold3d

## Environment

- **CSG engine**: `manifold3d` (pip install manifold3d). No blender, no open3d on this machine.
- **trimesh** is installed at system python3 (3.9 site-packages).
- Always use `engine='manifold'` in boolean calls.

## CSG primitives

```python
trimesh.creation.box(extents=(x,y,z))           # rectangular solid
trimesh.creation.cylinder(radius=r, height=h)    # cylinder
trimesh.creation.annulus(r_min, r_max, height)   # ring/tube
```

## Boolean operations

```python
trimesh.boolean.difference([base, cutter], engine='manifold')   # subtract
trimesh.boolean.union([part_a, part_b], engine='manifold')      # add
trimesh.boolean.intersection([a, b], engine='manifold')         # keep overlap
```

## Common pitfalls

- `ImportError: 'blender' is not in PATH` → switch to `engine='manifold'`
- `No module named 'manifold3d'` → `pip3 install manifold3d`
- Non-manifold meshes can cause boolean failures; ensure watertight inputs
- Large face counts slow CSG; use `mesh.simplify_quadric_decimation(target)` for pre-processing
- CSG result may have non-uniform normals; call `mesh.fix_normals()` after boolean ops

## Diagnostic: face-normal angle distribution

For functional parts with ramps/chutes/dispensing channels:

```python
import numpy as np
normals = mesh.face_normals
angles = np.degrees(np.arccos(np.clip(np.abs(normals[:, 2]), 0, 1)))

# Bin analysis:
bins = [
    (0, 10, "flat-horizontal"),
    (10, 25, "slight-slope"),
    (25, 45, "moderate-ramp"),    # good for dispensing
    (45, 70, "steep-ramp"),       # causes jamming
    (70, 90, "vertical/near-vert"),
]
for lo, hi, label in bins:
    mask = np.logical_and(angles >= lo, angles < hi)
    if mask.sum() > 0:
        area = mesh.area_faces[mask].sum()
        print(f"  {label}: {mask.sum()} faces, area={area:.1f}mm2")
```

**Design rule for dispensing ramps**: target 20-30° from horizontal. Angles >45° cause items to jam when the container is full (gravity + friction = stiction on steep surfaces).

## Cigarette box example (manufacturing_cigarette_box.py)

Generates a parametric cigarette box with 3 functional fixes applied to an existing MakerWorld design:

| Fix | Original Problem | Solution |
|-----|-----------------|----------|
| Ramp angle | ~60° steep ramp, cigarettes jam when full | 22° gentle slope to dispensing slot |
| No limiter | Press dispenses multiple cigarettes | 3mm ledge above slot blocks 2nd cigarette |
| Loose lid | Separate cap falls off | Sliding lid with tab-in-groove rail tracks |

```bash
python3 ~/.hermes/scripts/manufacturing_cigarette_box.py \
  --output /path/v2 \
  --ramp-angle 22 \
  --json
```

Output: base STL + sliding lid STL + report JSON. Run through mesh_qa before slicing.

## Parametric model report schema

All parametric generators emit a JSON report with:
```json
{
  "schema": "hermes_parametric_<type>_v<N>",
  "generated_at": "ISO-8601",
  "fixes": { "<fix_id>": { "original_...": ..., "new_...": ..., "effect": "..." } },
  "new_artifacts": { "<part>": { "path": "...", "faces": N, "volume_mm3": N } },
  "print_settings": { ... }
}
```

After generation, always run mesh QA:
```bash
python3 ~/.hermes/scripts/manufacturing_mesh_qa.py analyze \
  --model /path/part.stl \
  --intended-use "用途" \
  --layer-height 0.16 --nozzle-diameter 0.4 --requested-material PLA --json
```
