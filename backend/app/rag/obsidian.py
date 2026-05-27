from pathlib import Path
import hashlib
import re


IGNORED_DIRS = {".obsidian", ".trash", ".git"}


def iter_obsidian_notes(vault_path: str | Path) -> list[Path]:
    vault_path = Path(vault_path).expanduser().resolve()

    notes = []
    for path in vault_path.rglob("*.md"):
        # Obsidian 的配置目录和回收站不属于知识内容，入库会引入噪声。
        relative_parts = path.relative_to(vault_path).parts
        if any(part in IGNORED_DIRS for part in relative_parts):
            continue
        notes.append(path)

    return sorted(notes)


def build_obsidian_document_id(vault_path: str | Path, note_path: str | Path) -> str:
    vault_path = Path(vault_path).expanduser().resolve()
    note_path = Path(note_path).expanduser().resolve()
    relative_path = note_path.relative_to(vault_path).as_posix()
    # 用 Vault 内相对路径生成稳定 id：同一篇笔记重复导入时 document_id 不变，方便覆盖旧 chunks。
    digest = hashlib.md5(relative_path.encode("utf-8")).hexdigest()
    return f"obsidian-{digest}"


def extract_obsidian_metadata(vault_path: str | Path, note_path: str | Path) -> dict:
    vault_path = Path(vault_path).expanduser().resolve()
    note_path = Path(note_path).expanduser().resolve()
    text = note_path.read_text(encoding="utf-8", errors="ignore")

    relative_path = note_path.relative_to(vault_path).as_posix()
    folder = note_path.parent.relative_to(vault_path).as_posix()
    title = extract_title(text) or note_path.stem

    # 这些 metadata 会跟随每个 chunk 写入 Chroma，并最终返回给 Obsidian 插件做来源展示和打开笔记。
    metadata = {
        "source_type": "obsidian",
        "vault_name": vault_path.name,
        "vault_relative_path": relative_path,
        "folder": "" if folder == "." else folder,
        "title": title,
    }

    tags = extract_tags(text)
    # Chroma 不接受空 list 作为 metadata 值，所以只有存在标签/双链时才写入。
    if tags:
        metadata["tags"] = tags

    links = extract_wikilinks(text)
    if links:
        metadata["links"] = links

    return metadata


def extract_title(text: str) -> str | None:
    # 优先使用 Markdown 一级标题作为展示标题，比 “未命名.md” 这类文件名更适合做引用来源。
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("# "):
            return stripped[2:].strip()
    return None


def extract_tags(text: str) -> list[str]:
    # 同时支持 Obsidian 常见的 frontmatter tags 和正文内联 #tag。
    frontmatter_tags = extract_frontmatter_tags(text)
    inline_tags = re.findall(r"(?<!\w)#([\w\u4e00-\u9fff/-]+)", text)
    return sorted(set(frontmatter_tags + inline_tags))


def extract_frontmatter_tags(text: str) -> list[str]:
    frontmatter = extract_frontmatter(text)
    if not frontmatter:
        return []

    tags = []
    lines = frontmatter.splitlines()

    for index, line in enumerate(lines):
        stripped = line.strip()
        if not stripped.startswith("tags:"):
            continue

        value = stripped.removeprefix("tags:").strip()

        if value.startswith("[") and value.endswith("]"):
            tags.extend(
                item.strip().strip("'\"")
                for item in value[1:-1].split(",")
                if item.strip()
            )
            continue

        if value:
            tags.extend(
                item.strip().strip("'\"")
                for item in re.split(r"[, ]+", value)
                if item.strip()
            )
            continue

        for next_line in lines[index + 1 :]:
            next_stripped = next_line.strip()
            if next_stripped.startswith("- "):
                tags.append(next_stripped[2:].strip().strip("'\""))
                continue
            if next_stripped and not next_line.startswith((" ", "\t")):
                break

    return tags


def extract_frontmatter(text: str) -> str | None:
    if not text.startswith("---"):
        return None

    lines = text.splitlines()
    for index, line in enumerate(lines[1:], start=1):
        if line.strip() == "---":
            return "\n".join(lines[1:index])

    return None


def extract_wikilinks(text: str) -> list[str]:
    # 提取 Obsidian 双链。[[目标|别名]] 只保留真实目标，后续可用于关联笔记检索增强。
    links = re.findall(r"\[\[([^\]]+)\]\]", text)
    normalized_links = []

    for link in links:
        target = link.split("|", 1)[0].strip()
        if target:
            normalized_links.append(target)

    return sorted(set(normalized_links))
