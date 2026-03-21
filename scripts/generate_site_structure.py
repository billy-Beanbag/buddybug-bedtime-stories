#!/usr/bin/env python3
"""
Generate a family-tree style PDF of the Buddybug website structure.
Outputs: docs/website-structure.html (open in browser, Print > Save as PDF)
"""

import os
from pathlib import Path

# Routes derived from app/**/page.tsx - path segments to display labels
ROUTES = [
    ("/", "Home"),
    ("/login", "Login"),
    ("/register", "Register"),
    ("/register/free", "Register Free"),
    ("/register/premium", "Register Premium"),
    ("/profile", "Profile"),
    ("/library", "Library"),
    ("/reader/[bookId]", "Reader"),
    ("/saved", "Saved Stories"),
    ("/children", "Children"),
    ("/children/[childId]/comfort", "Child Comfort"),
    ("/settings", "Settings"),
    ("/settings/account", "Account"),
    ("/settings/family", "Family"),
    ("/settings/downloads", "Downloads"),
    ("/settings/notifications", "Notifications"),
    ("/settings/privacy", "Privacy"),
    ("/settings/about", "About"),
    ("/achievements", "Achievements"),
    ("/reading-plans", "Reading Plans"),
    ("/reading-plans/[planId]", "Plan Detail"),
    ("/educator", "Educator"),
    ("/educator/classroom-sets/[setId]", "Classroom Set"),
    ("/getting-started", "Getting Started"),
    ("/getting-started/child", "Child Setup"),
    ("/onboarding", "Onboarding"),
    ("/onboarding/child", "Onboarding Child"),
    ("/onboarding/preferences", "Preferences"),
    ("/onboarding/bedtime", "Bedtime Mode"),
    ("/onboarding/first-story", "First Story"),
    ("/pricing", "Pricing"),
    ("/upgrade", "Upgrade"),
    ("/refer", "Refer a Friend"),
    ("/gifts", "Gifts"),
    ("/promo", "Redeem Code"),
    ("/bedtime-pack", "Bedtime Pack"),
    ("/continue-reading", "Continue Reading"),
    ("/read-along", "Read Along"),
    ("/family-digest", "Family Digest"),
    ("/notifications", "Notifications"),
    ("/campaigns/[campaignKey]", "Campaign"),
    ("/for-parents", "For Parents"),
    ("/how-it-works", "How It Works"),
    ("/features", "Features"),
    ("/faq", "FAQ"),
    ("/support", "Support"),
    ("/privacy", "Privacy"),
    ("/privacy-policy", "Privacy Policy"),
    ("/terms", "Terms"),
    ("/whats-new", "What's New"),
    ("/parental-controls", "Parental Controls"),
    ("/beta", "Beta"),
    ("/status", "Status"),
    # Admin
    ("/admin", "Admin"),
    ("/admin/ideas", "Ideas"),
    ("/admin/editorial", "Editorial"),
    ("/admin/editorial/[projectId]", "Editorial Project"),
    ("/admin/translations", "Translations"),
    ("/admin/story-pages", "Story Pages"),
    ("/admin/lifecycle/[userId]", "User Lifecycle"),
    ("/admin/moderation", "Moderation"),
    ("/admin/moderation/[caseId]", "Moderation Case"),
    ("/admin/changelog", "Changelog"),
    ("/admin/beta", "Beta"),
    ("/admin/beta/[cohortId]", "Beta Cohort"),
    ("/admin/visual-references", "Visual References"),
    ("/admin/housekeeping", "Housekeeping"),
    ("/admin/drafts", "Drafts"),
    ("/admin/drafts/[draftId]", "Draft Detail"),
    ("/admin/organization", "Organization"),
    ("/admin/api-keys", "API Keys"),
    ("/admin/reporting", "Reporting"),
    ("/admin/illustrations", "Illustrations"),
    ("/admin/workflow", "Workflow"),
    ("/admin/status", "Admin Status"),
    ("/admin/billing-recovery", "Billing Recovery"),
    ("/admin/billing-recovery/[caseId]", "Recovery Case"),
    ("/admin/search", "Search"),
    ("/admin/feature-flags", "Feature Flags"),
    ("/admin/account-health", "Account Health"),
    ("/admin/support", "Support"),
    ("/admin/support/[ticketId]", "Support Ticket"),
    ("/admin/books", "Books"),
    ("/admin/analytics", "Analytics"),
    ("/admin/audio", "Audio"),
    ("/admin/story-quality", "Story Quality"),
    ("/admin/maintenance", "Maintenance"),
    ("/admin/runbooks", "Runbooks"),
    ("/admin/incidents", "Incidents"),
    ("/admin/incidents/[incidentId]", "Incident"),
]


def path_to_id(path: str) -> str:
    """Convert path to valid Mermaid node ID (alphanumeric + underscore only)."""
    s = path.replace("/", "_").replace("[", "").replace("]", "").replace("-", "_").strip("_")
    return s if s else "root"


