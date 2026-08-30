#!/usr/bin/env python3
"""Render carrot + Pip props from game 3D assets (USDA / voxel mesh)."""

from __future__ import annotations

import subprocess
import textwrap
from pathlib import Path

from PIL import Image, ImageOps

ROOT = Path(__file__).resolve().parents[1]
GAME_ASSETS = ROOT.parent / "harvestloop" / "harvestloop" / "Assets3D"
ASSETS = ROOT / "public" / "assets"
CACHE = ROOT / ".render-cache"

CARROT_USDA = GAME_ASSETS / "Carrot_Ripe.usda"

# Pip palette — mirrors VoxelEntityFactory.Candy (sRGB, used as USD linear tints).
PIP_PALETTE = [
    (0.97, 0.97, 0.95),  # white
    (0.97, 0.68, 0.78),  # pink inner ear
    (0.13, 0.20, 0.35),  # navy eyes
    (0.95, 0.55, 0.60),  # rose nose
    (0.15, 0.65, 0.60),  # scarf
    (0.99, 0.94, 0.86),  # cream belly / tail
]

FACES = (
    ((0, 1, 0), ((0, 1, 0), (0, 1, 1), (1, 1, 1), (1, 1, 0))),
    ((0, -1, 0), ((0, 0, 0), (1, 0, 0), (1, 0, 1), (0, 0, 1))),
    ((1, 0, 0), ((1, 0, 0), (1, 1, 0), (1, 1, 1), (1, 0, 1))),
    ((-1, 0, 0), ((0, 0, 0), (0, 0, 1), (0, 1, 1), (0, 1, 0))),
    ((0, 0, 1), ((0, 0, 1), (1, 0, 1), (1, 1, 1), (0, 1, 1))),
    ((0, 0, -1), ((0, 0, 0), (0, 1, 0), (1, 1, 0), (1, 0, 0))),
)


def _box(xs: range, ys: range, zs: range, color: int) -> list[tuple[int, int, int, int]]:
    return [(x, y, z, color) for x in xs for y in ys for z in zs]


def pip_voxels() -> list[tuple[int, int, int, int]]:
    """Voxel layout copied from VoxelEntityFactory.makePip()."""
    white, pink, navy, rose, scarf, cream = 0, 1, 2, 3, 4, 5
    voxels: list[tuple[int, int, int, int]] = []

    voxels += _box(range(2, 8), range(0, 5), range(3, 7), white)
    voxels += _box(range(2, 8), range(5, 6), range(3, 7), scarf)
    voxels += [(6, 4, 2, scarf), (6, 3, 2, scarf)]
    voxels += _box(range(1, 9), range(6, 13), range(2, 8), white)
    voxels += _box(range(2, 4), range(13, 19), range(4, 6), white)
    voxels += _box(range(6, 8), range(13, 19), range(4, 6), white)
    for y in range(14, 18):
        voxels.append((3, y, 3, pink))
        voxels.append((6, y, 3, pink))

    solid = {(x, y, z) for x, y, z, _ in voxels}

    def drop(predicate) -> None:
        nonlocal voxels
        voxels = [v for v in voxels if not predicate(v)]

    drop(lambda v: v[2] == 2 and v[0] in (3, 6) and v[1] == 10)
    voxels += [(3, 10, 2, navy), (6, 10, 2, navy)]
    drop(lambda v: v[2] == 2 and v[0] == 4 and v[1] == 9)
    drop(lambda v: v[2] == 2 and v[0] == 5 and v[1] == 9)
    voxels += [(4, 9, 2, rose), (5, 9, 2, rose)]
    drop(lambda v: v[2] == 2 and v[0] in (2, 7) and v[1] == 8)
    voxels += [(2, 8, 2, pink), (7, 8, 2, pink)]
    drop(lambda v: v[2] == 3 and 3 <= v[0] <= 6 and 1 <= v[1] <= 3)
    voxels += _box(range(3, 7), range(1, 4), range(3, 4), cream)
    voxels += [(2, 0, 2, white), (3, 0, 2, white), (6, 0, 2, white), (7, 0, 2, white)]
    voxels += _box(range(4, 6), range(2, 4), range(7, 8), cream)

    # Rebuild solid after edits.
    _ = solid  # noqa: F841 — kept for parity with Swift source.
    return voxels


