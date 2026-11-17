#!/usr/bin/env python3
"""Validate authored theory, coverage declarations, protected images and reader components."""
import argparse
import base64
import hashlib
import json
import re
from pathlib import Path
from bs4 import BeautifulSoup


def validate(md_path, html_path, manifest_path):
    md = Path(md_path).read_text()
    raw = Path(html_path).read_text()
    manifest = json.loads(Path(manifest_path).read_text())
    soup = BeautifulSoup(raw, "html.parser")
    article = soup.select_one(".prose")
    errors = []
    require = lambda ok, message: errors.append(message) if not ok else None
    require(article is not None, "Missing .prose article body")
    if article is None:
        return errors
    for match in re.finditer(r"^(?P<fence>`{3,}|~{3,})(?P<info>[^\n]*)\n.*?^(?P=fence)[ \t]*$", md, re.M | re.S):
        require(match.group("info").strip() == "mermaid", "Executable code fence in theory Markdown")
    require(soup.find("h1") is not None and bool(soup.find("h1").get_text(strip=True)), "Missing lesson title")
    require(soup.find("title") is not None and bool(soup.find("title").get_text(strip=True)), "Missing document title")
    ids = [node["id"] for node in soup.select("[id]")]
    require(len(ids) == len(set(ids)), "Duplicate HTML IDs")
    for link in soup.select('a[href^="#"]'):
        require(link["href"][1:] in ids, "Unresolved fragment: " + link["href"])
    for tag in soup.select('script[src], link[rel="stylesheet"]'):
        require(False, "External runtime dependency: " + str(tag)[:100])
    require(not re.search(r"url\(\s*['\"]?https?://", raw), "Remote CSS asset")
    payloads = set()
    for img in soup.select("img"):
        uri = img.get("src", "")
        require(uri.startswith("data:image/"), "Image not embedded: " + uri[:100])
        require(bool(img.get("alt")), "Image lacks alternative text")
        try:
            payload = base64.b64decode(uri.split(",", 1)[1], validate=True)
            payloads.add(hashlib.sha256(payload).hexdigest())
        except Exception:
            require(False, "Invalid base64 image")
    for asset in manifest.get("protected_images", []):
        require(asset.get("sha256") in payloads, "Protected image missing or changed: " + asset.get("label", "unnamed"))
    coverage = manifest.get("coverage", [])
    require(bool(manifest.get("source_url") or manifest.get("source_path")), "Manifest needs source_url or source_path")
    require(isinstance(coverage, list) and bool(coverage), "Missing source coverage inventory")
    for key in ("required_figures", "required_components", "protected_images"):
        require(key in manifest and isinstance(manifest[key], list), "Manifest list required: " + key)
    require(not article.select("figure") or bool(manifest.get("required_figures")), "Figures must be inventoried in required_figures")
    article_text = article.get_text(" ", strip=True)
    # Count all static panels, including those enhanced into non-default views.
    prose_copy = BeautifulSoup(str(article), "html.parser")
    for node in prose_copy.select("script,style,svg"):
        node.decompose()
    word_count = len(prose_copy.get_text().strip().split())
    word_limit = manifest.get("word_limit", 2500)
    require(isinstance(word_limit, int) and word_limit > 0, "word_limit must be a positive integer")
    if isinstance(word_limit, int) and word_limit > 2500:
        require(bool(manifest.get("word_limit_authorization")), "Higher word limit requires explicit authorization")
    if isinstance(word_limit, int):
        require(word_count <= word_limit, f"Prose word budget exceeded: {word_count} > {word_limit}; trim additions and repetition before source concepts")
    for row in coverage:
        name = row.get("source_item", "unnamed source item")
        require(row.get("reviewed") is True, "Source item not reviewed: " + name)
        require(len(row.get("review_note", "").strip()) >= 20, "Substantive coverage review note required: " + name)
        if row.get("status") == "authorized_omission":
            require(bool(row.get("authorization")), "Omission lacks user authorization: " + name)
            continue
        require(row.get("status") in ("preserved", "expanded"), "Invalid coverage status: " + name)
        require(bool(row.get("output_anchor")) and row["output_anchor"] in ids, "Missing source anchor: " + name)
        for evidence in row.get("evidence", []):
            require(evidence in article_text, "Source evidence string missing: " + evidence)
    figures = article.select("figure")
    for figure_id in manifest.get("required_figures", []):
        require(article.find("figure", id=figure_id) is not None, "Required figure missing: " + figure_id)
    for fig in figures:
        require(bool(fig.select_one("img,svg")), "Figure lacks a graphic: " + fig.get("id", "unnamed"))
        caption = fig.find_next_sibling()
        require(caption is not None and "caption" in caption.get("class", []), "Figure lacks its adjacent numbered caption")
    for kind in ("Figure", "Table"):
        numbers = [int(x) for x in re.findall(r"\*" + kind + r" (\d+):", md)]
        require(numbers == list(range(1, len(numbers) + 1)), kind + " captions are missing, duplicated or out of order")
    for widget in soup.select("[data-stepper], .walkthrough, [data-comparison], .evidence-switcher"):
        stepper = widget.has_attr("data-stepper") or "walkthrough" in widget.get("class", [])
        button_selector, panel_selector = ("[data-step]", ".step-panel") if stepper else ("[data-mode]", ".mode-panel")
        controls_selector, status_selector = (".step-controls", ".step-status") if stepper else (".mode-controls", ".switch-status")
        buttons, panels = widget.select(button_selector), widget.select(panel_selector)
        require(len(buttons) == len(panels) and len(panels) >= (1 if stepper else 2), "Component button/panel count mismatch: " + widget.get("id", "unnamed"))
        targets = [button.get("aria-controls") for button in buttons]
        require(set(targets) == {panel.get("id") for panel in panels} and len(targets) == len(set(targets)), "Component aria-controls mapping invalid")
        controls = widget.select_one(controls_selector)
        require(controls is not None and controls.has_attr("hidden"), "Inactive component controls must begin hidden")
        require(all(not panel.has_attr("hidden") for panel in panels), "Component panels must be visible without JavaScript")
        for button in buttons:
            require(button.name == "button" and button.get("type") == "button", "Use native type=button for component controls")
        status = widget.select_one(status_selector)
        require(status is not None and status.get("aria-live") == "polite", "Missing polite component status")
        if stepper:
            require(widget.select_one('[data-walk="previous"]') is not None and widget.select_one('[data-walk="next"]') is not None, "Stepper requires Previous/Next")
    for component in manifest.get("required_components", []):
        widget = soup.find(id=component["id"])
        require(widget is not None, "Required component missing: " + component["id"])
        if widget:
            selector = ".step-panel" if component["type"] == "stepper" else ".mode-panel"
            require(len(widget.select(selector)) == component["count"], "Required component panel count differs: " + component["id"])
    return errors


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("markdown")
    parser.add_argument("html")
    parser.add_argument("manifest")
    args = parser.parse_args()
    errors = validate(args.markdown, args.html, args.manifest)
    if errors:
        for error in errors:
            print("FAIL:", error)
        raise SystemExit(1)
    print("PASS: source declarations, figures, embedded assets and component contracts")


if __name__ == "__main__":
    main()
