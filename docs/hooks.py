"""MkDocs hook: replaces <!-- RULES --> with a table built from ganda_grammar.RULES."""
import ganda_grammar as gg


def on_page_markdown(markdown, **kwargs):
    if "<!-- RULES -->" not in markdown:
        return markdown
    rows = ["| Rule | What it corrects | Source |", "|---|---|---|"]
    for rule, (description, source) in gg.RULES.items():
        rows.append(f"| `{rule}` | {description} | {source} |".replace("\n", " "))
    return markdown.replace("<!-- RULES -->", "\n".join(rows))