def _mesh_for_color(
    voxels: list[tuple[int, int, int, int]],
    solid: set[tuple[int, int, int]],
    color_idx: int,
    size: float,
    origin: tuple[float, float, float],
) -> tuple[list[tuple[float, float, float]], list[tuple[float, float, float]], list[int]]:
    positions: list[tuple[float, float, float]] = []
    normals: list[tuple[float, float, float]] = []
    indices: list[int] = []

    for x, y, z, color in voxels:
        if color != color_idx:
            continue
        for normal, corners in FACES:
            neighbor = (x + normal[0], y + normal[1], z + normal[2])
            if neighbor in solid:
                continue
            start = len(positions)
            for cx, cy, cz in corners:
                positions.append(
                    (
                        (x + cx) * size + origin[0],
                        (y + cy) * size + origin[1],
                        (z + cz) * size + origin[2],
                    )
                )
                normals.append(normal)
            indices.extend([start, start + 1, start + 2, start, start + 2, start + 3])

    return positions, normals, indices


def _fmt_points(points: list[tuple[float, float, float]]) -> str:
    return ", ".join(f"({p[0]:g}, {p[1]:g}, {p[2]:g})" for p in points)


def _fmt_normals(normals: list[tuple[float, float, float]]) -> str:
    return ", ".join(f"({n[0]:g}, {n[1]:g}, {n[2]:g})" for n in normals)


def write_pip_usda(path: Path) -> None:
    voxels = pip_voxels()
    solid = {(x, y, z) for x, y, z, _ in voxels}
    unit = 0.062
    origin = (-5 * unit, 0.06, -5 * unit)

    meshes: list[str] = []
    materials: list[str] = []
    for idx, color in enumerate(PIP_PALETTE):
        positions, normals, indices = _mesh_for_color(voxels, solid, idx, unit, origin)
        if not positions:
            continue
        tri_count = len(indices) // 3
        face_counts = [3] * tri_count
        mats = textwrap.dedent(
            f"""
            def Material "Mat{idx}"
            {{
                token outputs:surface.connect = </Root/Materials/Mat{idx}/Shader.outputs:surface>
                def Shader "Shader"
                {{
                    uniform token info:id = "UsdPreviewSurface"
                    color3f inputs:diffuseColor = ({color[0]:g}, {color[1]:g}, {color[2]:g})
                    float inputs:roughness = 0.9
                    float inputs:metallic = 0
                    token outputs:surface
                }}
            }}
            """
        ).strip()
        materials.append(mats)
        meshes.append(
            textwrap.dedent(
                f"""
                def Mesh "geo{idx}"
                {{
                    int[] faceVertexCounts = [{", ".join("3" for _ in face_counts)}]
                    int[] faceVertexIndices = [{", ".join(str(i) for i in indices)}]
                    point3f[] points = [{_fmt_points(positions)}]
                    normal3f[] normals = [{_fmt_normals(normals)}]
                    uniform token subdivisionScheme = "none"
                    rel material:binding = </Root/Materials/Mat{idx}>
                }}
                """
            ).strip()
        )

    body = "\n\n    ".join(meshes)
    mats = "\n\n        ".join(materials)
    usda = textwrap.dedent(
        f"""
        #usda 1.0
        (
            defaultPrim = "Root"
            metersPerUnit = 1
            upAxis = "Y"
        )

        def Xform "Root"
        {{
            {body}

            def Scope "Materials"
            {{
                {mats}
            }}
        }}
        """
    ).strip()
    path.write_text(usda + "\n")


def write_scene_usda(
    path: Path,
    *,
    reference: Path | None = None,
    rotate_y: float = 0.0,
    translate: tuple[float, float, float] = (0.0, 0.0, 0.0),
) -> None:
    ref_block = ""
    if reference is not None:
        ref_block = textwrap.dedent(
            f"""
            def Xform "Asset" (
                references = @{reference.resolve()}@
            )
            {{
                double3 xformOp:rotateXYZ = (0, {rotate_y:g}, 0)
                double3 xformOp:translate = ({translate[0]:g}, {translate[1]:g}, {translate[2]:g})
                uniform token[] xformOpOrder = ["xformOp:translate", "xformOp:rotateXYZ"]
            }}
            """
        ).strip()

    usda = textwrap.dedent(
        f"""
        #usda 1.0
        (
            defaultPrim = "Scene"
            metersPerUnit = 1
            upAxis = "Y"
        )

        def Xform "Scene"
        {{
            {ref_block}

            def DomeLight "Key"
            {{
                float intensity = 900
                color3f color = (1, 1, 1)
            }}
        }}
        """
    ).strip()
    path.write_text(usda + "\n")


