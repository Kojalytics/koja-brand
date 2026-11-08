#!/usr/bin/env python3
"""Kojalytics branding for the Windows installer and exe of one Koja app (run in its repo):

    python3 brand/windows_brand.py <repo>

- Publisher: ArtCraft's company "Learning Machines LLC" becomes "Kojalytics" in packaging/windows
  (MSI Manufacturer, registry keys) and in the exe's VERSIONINFO (build.rs CompanyName, added
  where the app sets none).
- Windows Settings: the shared installer UI's own entry is registered as Kojalytics.<id> with the
  plain app name (ArtCraft's says "(Craft Apps)" under Craft.<id>).
- Installer identity: every random (version 4) GUID in packaging/windows/*.wxs|*.wxi (UpgradeCode,
  Upgrade Id, Component Guid) becomes a version 5 GUID derived from it. The Koja MSI is then its
  own product: ArtCraft's app of the same kind can't upgrade it, block it or share components.
  Derived, not random: the same ArtCraft GUID always gives the same Koja GUID, so every sync keeps
  the Koja app's UpgradeCode, and a version 5 GUID is never derived again (idempotent).
"""
import pathlib
import re
import sys
import uuid

KOJA_NS = uuid.UUID("6b6f6a61-6c79-5463-a000-77696e646f77")
# An exe's VERSIONINFO without a CompanyName (winresource in build.rs) gets one, after ProductName.
COMPANY = re.compile(r'(\.set\("ProductName", "[^"]*"\)\n)((\s*)\.set\()')
GUID = re.compile(r"\b([0-9A-Fa-f]{8})-([0-9A-Fa-f]{4})-([0-9A-Fa-f]{4})-([0-9A-Fa-f]{4})-([0-9A-Fa-f]{12})\b")


def koja_guid(m: re.Match) -> str:
    if m.group(3)[0] != "4":
        return m.group(0)
    new = str(uuid.uuid5(KOJA_NS, "kojalytics:" + m.group(0).upper())).upper()
    return new if m.group(0).isupper() else new.lower()


def main() -> None:
    repo = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else ".")
    changed = []
    win = repo / "packaging" / "windows"
    files = [p for p in win.rglob("*") if p.is_file()] if win.is_dir() else []
    files += [p for p in repo.glob("apps/*/build.rs")] + [p for p in repo.glob("crates/*/build.rs")]
    for path in files:
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        new = text.replace("Learning Machines LLC", "Kojalytics")
        # The shared installer UI (installer-ui.wxs) adds its own Windows Settings entry: under a
        # Kojalytics key (ArtCraft's app of the same kind uses Craft.<id>) and with the plain app name.
        new = new.replace("CurrentVersion\\Uninstall\\Craft.", "CurrentVersion\\Uninstall\\Kojalytics.")
        new = new.replace('Value="[ProductName] (Craft Apps)"', 'Value="[ProductName]"')
        new = new.replace("<!-- Legacy Launchers match the canonical MSI name exactly; keep this alias distinct. -->",
                          "<!-- The Kojalytics Launcher reads only MSI product-code entries, so this one keeps the plain name. -->")
        if path.name == "build.rs" and '.set("ProductName"' in new and "CompanyName" not in new:
            new = COMPANY.sub(lambda m: f'{m.group(1)}{m.group(3)}.set("CompanyName", "Kojalytics")\n{m.group(2)}', new, count=1)
        if path.suffix in (".wxs", ".wxi"):
            new = GUID.sub(koja_guid, new)
        if new != text:
            path.write_text(new, encoding="utf-8")
            changed.append(str(path.relative_to(repo)))
    print(f"windows branding: {len(changed)} files" + (": " + ", ".join(changed) if changed else ""))


if __name__ == "__main__":
    main()
