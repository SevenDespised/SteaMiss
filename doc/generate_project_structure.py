from __future__ import annotations

import ast
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


@dataclass(frozen=True)
class ClassInfo:
    name: str
    methods: list[str]


@dataclass(frozen=True)
class ModuleInfo:
    rel_path: str
    functions: list[str]
    classes: list[ClassInfo]
    parse_error: str | None = None


@dataclass
class TreeNode:
    name: str
    children: list["TreeNode"]


SKIP_DIR_NAMES = {
    ".git",
    ".idea",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    ".tox",
    ".venv",
    "venv",
    "env",
    "node_modules",
    "dist",
    "build",
    "__pycache__",
}

SKIP_FILE_SUFFIXES = {
    ".pyc",
    ".pyo",
    ".pyd",
    ".so",
    ".dll",
    ".exe",
    ".obj",
    ".lib",
}

SKIP_FILE_NAMES = {
    ".DS_Store",
}


def _read_text_best_effort(path: Path) -> str:
    data = path.read_bytes()
    for enc in ("utf-8", "utf-8-sig", "gbk", "cp936"):
        try:
            return data.decode(enc)
        except UnicodeDecodeError:
            continue
    return data.decode("utf-8", errors="replace")


def _is_skipped_dir(dir_path: Path) -> bool:
    return dir_path.name in SKIP_DIR_NAMES


def _is_skipped_file(file_path: Path) -> bool:
    if file_path.name in SKIP_FILE_NAMES:
        return True
    if file_path.suffix.lower() in SKIP_FILE_SUFFIXES:
        return True
    return False


def iter_files(root: Path) -> Iterable[Path]:
    for current_root, dirs, files in os.walk(root):
        current_root_path = Path(current_root)

        # Mutate dirs in-place to prune walk
        dirs[:] = [d for d in dirs if not _is_skipped_dir(current_root_path / d)]

        for file_name in files:
            file_path = current_root_path / file_name
            if _is_skipped_file(file_path):
                continue
            yield file_path


def _render_tree_lines(node: TreeNode, prefix: str = "", is_last: bool = True) -> list[str]:
    branch = "└── " if is_last else "├── "
    lines: list[str] = [f"{prefix}{branch}{node.name}\n"]
    if not node.children:
        return lines

    child_prefix = prefix + ("    " if is_last else "│   ")
    for idx, child in enumerate(node.children):
        lines.extend(_render_tree_lines(child, prefix=child_prefix, is_last=(idx == len(node.children) - 1)))
    return lines


def _sorted_dir_entries(dir_path: Path) -> tuple[list[Path], list[Path]]:
    try:
        entries = list(dir_path.iterdir())
    except OSError:
        return ([], [])

    dirs = sorted([p for p in entries if p.is_dir() and not _is_skipped_dir(p)], key=lambda p: p.name.lower())
    files = sorted([p for p in entries if p.is_file() and not _is_skipped_file(p)], key=lambda p: p.name.lower())
    return (dirs, files)


def build_src_tree_with_symbols(src_root: Path) -> str:
    def build_dir_node(dir_path: Path) -> TreeNode:
        dirs, files = _sorted_dir_entries(dir_path)
        children: list[TreeNode] = []

        for d in dirs:
            children.append(build_dir_node(d))

        for f in files:
            if f.suffix.lower() == ".py":
                module = parse_python_module(f, root=src_root)
                file_children: list[TreeNode] = []

                if module.parse_error:
                    file_children.append(TreeNode(name=f"（解析失败：{module.parse_error}）", children=[]))
                else:
                    # 顶层函数
                    for fn in module.functions:
                        file_children.append(TreeNode(name=f"def {fn}()", children=[]))

                    # 类 + 方法
                    for c in module.classes:
                        method_nodes = [TreeNode(name=f"{m}()", children=[]) for m in c.methods]
                        file_children.append(TreeNode(name=f"class {c.name}", children=method_nodes))

                children.append(TreeNode(name=f.name, children=file_children))
            else:
                children.append(TreeNode(name=f.name, children=[]))

        return TreeNode(name=dir_path.name + "/", children=children)

    root_node = build_dir_node(src_root)
    lines: list[str] = []
    lines.append("```\n")
    # 顶层根节点不需要前缀分支符号，手动渲染其 children
    lines.append(f"{root_node.name}\n")
    for idx, child in enumerate(root_node.children):
        lines.extend(_render_tree_lines(child, prefix="", is_last=(idx == len(root_node.children) - 1)))
    lines.append("```\n")
    return "".join(lines)


def parse_python_module(py_path: Path, root: Path) -> ModuleInfo:
    rel_path = py_path.relative_to(root).as_posix()
    try:
        source = _read_text_best_effort(py_path)
        tree = ast.parse(source, filename=str(py_path))
    except Exception as e:  # noqa: BLE001 - best-effort doc generation
        return ModuleInfo(rel_path=rel_path, functions=[], classes=[], parse_error=f"{type(e).__name__}: {e}")

    functions: list[str] = []
    classes: list[ClassInfo] = []

    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            functions.append(node.name)
        elif isinstance(node, ast.ClassDef):
            methods: list[str] = []
            for child in node.body:
                if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    methods.append(child.name)
            classes.append(ClassInfo(name=node.name, methods=methods))

    # 保留原始定义顺序更贴近源码阅读习惯；仅对类名做稳定排序意义不大
    return ModuleInfo(rel_path=rel_path, functions=functions, classes=classes)

def main() -> None:
    project_root = Path(__file__).resolve().parents[1]
    src_root = project_root / "src"
    out_path = project_root / "doc" / "项目结构总览.md"

    # 仅整理 src 目录
    all_files = sorted(iter_files(src_root), key=lambda p: p.relative_to(src_root).as_posix().lower())
    py_files = [p for p in all_files if p.suffix.lower() == ".py"]
    modules = [parse_python_module(p, root=src_root) for p in py_files]

    content_lines: list[str] = []
    content_lines.append("# SteaMiss（src）结构总览\n\n")
    content_lines.append("说明：\n")
    content_lines.append("- 本文档由脚本自动生成，仅包含 src/ 下的目录结构与 Python 符号（文件、类、方法、顶层函数）。\n")
    content_lines.append("- 默认忽略缓存/构建/依赖目录（例如 __pycache__/、.venv/、dist/、build/ 等）与二进制文件。\n\n")

    content_lines.append("## 目录树（含类与方法）\n\n")
    content_lines.append(build_src_tree_with_symbols(src_root))
    content_lines.append("\n")

    out_path.write_text("".join(content_lines), encoding="utf-8")
    print(f"Generated: {out_path}")
    print(f"Python modules parsed: {len(modules)}")


if __name__ == "__main__":
    main()