def usd_render(scene: Path, out_png: Path, width: int = 1024) -> None:
    out_png.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        ["usdrecord", str(scene), str(out_png), "-w", str(width)],
        check=True,
        capture_output=True,
        text=True,
    )


def keyed_rgba(img: Image.Image, threshold: int = 24) -> Image.Image:
    img = img.convert("RGBA")
    px = img.load()
    w, h = img.size
    for y in range(h):
        for x in range(w):
            r, g, b, _ = px[x, y]
            if r <= threshold and g <= threshold and b <= threshold:
                px[x, y] = (0, 0, 0, 0)
    return img


def trim_alpha(img: Image.Image, pad: int = 6) -> Image.Image:
    px = img.load()
    w, h = img.size
    points = [(x, y) for y in range(h) for x in range(w) if px[x, y][3] > 8]
    if not points:
        return img
    xs = [p[0] for p in points]
    ys = [p[1] for p in points]
    return img.crop(
        (
            max(0, min(xs) - pad),
            max(0, min(ys) - pad),
            min(w, max(xs) + pad + 1),
            min(h, max(ys) + pad + 1),
        )
    )


def fit_tall(img: Image.Image, size: tuple[int, int]) -> Image.Image:
    fitted = ImageOps.contain(img, size, method=Image.Resampling.LANCZOS)
    out = Image.new("RGBA", size, (0, 0, 0, 0))
    out.paste(fitted, ((size[0] - fitted.width) // 2, (size[1] - fitted.height) // 2), fitted)
    return out


def square_icon(img: Image.Image, size: int) -> Image.Image:
    side = max(img.size)
    sq = Image.new("RGBA", (side, side), (0, 0, 0, 0))
    sq.paste(img, ((side - img.width) // 2, (side - img.height) // 2), img)
    return sq.resize((size, size), Image.Resampling.LANCZOS)


def render_carrot() -> Image.Image:
    scene = CACHE / "carrot-scene.usda"
    raw = CACHE / "carrot-raw.png"
    write_scene_usda(
        scene,
        reference=CARROT_USDA,
        rotate_y=-28,
        translate=(0.0, -0.55, 0.0),
    )
    usd_render(scene, raw, width=1200)
    return trim_alpha(keyed_rgba(Image.open(raw)))


def render_pip() -> Image.Image:
    pip_usda = CACHE / "pip.usda"
    scene = CACHE / "pip-scene.usda"
    raw = CACHE / "pip-raw.png"
    write_pip_usda(pip_usda)
    write_scene_usda(scene, reference=pip_usda, rotate_y=145)
    usd_render(scene, raw, width=1200)
    return trim_alpha(keyed_rgba(Image.open(raw)))


def write_prop_assets() -> None:
    if not CARROT_USDA.exists():
        raise SystemExit(f"Missing game asset: {CARROT_USDA}")

    CACHE.mkdir(parents=True, exist_ok=True)
    ASSETS.mkdir(parents=True, exist_ok=True)

    carrot = render_carrot()
    pip = render_pip()

    square_icon(carrot, 96).save(ASSETS / "icon-carrot.png", optimize=True)
    fit_tall(carrot, (80, 140)).save(ASSETS / "carrot.png", optimize=True)
    fit_tall(ImageOps.mirror(carrot), (80, 140)).save(ASSETS / "carrot-2.png", optimize=True)
    square_icon(carrot, 72).save(ASSETS / "carrot-3.png", optimize=True)
    square_icon(pip, 256).save(ASSETS / "pip-icon.png", optimize=True)

    print("rendered props from 3D assets ->", ASSETS)


def main() -> None:
    write_prop_assets()


if __name__ == "__main__":
    main()
