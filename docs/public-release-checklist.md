# Public release checklist

The repository remains private until every required item is checked.

## Source and history

- [x] Current tracked files contain no token, database, browser profile, personal export or real candidate data.
- [x] Git history contains no recoverable structured secret or personal path.
- [x] Redundant binary review archives are removed.
- [x] `.gitignore` covers runtime, build, release and personal-data paths.

## Product truth

- [x] README describes desktop v1.0.7 and Skill v0.1.0 accurately.
- [x] CI uses only the fictional fixture generator.
- [x] Download links point to the published v1.0.7 release assets.
- [x] Known limitations include unsigned binaries, manual extension loading and sample bias.
- [x] Browser collection is described as BOSS直聘-only, user-triggered and
  subject to platform terms.

## Verification

- [x] Extension `npm ci`, type check and build pass.
- [x] Unified 29-group core baseline passes from fictional data.
- [x] Packaged ZIP smoke test passes.
- [x] Installer install/start/uninstall/data-retention smoke test passes.
- [x] Skill validation and API-contract tests pass.
- [x] GitHub Actions succeeds on the public-readiness pull request and `main`.
- [x] Tests are organized by environment and discovered by the unified runner.

## Repository settings

- [x] MIT license is present in the release-readiness branch.
- [x] Security policy is present in the release-readiness branch.
- [ ] Repository description and topics match the product.
- [ ] Private vulnerability reporting is enabled when available.
- [ ] Default branch protection is configured after the first successful CI run.

## Final action

Only after the checklist passes:

1. merge the public-polish pull request;
2. complete the repository description, topics and branch protection;
3. let the repository owner switch visibility from private to public;
4. open the public README in a signed-out browser;
5. verify the CI badge and every release link.