def build_tree() -> list[tuple[str, str, str | None]]:
    """Return (path, label, parent_path) for each route."""
    result = []
    for path, label in ROUTES:
        if path == "/":
            parent = None
        else:
            parts = path.strip("/").split("/")
            if len(parts) == 1:
                parent = "/"
            else:
                parent_parts = parts[:-1]
                parent = "/" + "/".join(parent_parts) if parent_parts else "/"
        result.append((path, label, parent))
    return result


def generate_mermaid(tree: list[tuple[str, str, str | None]]) -> str:
    """Generate Mermaid flowchart for family tree."""
    lines = ["flowchart TB", "    direction TB"]
    node_ids = {}
    for path, label, parent in tree:
        nid = path_to_id(path)
        node_ids[path] = nid
        safe_label = label.replace('"', "'")
        lines.append(f'    {nid}["{safe_label}"]')

    for path, label, parent in tree:
        if parent is None:
            continue
        pid = path_to_id(parent)
        nid = path_to_id(path)
        if nid != pid:
            lines.append(f"    {pid} --> {nid}")

    return "\n".join(lines)


def generate_html(mermaid_code: str) -> str:
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Buddybug Website Structure</title>
  <script src="https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.min.js"></script>
  <style>
    * {{ box-sizing: border-box; }}
    body {{
      font-family: system-ui, -apple-system, sans-serif;
      margin: 0;
      padding: 2rem;
      background: #f8fafc;
      color: #1e293b;
    }}
    h1 {{
      font-size: 1.75rem;
      font-weight: 700;
      color: #4338ca;
      margin-bottom: 0.5rem;
    }}
    .subtitle {{
      color: #64748b;
      font-size: 0.95rem;
      margin-bottom: 2rem;
    }}
    #diagram {{
      background: white;
      border-radius: 1rem;
      padding: 2rem;
      box-shadow: 0 4px 6px -1px rgb(0 0 0 / 0.1);
      overflow-x: auto;
      min-height: 400px;
    }}
    .mermaid {{
      display: flex;
      justify-content: center;
    }}
    .mermaid svg {{
      max-width: 100%;
    }}
    .print-hint {{
      margin-top: 2rem;
      padding: 1rem 1.25rem;
      background: #eef2ff;
      border-radius: 0.75rem;
      font-size: 0.9rem;
      color: #4338ca;
    }}
    @media print {{
      body {{ background: white; padding: 1rem; }}
      #diagram {{ box-shadow: none; border: 1px solid #e2e8f0; }}
      .print-hint {{ display: none; }}
    }}
  </style>
</head>
<body>
  <h1>Buddybug Website Structure</h1>
  <p class="subtitle">Family tree view of routes and pages</p>
  <div id="diagram">
    <pre class="mermaid">
{mermaid_code}
    </pre>
  </div>
  <p class="print-hint">
    To save as PDF: press <kbd>Ctrl+P</kbd> (or <kbd>Cmd+P</kbd> on Mac), then choose "Save as PDF" as the destination.
  </p>
  <script>
    mermaid.initialize({{ startOnLoad: true, theme: 'base', themeVariables: {{
      primaryColor: '#e0e7ff',
      primaryTextColor: '#312e81',
      primaryBorderColor: '#6366f1',
      lineColor: '#94a3b8',
      secondaryColor: '#f1f5f9',
      tertiaryColor: '#f8fafc'
    }}}});
  </script>
</body>
</html>
"""


def main():
    script_dir = Path(__file__).resolve().parent
    project_root = script_dir.parent
    output_dir = project_root / "docs"
    output_dir.mkdir(exist_ok=True)

    tree = build_tree()
    mermaid = generate_mermaid(tree)

    # Write Mermaid source (.mmd) for PDF generation via mermaid-cli
    mmd_path = output_dir / "website-structure.mmd"
    mmd_path.write_text(mermaid, encoding="utf-8")
    print(f"Generated: {mmd_path}")

    # Write HTML for browser view / print-to-PDF
    html_path = output_dir / "website-structure.html"
    html_path.write_text(generate_html(mermaid), encoding="utf-8")
    print(f"Generated: {html_path}")

    # Try to generate PDF via mermaid-cli
    pdf_path = output_dir / "website-structure.pdf"
    import subprocess
    try:
        subprocess.run(
            ["npx", "-y", "@mermaid-js/mermaid-cli", "mmdc", "-i", str(mmd_path), "-o", str(pdf_path), "-b", "white"],
            check=True,
            capture_output=True,
            cwd=str(project_root),
        )
        print(f"Generated: {pdf_path}")
    except (subprocess.CalledProcessError, FileNotFoundError) as e:
        print("PDF generation skipped (run: npx -y @mermaid-js/mermaid-cli mmdc -i docs/website-structure.mmd -o docs/website-structure.pdf)")
        print("Or open docs/website-structure.html in a browser and use Ctrl+P > Save as PDF.")


if __name__ == "__main__":
    main()
