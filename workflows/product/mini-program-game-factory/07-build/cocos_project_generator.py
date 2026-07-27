#!/usr/bin/env python3
"""Generate and verify a deterministic Cocos Creator 3.8 project candidate."""

from __future__ import annotations

import argparse
import base64
import hashlib
import json
import os
import shutil
import tempfile
import uuid
from pathlib import Path
from typing import Any, Mapping

CREATOR_VERSION = "3.8.0"
SERIALIZATION_SOURCE = {
    "repository": "https://github.com/cocos/cocos-example-projects",
    "commit": "5acd26218d3915169679a288ebf65b9ca1f96027",
    "project": "physics-3d",
    "creator_version": "3.8.0",
}
RUNTIME_SOURCES = (
    "content-pack.ts",
    "gameplay-kernel.ts",
    "platform-port.ts",
    "local-platform-stub.ts",
)


class ProjectGenerationError(ValueError):
    pass


def _canonical(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()


def _digest(value: Any) -> str:
    return hashlib.sha256(_canonical(value)).hexdigest()


def _file_digest(path: Path) -> str:
    hasher = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(65536), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n")


def compress_uuid(value: str) -> str:
    """Cocos UUID compression used by serialized custom component __type__."""
    compact = value.replace("-", "")
    if len(compact) != 32 or any(char not in "0123456789abcdefABCDEF" for char in compact):
        raise ProjectGenerationError("uuid must contain exactly 32 hexadecimal digits")
    alphabet = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/"
    output = compact[:5]
    for index in range(5, 32, 3):
        triplet = int(compact[index : index + 3], 16)
        output += alphabet[triplet >> 6] + alphabet[triplet & 0x3F]
    return output


def _verify_candidate(candidate_root: Path) -> Mapping[str, Any]:
    manifest_path = candidate_root / "candidate-manifest.json"
    if not manifest_path.is_file():
        raise ProjectGenerationError("candidate manifest is missing")
    manifest = json.loads(manifest_path.read_text())
    payload = dict(manifest)
    claimed = payload.pop("manifest_digest", None)
    if not claimed or _digest(payload) != claimed:
        raise ProjectGenerationError("candidate manifest digest mismatch")
    if manifest.get("closure_state") != "cocos_candidate_materialized" or not manifest.get("candidate_only"):
        raise ProjectGenerationError("candidate manifest has invalid closure state")
    if any(manifest.get("authority", {}).values()):
        raise ProjectGenerationError("candidate manifest opens forbidden authority")
    for relative, expected in manifest.get("files", {}).items():
        path = candidate_root / relative
        if not path.is_file() or _file_digest(path) != expected.get("sha256") or path.stat().st_size != expected.get("bytes"):
            raise ProjectGenerationError(f"candidate manifest file mismatch: {relative}")
    return manifest


def _script_meta(script_uuid: str) -> Mapping[str, Any]:
    return {
        "ver": "4.0.23",
        "importer": "typescript",
        "imported": True,
        "uuid": script_uuid,
        "files": [],
        "subMetas": {},
        "userData": {
            "moduleId": "project:///assets/game-factory/GameBootstrap.js",
            "simulateGlobals": [],
        },
    }


def _scene(scene_uuid: str, script_uuid: str, seed: int) -> list[Mapping[str, Any]]:
    return [
        {
            "__type__": "cc.SceneAsset",
            "_name": "main",
            "_objFlags": 0,
            "_native": "",
            "scene": {"__id__": 1},
            "asyncLoadAssets": False,
        },
        {
            "__type__": "cc.Scene",
            "_name": "main",
            "_objFlags": 0,
            "_parent": None,
            "_children": [{"__id__": 2}],
            "_active": True,
            "_components": [],
            "_prefab": None,
            "autoReleaseAssets": False,
            "_globals": {"__id__": 4},
            "_id": scene_uuid,
        },
        {
            "__type__": "cc.Node",
            "_name": "GameBootstrap",
            "_objFlags": 0,
            "_parent": {"__id__": 1},
            "_children": [],
            "_active": True,
            "_components": [{"__id__": 3}],
            "_prefab": None,
            "_lpos": {"__type__": "cc.Vec3", "x": 0, "y": 0, "z": 0},
            "_lrot": {"__type__": "cc.Quat", "x": 0, "y": 0, "z": 0, "w": 1},
            "_lscale": {"__type__": "cc.Vec3", "x": 1, "y": 1, "z": 1},
            "_layer": 33554432,
            "_euler": {"__type__": "cc.Vec3", "x": 0, "y": 0, "z": 0},
            "_id": "GFBootstrapNode000000000",
        },
        {
            "__type__": compress_uuid(script_uuid),
            "_name": "",
            "_objFlags": 0,
            "node": {"__id__": 2},
            "_enabled": True,
            "__prefab": None,
            "seed": seed,
            "_id": "GFBootstrapComponent00000",
        },
        {
            "__type__": "cc.SceneGlobals",
            "ambient": {"__id__": 5},
            "_skybox": {"__id__": 6},
            "shadows": {"__id__": 7},
        },
        {
            "__type__": "cc.AmbientInfo",
            "_skyColor": {"__type__": "cc.Vec4", "x": 0.2, "y": 0.5, "z": 0.8, "w": 0.52},
            "_skyIllum": 20000,
            "_groundAlbedo": {"__type__": "cc.Vec4", "x": 0.2, "y": 0.2, "z": 0.2, "w": 1},
        },
        {
            "__type__": "cc.SkyboxInfo",
            "_envmap": None,
            "_enabled": False,
            "_useHDR": True,
            "_envmapLDR": None,
            "_envmapHDR": None,
            "_diffuseMapLDR": None,
            "_diffuseMapHDR": None,
            "_envLightingType": 0,
        },
        {
            "__type__": "cc.ShadowsInfo",
            "_enabled": False,
            "_normal": {"__type__": "cc.Vec3", "x": 0, "y": 1, "z": 0},
            "_distance": 0,
            "_shadowColor": {"__type__": "cc.Color", "r": 0, "g": 0, "b": 0, "a": 76},
        },
    ]


def _bootstrap_source(content: Mapping[str, Any]) -> str:
    serialized = json.dumps(content, ensure_ascii=False, sort_keys=True, indent=2)
    return f'''import {{ _decorator, Component }} from 'cc';
import {{ normalizeContentPack }} from './core/content-pack.js';
import {{ applyAction, createGame, GameState, scoreState }} from './core/gameplay-kernel.js';

const {{ ccclass, property }} = _decorator;
const CONTENT_PACK = {serialized} as const;

@ccclass('GameBootstrap')
export class GameBootstrap extends Component {{
  @property
  public seed = 20260727;

  private state: GameState | null = null;

  public onLoad(): void {{
    this.state = createGame(normalizeContentPack(CONTENT_PACK), this.seed);
    this.node.emit('game-state-changed', this.snapshot());
  }}

  public rotateNode(index: number): void {{
    this.update({{ type: 'rotate_node', index }});
  }}

  public swapAdjacent(first: number, second: number): void {{
    this.update({{ type: 'swap_adjacent', first, second }});
  }}

  public requestHint(): void {{
    this.update({{ type: 'request_hint' }});
  }}

  public snapshot(): Readonly<GameState> {{
    if (!this.state) throw new Error('GameBootstrap has not loaded');
    return this.state;
  }}

  public score(): number {{
    return this.state ? scoreState(this.state) : 0;
  }}

  private update(action: Parameters<typeof applyAction>[1]): void {{
    if (!this.state) throw new Error('GameBootstrap has not loaded');
    this.state = applyAction(this.state, action);
    this.node.emit('game-state-changed', this.snapshot());
  }}
}}
'''


def _build_intent(platform: str, task_name: str) -> Mapping[str, Any]:
    return {
        "schema_version": 1,
        "platform": platform,
        "creator_task_name": task_name,
        "appid": None,
        "closure_state": "appid_required",
        "executable": False,
        "authority": {"may_build": False, "may_invoke_devtools": False, "may_publish": False},
    }


def _collect_files(root: Path) -> list[Mapping[str, Any]]:
    files = []
    for path in sorted(item for item in root.rglob("*") if item.is_file() and item.name != "project-manifest.json"):
        relative = path.relative_to(root).as_posix()
        files.append({"path": relative, "bytes": path.stat().st_size, "sha256": _file_digest(path)})
    return files


def generate_cocos_project(candidate_root: Path, runtime_core: Path, output_root: Path) -> Mapping[str, Any]:
    candidate_root = Path(candidate_root)
    runtime_core = Path(runtime_core)
    output_root = Path(output_root)
    if output_root.exists() or output_root.is_symlink():
        raise ProjectGenerationError("output root already exists")
    if not runtime_core.is_dir():
        raise ProjectGenerationError("runtime core is missing")
    candidate = _verify_candidate(candidate_root)
    content = json.loads((candidate_root / "generated" / "content-pack.json").read_text())
    source_compile_digest = candidate["source_compile_digest"]
    namespace = uuid.UUID("f7a469c3-37cf-4ec3-a21a-3ae0653a1e6a")
    project_uuid = str(uuid.uuid5(namespace, source_compile_digest + ":project"))
    scene_uuid = str(uuid.uuid5(namespace, source_compile_digest + ":scene"))
    script_uuid = str(uuid.uuid5(namespace, source_compile_digest + ":bootstrap"))
    output_root.parent.mkdir(parents=True, exist_ok=True)
    staging = Path(tempfile.mkdtemp(prefix=f".{output_root.name}.", dir=output_root.parent))
    try:
        _write_json(staging / "package.json", {
            "name": "hermes-circuit-untangle",
            "type": "2d",
            "uuid": project_uuid,
            "creator": {"version": CREATOR_VERSION},
            "version": "0.1.0",
        })
        _write_json(staging / "tsconfig.json", {
            "compilerOptions": {
                "target": "ES2017",
                "lib": ["ES2017", "DOM"],
                "module": "ES2020",
                "moduleResolution": "node",
                "strict": True,
                "noEmit": True,
                "experimentalDecorators": True,
                "skipLibCheck": True,
                "baseUrl": ".",
                "paths": {"cc": ["typecheck/cc.d.ts"]},
            },
            "include": ["assets/**/*.ts", "typecheck/**/*.d.ts"],
        })
        typecheck_dir = staging / "typecheck"
        typecheck_dir.mkdir(parents=True)
        (typecheck_dir / "cc.d.ts").write_text("""declare module 'cc' {
  export interface CocosDecoratorApi {
    ccclass(name: string): ClassDecorator;
    property(target: object, propertyKey: string | symbol): void;
  }
  export const _decorator: CocosDecoratorApi;
  export class Node {
    emit(event: string, ...args: unknown[]): void;
  }
  export class Component {
    readonly node: Node;
  }
}
""")
        (typecheck_dir / "README.md").write_text(
            "This declaration is only a local TypeScript boundary shim. "
            "Passing it is not evidence of Cocos Creator API, import, preview, or build success.\n"
        )
        (staging / ".gitignore").write_text("library/\nlocal/\ntemp/\nbuild/\n")
        core_target = staging / "assets" / "game-factory" / "core"
        core_target.mkdir(parents=True)
        for name in RUNTIME_SOURCES:
            source = runtime_core / "src" / name
            if not source.is_file():
                raise ProjectGenerationError(f"runtime source is missing: {name}")
            shutil.copyfile(source, core_target / name)
        bootstrap = staging / "assets" / "game-factory" / "GameBootstrap.ts"
        bootstrap.parent.mkdir(parents=True, exist_ok=True)
        bootstrap.write_text(_bootstrap_source(content))
        _write_json(Path(str(bootstrap) + ".meta"), _script_meta(script_uuid))
        scene = staging / "assets" / "scenes" / "main.scene"
        _write_json(scene, _scene(scene_uuid, script_uuid, 20260727))
        _write_json(Path(str(scene) + ".meta"), {
            "ver": "1.1.39", "importer": "scene", "imported": True, "uuid": scene_uuid,
            "files": [".json"], "subMetas": {}, "userData": {},
        })
        _write_json(staging / "build-intents" / "wechatgame.json", _build_intent("wechat", "wechatgame"))
        _write_json(staging / "build-intents" / "bytedance-mini-game.json", _build_intent("douyin", "bytedance-mini-game"))
        _write_json(staging / "source" / "content-pack.json", content)
        _write_json(staging / "source" / "gameplay-kernel.json", json.loads((candidate_root / "generated" / "gameplay-kernel.json").read_text()))
        readme = """# Hermes Cocos Creator 3.8 candidate\n\nGenerated deterministically from a verified WorkPackage candidate.\n\n- `assets/scenes/main.scene` attaches `GameBootstrap`.\n- `assets/game-factory/core/` is the Node-tested pure TypeScript kernel.\n- Build intents are non-executable until a real AppID and human authority are supplied.\n- `creator_import_pending` is not evidence that Creator imported, previewed, or built this project.\n"""
        (staging / "README.md").write_text(readme)
        payload = {
            "schema_version": 1,
            "closure_state": "creator_import_pending",
            "creator_version": CREATOR_VERSION,
            "source_candidate_manifest_digest": candidate["manifest_digest"],
            "source_compile_digest": source_compile_digest,
            "serialization_source": SERIALIZATION_SOURCE,
            "project_uuid": project_uuid,
            "scene_uuid": scene_uuid,
            "script_uuid": script_uuid,
            "script_type": compress_uuid(script_uuid),
            "platform_targets": {"wechat": "wechatgame", "douyin": "bytedance-mini-game"},
            "authority": {
                "creator_runtime_verified": False,
                "may_build_platform": False,
                "may_invoke_devtools": False,
                "may_publish": False,
            },
            "files": _collect_files(staging),
        }
        manifest = {**payload, "project_digest": _digest(payload)}
        _write_json(staging / "project-manifest.json", manifest)
        os.rename(staging, output_root)
        return manifest
    except Exception:
        shutil.rmtree(staging, ignore_errors=True)
        raise


def verify_generated_project(root: Path) -> Mapping[str, Any]:
    root = Path(root)
    manifest_path = root / "project-manifest.json"
    if not manifest_path.is_file():
        raise ProjectGenerationError("project manifest is missing")
    manifest = json.loads(manifest_path.read_text())
    payload = dict(manifest)
    claimed = payload.pop("project_digest", None)
    if not claimed or _digest(payload) != claimed:
        raise ProjectGenerationError("project manifest digest mismatch")
    if manifest.get("closure_state") != "creator_import_pending" or any(manifest.get("authority", {}).values()):
        raise ProjectGenerationError("project manifest opens forbidden authority")
    expected_paths = set()
    for entry in manifest.get("files", []):
        relative = entry.get("path", "")
        if not relative or relative.startswith("/") or ".." in Path(relative).parts:
            raise ProjectGenerationError("project manifest contains an unsafe path")
        expected_paths.add(relative)
        path = root / relative
        if path.is_symlink() or not path.is_file() or path.stat().st_size != entry.get("bytes") or _file_digest(path) != entry.get("sha256"):
            raise ProjectGenerationError(f"generated file digest mismatch: {relative}")
    actual_paths = {path.relative_to(root).as_posix() for path in root.rglob("*") if path.is_file() and path.name != "project-manifest.json"}
    if actual_paths != expected_paths:
        raise ProjectGenerationError("generated project file set mismatch")
    scene = json.loads((root / "assets" / "scenes" / "main.scene").read_text())
    if manifest.get("script_type") not in {item.get("__type__") for item in scene if isinstance(item, dict)}:
        raise ProjectGenerationError("scene does not attach the declared bootstrap script")
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--candidate", type=Path)
    parser.add_argument("--runtime-core", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--verify", type=Path)
    args = parser.parse_args()
    if args.verify:
        result = verify_generated_project(args.verify)
    else:
        missing = [name for name in ("candidate", "runtime_core", "output") if getattr(args, name) is None]
        if missing:
            parser.error("generation requires --candidate, --runtime-core and --output")
        result = generate_cocos_project(args.candidate, args.runtime_core, args.output)
    print(json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
