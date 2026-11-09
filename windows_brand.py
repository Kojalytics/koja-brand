#!/usr/bin/env python3
"""Kojalytics branding for the Windows installer and exe of one Koja app (run in its repo):

    python3 brand/windows_brand.py <repo>

- Publisher: ArtCraft's company "Learning Machines LLC" becomes "Kojalytics" in packaging/windows
  (MSI Manufacturer, registry keys) and in the exe's VERSIONINFO (build.rs CompanyName, added
  where the app sets none).
- Windows Settings: the shared installer UI's own entry is registered as Kojalytics.<id> with the
  plain app name (ArtCraft's says "(Craft Apps)" under Craft.<id>).
- Signing: packaging/windows/sign.ps1 also signs through SSL.com eSigner (jsign, pinned) when the
  ES_* secrets are set, and links the signature to kojalytics.com/software.
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

# SSL.com eSigner for packaging/windows/sign.ps1 (Kojalytics signs with an IV certificate whose key
# lives in SSL.com's cloud HSM): jsign, pinned by its SHA-256, signs exe and MSI through eSigner.
JSIGN_URL = "https://repo1.maven.org/maven2/net/jsign/jsign/7.6/jsign-7.6.jar"
JSIGN_SHA256 = "6CF58AA080E7FF82656F320CFF8D4A3BFF30408DF8766806DCBA3740DD839FA5"
ESIGNER_DETECT = (
    "$haveAzure = -not ($azureVars | Where-Object { -not [Environment]::GetEnvironmentVariable($_) })\n",
    "$haveAzure = -not ($azureVars | Where-Object { -not [Environment]::GetEnvironmentVariable($_) })\n"
    "# SSL.com eSigner (Kojalytics): ES_USERNAME, ES_PASSWORD, CREDENTIAL_ID, ES_TOTP_SECRET.\n"
    "$esignerVars = 'ES_USERNAME', 'ES_PASSWORD', 'CREDENTIAL_ID', 'ES_TOTP_SECRET'\n"
    "$haveESigner = -not ($esignerVars | Where-Object { -not [Environment]::GetEnvironmentVariable($_) })\n",
)
ESIGNER_NONE = (
    "if (-not $haveCert -and -not $haveAzure) {\n"
    '  Write-Warn "Windows signing secrets not set (WINDOWS_CERTIFICATE or AZURE_*): leaving unsigned: $($Files -join \', \')"',
    "if (-not $haveCert -and -not $haveAzure -and -not $haveESigner) {\n"
    '  Write-Warn "Windows signing secrets not set (ES_* for SSL.com eSigner, WINDOWS_CERTIFICATE or AZURE_*): leaving unsigned: $($Files -join \', \')"',
)
ESIGNER_SIGN = (
    "try {\n  if ($haveCert) {\n",
    "try {\n"
    "  if ($haveESigner) {\n"
    '    Write-Output "Signing with SSL.com eSigner: $($Files -join \', \')"\n'
    "    $jar = Join-Path $tmp 'jsign.jar'\n"
    f"    Invoke-WebRequest -Uri '{JSIGN_URL}' -OutFile $jar\n"
    f"    if ((Get-FileHash -Algorithm SHA256 $jar).Hash -ne '{JSIGN_SHA256}') {{ throw 'jsign.jar does not match its pinned SHA-256' }}\n"
    "    # jsign reads the secrets from the environment (env:NAME), so none of them is on a command line.\n"
    '    $env:ESIGNER_STOREPASS = "$env:ES_USERNAME|$env:ES_PASSWORD"\n'
    "    $ts = if ($env:WINDOWS_TIMESTAMP_URL) { $env:WINDOWS_TIMESTAMP_URL } else { 'http://ts.ssl.com' }\n"
    "    $name = $common[[array]::IndexOf($common, '/d') + 1]\n"
    "    $url = $common[[array]::IndexOf($common, '/du') + 1]\n"
    "    & java -jar $jar --storetype ESIGNER --storepass env:ESIGNER_STOREPASS --alias $env:CREDENTIAL_ID --keypass env:ES_TOTP_SECRET `\n"
    "      --alg SHA-256 --tsaurl $ts --tsmode RFC3161 --name $name --url $url @Files\n"
    "    $code = $LASTEXITCODE\n"
    "    Remove-Item Env:ESIGNER_STOREPASS -ErrorAction SilentlyContinue\n"
    '    if ($code -ne 0) { throw "jsign (SSL.com eSigner) failed with exit code $code" }\n'
    "  }\n"
    "  elseif ($haveCert) {\n",
)
# The signature's "more information" link: the Koja apps' page, not the GitHub repo.
SIGN_URL = ("'/du', 'https://github.com/Kojalytics/", "'/du', 'https://www.kojalytics.com/software'")


def esigner(text: str) -> str:
    if "$haveESigner" in text or "$haveAzure = " not in text:
        return text
    for old, new in (ESIGNER_DETECT, ESIGNER_NONE, ESIGNER_SIGN):
        if old not in text:
            raise SystemExit(f"sign.ps1 changed upstream, eSigner not added: {old[:60]!r}")
        text = text.replace(old, new, 1)
    return text


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
        if path.name == "sign.ps1":
            new = esigner(new)
            new = re.sub(r"'/du', 'https://github\.com/Kojalytics/[A-Za-z0-9_.-]+'", "'/du', 'https://www.kojalytics.com/software'", new)
        if new != text:
            path.write_text(new, encoding="utf-8")
            changed.append(str(path.relative_to(repo)))
    print(f"windows branding: {len(changed)} files" + (": " + ", ".join(changed) if changed else ""))


if __name__ == "__main__":
    main()
