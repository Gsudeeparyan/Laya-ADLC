# Third-party notices

Laya-ADLC's own content is proprietary, for Laya Healthcare's internal use. It includes the third-party material below, under these licences.

## Matt Pocock's skills

**Where:** `technical/skills-and-agents/skills/`, in the 27 skills with `metadata.source: mattpocock/skills@...`.
**Source:** https://github.com/mattpocock/skills, pinned commit in `technical/skills-and-agents/MATT-POCOCK-SKILLS.md`.
**Changes:** adapted for GitHub Copilot by `technical/platform/tools/vendor_matt_skills.py`, as listed in that file. Local instructions references were converted to `.github/copilot-instructions.md`, calls to a "Skill tool" became instructions to read the sibling skill, and each skill's `agents/openai.yaml` was removed.

```text
MIT License

Copyright (c) 2026 Matt Pocock

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

## Agent rules from books

**Where:** the five `RULES.md` files in `technical/skills-and-agents/skills/`: `legacy-change`, `production-ready`, `data-design`, `bounded-contexts` and `refactoring-pass`.
**Source:** https://github.com/mattpocock/agent-rules-books, v0.5, commit a7d7649. Each file has its own attribution header.

```text
MIT License

Copyright (c) 2026 Maciej Ciemborowicz

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

## Microsoft's JSON schemas

**Where:** `technical/platform/tests/schemas/`. Copies of Microsoft's published schemas for declarative agents and plugins, used only in tests to validate the packages.
**Source:** https://developer.microsoft.com/json-schemas/copilot/

## Ideas, without copied text

These influenced the library, but no text was copied:

- Microsoft HVE Core (role guides), MIT.
- Birgitta Böckeler's article on harness engineering, and Simon Willison's "lethal trifecta".
- Several open-source skill collections, surveyed on 05/11/2026 and not included. Their ideas on evidence-based review, approval tied to an exact commit, and read-only reviewers were rewritten from scratch. The collections themselves were left out because they included telemetry, remote code at install time, permission-bypass flags, offensive-security tooling, and unclear licences on individual items.
