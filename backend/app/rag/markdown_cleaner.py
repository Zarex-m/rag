import re
from pathlib import Path


FRONTMATTER_PATTERN = re.compile(r"\A---\s*\n.*?\n---\s*\n?", re.DOTALL)
FENCED_CODE_PATTERN = re.compile(r"```.*?```", re.DOTALL)


def strip_frontmatter(text: str) -> str:
    return FRONTMATTER_PATTERN.sub("", text, count=1)


def extract_markdown_title(text: str, fallback: str) -> str:
    for line in text.splitlines():
        line = line.strip()
        if not line.startswith("#"):
            continue

        title = line.lstrip("#").strip()
        if title:
            return title

    return fallback


def extract_markdown_tags(text: str) -> list[str]:
    tags = set()

    frontmatter_match = FRONTMATTER_PATTERN.match(text)
    if frontmatter_match:
        frontmatter = frontmatter_match.group(0)
        for line in frontmatter.splitlines():
            line = line.strip()
            if not line.startswith("tags:"):
                continue

            raw_tags = line.removeprefix("tags:").strip()
            for tag in re.split(r"[,，\s\[\]]+", raw_tags):
                tag = tag.strip().lstrip("#")
                if tag:
                    tags.add(tag)

    for tag in re.findall(r"(?<!\w)#([\u4e00-\u9fffA-Za-z0-9_-]+)", text):
        tags.add(tag)

    return sorted(tags)


def build_title_path(vault_name: str, relative_path: Path, title: str) -> str:
    parts = [vault_name]
    parts.extend(part for part in relative_path.parent.parts if part and part != ".")
    if title:
        parts.append(title)
    else:
        parts.append(relative_path.stem)

    return " > ".join(parts)


def remove_markdown_images(text: str) -> str:
    # Obsidian embeds: ![[image.png]] / ![[note#section]]
    text = re.sub(r"!\[\[[^\]]+\]\]", "", text)

    # Standard markdown images: ![alt](url)
    text = re.sub(r"!\[[^\]]*\]\([^)]+\)", "", text)

    return text


def normalize_obsidian_links(text: str) -> str:
    def replace_wiki_link(match: re.Match) -> str:
        content = match.group(1).strip()
        if not content:
            return ""

        if "|" in content:
            return content.split("|")[-1].strip()

        if "#" in content:
            return content.split("#")[-1].strip()

        return content

    return re.sub(r"\[\[([^\]]+)\]\]", replace_wiki_link, text)


def normalize_markdown_links(text: str) -> str:
    return re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)


def remove_html_comments(text: str) -> str:
    return re.sub(r"<!--.*?-->", "", text, flags=re.DOTALL)


def normalize_callouts(text: str) -> str:
    # > [!note] title  -> title
    text = re.sub(r"^>\s*\[![A-Za-z0-9_-]+\]\s*", "", text, flags=re.MULTILINE)
    # > content        -> content
    text = re.sub(r"^>\s?", "", text, flags=re.MULTILINE)
    return text


def clean_markdown_text(text: str) -> str:
    if not text:
        return ""

    code_blocks: list[str] = []

    def preserve_code_block(match: re.Match) -> str:
        code_blocks.append(match.group(0))
        return f"\n@@CODE_BLOCK_{len(code_blocks) - 1}@@\n"

    text = FENCED_CODE_PATTERN.sub(preserve_code_block, text)
    text = strip_frontmatter(text)
    text = remove_html_comments(text)
    text = remove_markdown_images(text)
    text = normalize_obsidian_links(text)
    text = normalize_markdown_links(text)
    text = normalize_callouts(text)

    for index, code_block in enumerate(code_blocks):
        text = text.replace(f"@@CODE_BLOCK_{index}@@", code_block)

    text = re.sub(r"\n{3,}", "\n\n", text)

    return text.strip()


def inject_title_path(text: str, title_path: str) -> str:
    if not title_path:
        return text

    return f"标题路径：{title_path}\n\n{text}".strip()
