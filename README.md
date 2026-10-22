# Kojalytics brand tools

Tools that keep the Koja apps (Kojalytics' builds of the open-source ArtCraft apps) branded:

| File | What it does |
|---|---|
| `rebrand.sh <id> <KojaName>` | Applies the Kojalytics branding to a Craft app (customer-visible text, logos, license check, NOTICE, DMG background) |
| `brand-guard.sh <repo> <id>` | Fails when anything a customer sees still shows ArtCraft, a Craft name, Discord, ArtCraft's links or developer ID, or when the license check is missing |
| `sync-upstream.sh <id> <KojaName>` | Merges ArtCraft's newest release, rebrands, runs the guard and the tests |
| `koja-sync.yml` | Weekly GitHub workflow in each app repo: sync, build, sign, notarize, draft release |

The apps are MIT/Apache-2.0 licensed by the ArtCraft Team; Kojalytics is not affiliated with,
sponsored or endorsed by the ArtCraft Team. The Kojalytics name and logo are Kojalytics' own.
Inter (fonts/) is licensed under the SIL Open Font License (fonts/OFL-Inter.txt).
