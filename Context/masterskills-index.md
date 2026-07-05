# masterskills-index.md
# Format version: 1.1
# Last updated: 2026-07-05
# Owner: Shawn

Lightweight, tracked index of MasterSkills referenced by this project. Per the MasterSkills Folder Policy, actual skill files are never committed to this repository — only pointers (artifact URI, version, short description) live here. The real files live in a secure artifact store, private package registry, or local developer machine.

## Currently in use

None. TransitSense v0.1.x does not import any MasterSkills.

## Format for future entries

```
- name: <masterskill-name>
  version: <semver>
  artifact_uri: artifact://masterskills/<name>/<version>
  description: <one line>
  license: <license>
  required_permissions: <e.g. read-artifacts>
  used_by: <agent/skill name(s) in agents.md/skills.md>
```

If a MasterSkill is added later, add an entry here, reference it by artifact URI in the relevant agent/skill's Context field in `agents.md`/`skills.md`, and log the run details (name@version, artifact URI, test result) in the CRAFT Log's `MasterSkills Used` field in `progress.md`.
