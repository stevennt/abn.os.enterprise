# Loop 5 program review — what the 100 issues changed (issue #240)

Loop 5 set out to make one sentence true: *a company can be modelled as an
OpenGate tenant — a group of companies or a single legal entity, each with its
own org chart, departments and folders — and its people sign in through 1ID.*

**Verdict: the tenant side is real, gated and evidenced; the identity side is
not.** 78 of the 99 scored issues are delivered — 77 closed and 1 committed but
left open (#203); this review is the 100th and is not scored. Every concern of
tenant onboarding now has a contract, a CLI and a record: shape, org, folders,
ACL, seats, plans, terms, metering, statements, export/import, health, the
onboarding guide and the go/no-go scorecard. What the loop was named after —
the 1ID login — was configured (`sso.json`, rotation runbook) but its login
path is another session's uncommitted work, and a group tenant still cannot use
the portal. The next loop is the pilot loop: finish those two, then take one
customer through.

## The loop in numbers

| Metric | Value |
|---|---|
| Issues in the loop | 100 (#141–#240, `loop:5`) |
| Closed with a commit naming them | **77** |
| Delivered, issue left open | **1** (#203) |
| Open but covered by another issue | **5** |
| Open and partially delivered | **4** |
| Open and blocked | **1** (#208) |
| Open and not started | **11** |
| Issues scored | **99** (+ this review, unscored) |
| Commits naming loop-5 issues | 88 (80 platform, 8 contract), 2026-10-31 → 11-01 |
| Target split | 91 platform, 8 both, 1 contract |
| Type split | 33 engine, 24 data, 17 touchpoint, 15 grc, 8 metamodel, 3 pilot |
| Platform at close | `resolve.py --sync` green, 1286 tests, `tsc apps/api` green |
| Contract at close | 39 existing CI steps + the new ledger check, green |

The two-day commit span (2026-10-31 → 11-01) is not a boast: 100 issues
were pushed through in a short burst, which is exactly why the breadth is high and the end-to-end paths
are few. The ledger counts issues, not depth.

## What the loop actually built

Four layers, in the order they matter:

1. **The tenant model and its files** — shape (`single`/`group`), registry,
   directory layout, per-company org charts, departments as a taxonomy, folder
   roots and ACL by unit, positions. Validated by `opengate sync` on every push.
2. **Platform contracts with records** — every commercial or legal concern is
   one Python module plus a JSON/JSONL record in the tenant folder: plans,
   seats, quota alerts, trial expiry, statements, terms, plan changes, metering,
   health, export/import, retention, SSO secrets and rotation, the scorecard.
   Each has a CLI and a `sync` validator, so "it happened" is a file.
3. **The portal surface** — org viewer, roster, folder browser, case workspace,
   admin companies, branding, readiness. Pages that read the same files.
4. **The gates and the paper** — `docs/onboarding-tenant.md` (the operator
   guide), `docs/readiness-scorecard.md` (ten gates + recorded go/no-go),
   `docs/runbook-add-company.md`, `docs/runbook-rotate-sso-secret.md`, and the
   contract docs in this repo.

## Done / not done (all 100)

Status legend: **done** = closed and a commit names it; **delivered, open** =
commit exists, issue never closed; **covered** = an open issue whose capability
shipped under another issue; **partial** = some of it shipped; **blocked** = a
named blocker; **not started** = no code.

| # | Issue | Title | Status | Evidence |
|---|---|---|---|---|
| 141 | [#141](https://github.com/stevennt/abn.os.enterprise/issues/141) | Tenant model: single entity vs group | done | [efa7544](https://github.com/stevennt/abn.platform.opengate/commit/efa754493bc795415b2c348ce0b89eb98630d65e) |
| 142 | [#142](https://github.com/stevennt/abn.os.enterprise/issues/142) | 1ID: per-tenant OIDC via sso.json | partial | — |
| 143 | [#143](https://github.com/stevennt/abn.os.enterprise/issues/143) | Map 1ID claims to tenant and company | not started | — |
| 144 | [#144](https://github.com/stevennt/abn.os.enterprise/issues/144) | Tenant registry + active-tenant resolution | done | [3eaf59e](https://github.com/stevennt/abn.platform.opengate/commit/3eaf59e4dc5ada2dcdf10b645f5eb92c9a4bed61) |
| 145 | [#145](https://github.com/stevennt/abn.os.enterprise/issues/145) | tenant-template v2: group-aware provisioning template | partial | — |
| 146 | [#146](https://github.com/stevennt/abn.os.enterprise/issues/146) | Tenant directory layout + isolation rule | done | [37b077f](https://github.com/stevennt/abn.platform.opengate/commit/37b077f1912ddfb39b7cc8e62838b99c9ad5c51d) |
| 147 | [#147](https://github.com/stevennt/abn.os.enterprise/issues/147) | Tenant profile fields for groups | done | [be98f44](https://github.com/stevennt/abn.platform.opengate/commit/be98f44ff2ae6f613b0fe8c1b2b0021473fb044e) |
| 148 | [#148](https://github.com/stevennt/abn.os.enterprise/issues/148) | Multi-company org.json | done | [cef65f7](https://github.com/stevennt/abn.platform.opengate/commit/cef65f734409912e733ccf31966067ab8cc78fff) |
| 149 | [#149](https://github.com/stevennt/abn.os.enterprise/issues/149) | Role to company scoping | covered | — |
| 150 | [#150](https://github.com/stevennt/abn.os.enterprise/issues/150) | Tenant config audit trail | covered | — |
| 151 | [#151](https://github.com/stevennt/abn.os.enterprise/issues/151) | Company org schema: units, positions, heads | partial | — |
| 152 | [#152](https://github.com/stevennt/abn.os.enterprise/issues/152) | Department taxonomy shared across companies | done | [0d95d06](https://github.com/stevennt/abn.platform.opengate/commit/0d95d060fa3abdb9f59ad74cddca07dff1de343d) |
| 153 | [#153](https://github.com/stevennt/abn.os.enterprise/issues/153) | RACI per unit per process, per company | done | [c490aca](https://github.com/stevennt/abn.platform.opengate/commit/c490acac6903f3e891bb27816c0937540e4a8a82) |
| 154 | [#154](https://github.com/stevennt/abn.os.enterprise/issues/154) | Approval authority grid per company | done | [f26bd02](https://github.com/stevennt/abn.platform.opengate/commit/f26bd02352b3e64edb5f0cd6f0ea13236ca33d44) |
| 155 | [#155](https://github.com/stevennt/abn.os.enterprise/issues/155) | Group shared-services modelling | done | [9c750e4](https://github.com/stevennt/abn.platform.opengate/commit/9c750e4c6bdbdffd95071248618dcbcda46434a9) |
| 156 | [#156](https://github.com/stevennt/abn.os.enterprise/issues/156) | Org import from CSV/XLSX | done | [49a9a28](https://github.com/stevennt/abn.platform.opengate/commit/49a9a28b6146e362bb4ca205201677b9b1dae5ba) |
| 157 | [#157](https://github.com/stevennt/abn.os.enterprise/issues/157) | Org validation: cycles, orphans, duplicate ids | done | [e4ec618](https://github.com/stevennt/abn.platform.opengate/commit/e4ec618ab2ba956fda6ba59c9d1c785cca2e7750) |
| 158 | [#158](https://github.com/stevennt/abn.os.enterprise/issues/158) | Headcount plan vs actual people | covered | — |
| 159 | [#159](https://github.com/stevennt/abn.os.enterprise/issues/159) | Org versioning with effective dates | done | [cd2aaab](https://github.com/stevennt/abn.platform.opengate/commit/cd2aaabb4952aaa13fc80344e6430caeafefc4f2) |
| 160 | [#160](https://github.com/stevennt/abn.os.enterprise/issues/160) | Unit to domain pack mapping | not started | — |
| 161 | [#161](https://github.com/stevennt/abn.os.enterprise/issues/161) | Folder taxonomy per company | done | [4505245](https://github.com/stevennt/abn.platform.opengate/commit/450524501bc8942afad8454fc6643c9f794bcb5d) |
| 162 | [#162](https://github.com/stevennt/abn.os.enterprise/issues/162) | Storage abstraction per tenant | done | [c322134](https://github.com/stevennt/abn.platform.opengate/commit/c32213481766bd0d2d292be859c54438699bb2ad) |
| 163 | [#163](https://github.com/stevennt/abn.os.enterprise/issues/163) | Upload policy: quota, type allowlist, size | done | [ee702c2](https://github.com/stevennt/abn.platform.opengate/commit/ee702c27cabb1b75eabebed7494c39661ab0964e) |
| 164 | [#164](https://github.com/stevennt/abn.os.enterprise/issues/164) | Path safety: no traversal, tenant prefix | done | [b3d20b7](https://github.com/stevennt/abn.platform.opengate/commit/b3d20b7ea6d76c7e2a13ce921ddce5d160a9a651) |
| 165 | [#165](https://github.com/stevennt/abn.os.enterprise/issues/165) | Per-folder ACLs tied to org units | done | [708b2cf](https://github.com/stevennt/abn.platform.opengate/commit/708b2cfee6b900d6b4db0d9b6b3a47fbafb48b3a) |
| 166 | [#166](https://github.com/stevennt/abn.os.enterprise/issues/166) | Case to folder to document linking | done | [8822fd3](https://github.com/stevennt/abn.platform.opengate/commit/8822fd3681cba28d32c89a922660b9962f5d80e0) |
| 167 | [#167](https://github.com/stevennt/abn.os.enterprise/issues/167) | Retention policy per folder type | done | [f82433b](https://github.com/stevennt/abn.platform.opengate/commit/f82433b450006cce9862b6880a4ac818f4c37f3a) |
| 168 | [#168](https://github.com/stevennt/abn.os.enterprise/issues/168) | Per-tenant search index | done | [c6104db](https://github.com/stevennt/abn.platform.opengate/commit/c6104dbb3ef561835002c79c95d9e77261ede7d0) |
| 169 | [#169](https://github.com/stevennt/abn.os.enterprise/issues/169) | Bulk import (zip + manifest) | done | [3b6a5dc](https://github.com/stevennt/abn.platform.opengate/commit/3b6a5dc434bb9b9148ca1a1a9b0b4e0c436c7eed) |
| 170 | [#170](https://github.com/stevennt/abn.os.enterprise/issues/170) | Storage usage metering per company | partial | — |
| 171 | [#171](https://github.com/stevennt/abn.os.enterprise/issues/171) | Department pack: business/operations | done | [4d8ee67](https://github.com/stevennt/abn.platform.opengate/commit/4d8ee67e71cfe056250b5b2e530e1811dbd838a4) |
| 172 | [#172](https://github.com/stevennt/abn.os.enterprise/issues/172) | Department pack: HR | done | [fe7af90](https://github.com/stevennt/abn.platform.opengate/commit/fe7af90b18ac17dc09a713d9d6f669892c93df2c) |
| 173 | [#173](https://github.com/stevennt/abn.os.enterprise/issues/173) | Department pack: documents/knowledge | done | [97c7a1f](https://github.com/stevennt/abn.platform.opengate/commit/97c7a1f8ec47c0c540bb0d286e26e8d57b722791) |
| 174 | [#174](https://github.com/stevennt/abn.os.enterprise/issues/174) | Department pack: marketing | done | [a687d86](https://github.com/stevennt/abn.platform.opengate/commit/a687d86d28879f164695c10d3f476c588b239d98) |
| 175 | [#175](https://github.com/stevennt/abn.os.enterprise/issues/175) | Pack composition per tenant plan | covered | — |
| 176 | [#176](https://github.com/stevennt/abn.os.enterprise/issues/176) | Pack version pinning per tenant (bundle refs) | done | [cba71c7](https://github.com/stevennt/abn.platform.opengate/commit/cba71c79c4ee30d699ba81d2f38831914826e3ad) |
| 177 | [#177](https://github.com/stevennt/abn.os.enterprise/issues/177) | First enterprise tenant pack set | done | [2b06ee8](https://github.com/stevennt/abn.platform.opengate/commit/2b06ee8be03c38739a5261e1da7647ec12ddec43), [7d5e333](https://github.com/stevennt/abn.os.enterprise/commit/7d5e333e160da86cf9e5499e88438e176ec751d9) |
| 178 | [#178](https://github.com/stevennt/abn.os.enterprise/issues/178) | Link abn.os.enterprise industries to tenant companies | done | [f01983e](https://github.com/stevennt/abn.platform.opengate/commit/f01983e80118f4d5079879f8ec3f6d3834135751), [b439088](https://github.com/stevennt/abn.os.enterprise/commit/b439088b153ef2a8d411c5c734804b0c6c4c2c74) |
| 179 | [#179](https://github.com/stevennt/abn.os.enterprise/issues/179) | Pack lint gate for new department packs | done | [dbc6c1c](https://github.com/stevennt/abn.platform.opengate/commit/dbc6c1c3df918f7f84dccc90e7bf0380839e1bb2), [9c90113](https://github.com/stevennt/abn.platform.opengate/commit/9c90113f258c78b41360f139af171ce52581e7d8) |
| 180 | [#180](https://github.com/stevennt/abn.os.enterprise/issues/180) | Industry registry to pack mapping | not started | — |
| 181 | [#181](https://github.com/stevennt/abn.os.enterprise/issues/181) | Tenant boundary test suite | done | [43086f7](https://github.com/stevennt/abn.platform.opengate/commit/43086f758359a397387c5ce8cc957cac69537f7b) |
| 182 | [#182](https://github.com/stevennt/abn.os.enterprise/issues/182) | 1ID token tenant enforcement | not started | — |
| 183 | [#183](https://github.com/stevennt/abn.os.enterprise/issues/183) | Per-tenant secrets handling | done | [ef4f434](https://github.com/stevennt/abn.platform.opengate/commit/ef4f4342ac835e408c481ef0b675918d53944c38) |
| 184 | [#184](https://github.com/stevennt/abn.os.enterprise/issues/184) | Jurisdiction and data-residency tagging | done | [9382271](https://github.com/stevennt/abn.platform.opengate/commit/938227106483987d448c6799e375a4bd3f7cc18e) |
| 185 | [#185](https://github.com/stevennt/abn.os.enterprise/issues/185) | PII classification per tenant field | done | [242ca4b](https://github.com/stevennt/abn.platform.opengate/commit/242ca4b9e8c73189d6fc6231cff537bffc4ebc3e) |
| 186 | [#186](https://github.com/stevennt/abn.os.enterprise/issues/186) | Platform admin vs tenant admin separation | covered | — |
| 187 | [#187](https://github.com/stevennt/abn.os.enterprise/issues/187) | Break-glass access with audit | done | [44fc76c](https://github.com/stevennt/abn.platform.opengate/commit/44fc76c52ae470246131469f711fe6f93f27a7d7) |
| 188 | [#188](https://github.com/stevennt/abn.os.enterprise/issues/188) | Per-tenant rate limits | not started | — |
| 189 | [#189](https://github.com/stevennt/abn.os.enterprise/issues/189) | Tenant export bundle | done | [c9b7761](https://github.com/stevennt/abn.platform.opengate/commit/c9b776124ea2d067f7a773885c0bf45c17aedcf8) |
| 190 | [#190](https://github.com/stevennt/abn.os.enterprise/issues/190) | Tenant offboarding and deletion | done | [01c8328](https://github.com/stevennt/abn.platform.opengate/commit/01c8328161e37cbee79c43b00533abd556be0fa6) |
| 191 | [#191](https://github.com/stevennt/abn.os.enterprise/issues/191) | Onboarding wizard v2: group or single | not started | — |
| 192 | [#192](https://github.com/stevennt/abn.os.enterprise/issues/192) | Wizard step: companies | not started | — |
| 193 | [#193](https://github.com/stevennt/abn.os.enterprise/issues/193) | Wizard step: connect 1ID | not started | — |
| 194 | [#194](https://github.com/stevennt/abn.os.enterprise/issues/194) | Wizard step: departments | not started | — |
| 195 | [#195](https://github.com/stevennt/abn.os.enterprise/issues/195) | Wizard step: folders | done | [bd280c8](https://github.com/stevennt/abn.platform.opengate/commit/bd280c8354dc83c57cdc8e612f7e3ec1e18773e3) |
| 196 | [#196](https://github.com/stevennt/abn.os.enterprise/issues/196) | Dry-run provisioning | done | [a6716fb](https://github.com/stevennt/abn.platform.opengate/commit/a6716fbafaf3702910f06ea6466d9067e0268032) |
| 197 | [#197](https://github.com/stevennt/abn.os.enterprise/issues/197) | Idempotent provisioner | done | [dfd595e](https://github.com/stevennt/abn.platform.opengate/commit/dfd595ef9e4360a113ba0713126f682bbe721c59) |
| 198 | [#198](https://github.com/stevennt/abn.os.enterprise/issues/198) | Provisioning rollback | done | [1094910](https://github.com/stevennt/abn.platform.opengate/commit/109491080189a48b1213843b76ee15b5f57d2462) |
| 199 | [#199](https://github.com/stevennt/abn.os.enterprise/issues/199) | Golden tenant acceptance test | done | [94c3fed](https://github.com/stevennt/abn.platform.opengate/commit/94c3fedd5f3856eae7ce2cfad4854b255e2f9661) |
| 200 | [#200](https://github.com/stevennt/abn.os.enterprise/issues/200) | Onboarding API contract | done | [196f62b](https://github.com/stevennt/abn.platform.opengate/commit/196f62b300efd7f133337ba929f505b61fa539f6) |
| 201 | [#201](https://github.com/stevennt/abn.os.enterprise/issues/201) | Tenant/company switcher | not started | — |
| 202 | [#202](https://github.com/stevennt/abn.os.enterprise/issues/202) | Company-scoped dashboard | not started | — |
| 203 | [#203](https://github.com/stevennt/abn.os.enterprise/issues/203) | Org chart viewer | delivered, open | [1e0c1da](https://github.com/stevennt/abn.platform.opengate/commit/1e0c1dac85af3a765cf63c78d793420925616ad4) |
| 204 | [#204](https://github.com/stevennt/abn.os.enterprise/issues/204) | Roster and positions page | done | [6b531b2](https://github.com/stevennt/abn.platform.opengate/commit/6b531b289b93661d95aad3ae905617b614c1a151) |
| 205 | [#205](https://github.com/stevennt/abn.os.enterprise/issues/205) | Folder browser | done | [2803ef1](https://github.com/stevennt/abn.platform.opengate/commit/2803ef1c1255f6c2e6f6cd9f144faf2506bc7cdb) |
| 206 | [#206](https://github.com/stevennt/abn.os.enterprise/issues/206) | Case workspace | done | [47e22b0](https://github.com/stevennt/abn.platform.opengate/commit/47e22b0089d8357228ae2842322a1d874e24e7cc) |
| 207 | [#207](https://github.com/stevennt/abn.os.enterprise/issues/207) | Admin console: companies | done | [d1bf01e](https://github.com/stevennt/abn.platform.opengate/commit/d1bf01ee1d9f4e2fe730b3d928f370825d421147) |
| 208 | [#208](https://github.com/stevennt/abn.os.enterprise/issues/208) | Admin console: identity status | blocked | — |
| 209 | [#209](https://github.com/stevennt/abn.os.enterprise/issues/209) | Per-tenant branding | done | [67a5795](https://github.com/stevennt/abn.platform.opengate/commit/67a57954cc8cbfdc6d0ca57244d69553e396594e) |
| 210 | [#210](https://github.com/stevennt/abn.os.enterprise/issues/210) | Onboarding checklist after provisioning | done | [5a3a944](https://github.com/stevennt/abn.platform.opengate/commit/5a3a944c92d3526c2cf72c2051bcd0bb808b0082) |
| 211 | [#211](https://github.com/stevennt/abn.os.enterprise/issues/211) | Dataset scoping per tenant | done | [3794bd1](https://github.com/stevennt/abn.platform.opengate/commit/3794bd199ed156f1e1adbab6922a705b5f758240) |
| 212 | [#212](https://github.com/stevennt/abn.os.enterprise/issues/212) | Model pinning per tenant | done | [718e478](https://github.com/stevennt/abn.platform.opengate/commit/718e478da12d084886e6bdec0507e4a24e66d0f8) |
| 213 | [#213](https://github.com/stevennt/abn.os.enterprise/issues/213) | Trace retention policy per tenant | done | [55c8228](https://github.com/stevennt/abn.platform.opengate/commit/55c8228fbedc2cf405b5a0aa31321e2a0893c1dd) |
| 214 | [#214](https://github.com/stevennt/abn.os.enterprise/issues/214) | Per-tenant usage analytics | done | [0f1f7d3](https://github.com/stevennt/abn.platform.opengate/commit/0f1f7d345246f0281f2ed10140f126427b8047af) |
| 215 | [#215](https://github.com/stevennt/abn.os.enterprise/issues/215) | Metering event schema | done | [d75583c](https://github.com/stevennt/abn.platform.opengate/commit/d75583c6dc6e232da826e9743da22e6c7619c69e) |
| 216 | [#216](https://github.com/stevennt/abn.os.enterprise/issues/216) | Tenant data import | done | [8633f97](https://github.com/stevennt/abn.platform.opengate/commit/8633f971692fff0d05d5a33c3b4aed6f1492f131) |
| 217 | [#217](https://github.com/stevennt/abn.os.enterprise/issues/217) | Tenant data export (self-service) | done | [1567795](https://github.com/stevennt/abn.platform.opengate/commit/1567795846d47cb567b2522ba31981ab961cb911) |
| 218 | [#218](https://github.com/stevennt/abn.os.enterprise/issues/218) | Golden fixtures per tenant | done | [d4d8d26](https://github.com/stevennt/abn.platform.opengate/commit/d4d8d261c07c596645df15df8672ea40a81fc4e4) |
| 219 | [#219](https://github.com/stevennt/abn.os.enterprise/issues/219) | Platform-level cross-tenant benchmark | done | [716c730](https://github.com/stevennt/abn.platform.opengate/commit/716c730f99203482b8d517f298ff214535a2e1ab) |
| 220 | [#220](https://github.com/stevennt/abn.os.enterprise/issues/220) | Tenant data catalog | done | [255eef6](https://github.com/stevennt/abn.platform.opengate/commit/255eef6f2ffb3268cde4ae48c9e6a80d7256c1f4) |
| 221 | [#221](https://github.com/stevennt/abn.os.enterprise/issues/221) | Plan enforcement at runtime | done | [e440a64](https://github.com/stevennt/abn.platform.opengate/commit/e440a6419c71be0315a503d43ceffdab64a82790) |
| 222 | [#222](https://github.com/stevennt/abn.os.enterprise/issues/222) | Seat limits and invites | done | [775f2e5](https://github.com/stevennt/abn.platform.opengate/commit/775f2e52d6e4754f2d5ee08cf591d8a615f30bf5) |
| 223 | [#223](https://github.com/stevennt/abn.os.enterprise/issues/223) | Quota alerts | done | [ecde01e](https://github.com/stevennt/abn.platform.opengate/commit/ecde01e64452395bf0e8f0155c816ef01490a8d3) |
| 224 | [#224](https://github.com/stevennt/abn.os.enterprise/issues/224) | Trial expiry behaviour | done | [5349bfb](https://github.com/stevennt/abn.platform.opengate/commit/5349bfbb09c976415b50acfcca2a14f97f2a3013) |
| 225 | [#225](https://github.com/stevennt/abn.os.enterprise/issues/225) | Metering to invoices (no billing yet) | done | [1983f25](https://github.com/stevennt/abn.platform.opengate/commit/1983f255ec225d118325112ed6f1ef4828aa87b6) |
| 226 | [#226](https://github.com/stevennt/abn.os.enterprise/issues/226) | Contract and terms per tenant | done | [4698669](https://github.com/stevennt/abn.platform.opengate/commit/4698669b9b0fdee06e1a8699072084dd09d72526) |
| 227 | [#227](https://github.com/stevennt/abn.os.enterprise/issues/227) | Upgrade and downgrade path | done | [88db5b0](https://github.com/stevennt/abn.platform.opengate/commit/88db5b0c6db03698827b364a62a0c8f51ac62493) |
| 228 | [#228](https://github.com/stevennt/abn.os.enterprise/issues/228) | Group pricing and rollup | done | [1f6f303](https://github.com/stevennt/abn.platform.opengate/commit/1f6f303bb81a48c1129e1628790b32d153e76cda) |
| 229 | [#229](https://github.com/stevennt/abn.os.enterprise/issues/229) | Tenant health score | done | [0f75ff3](https://github.com/stevennt/abn.platform.opengate/commit/0f75ff339128aed9ac04e449f1ed2c878dc8db64) |
| 230 | [#230](https://github.com/stevennt/abn.os.enterprise/issues/230) | Commercial onboarding pack | done | [11ca1e2](https://github.com/stevennt/abn.platform.opengate/commit/11ca1e257cf712824a1c40484fb8b749399e0989), [a7baab4](https://github.com/stevennt/abn.os.enterprise/commit/a7baab409dce013bd296b57aafc500565b878dfa) |
| 231 | [#231](https://github.com/stevennt/abn.os.enterprise/issues/231) | Enterprise OS model per company (repo template) | done | [cd0327a](https://github.com/stevennt/abn.os.enterprise/commit/cd0327aa7cfaabbd000308d877513e95d0653581) |
| 232 | [#232](https://github.com/stevennt/abn.os.enterprise/issues/232) | Tenant to enterprise-repo mapping | done | [3d9c7b0](https://github.com/stevennt/abn.platform.opengate/commit/3d9c7b0e9362016db485dddfc7a26c2ef818b574), [0226e9e](https://github.com/stevennt/abn.os.enterprise/commit/0226e9e52ec23ce5720bff2957425e0cf794af1b) |
| 233 | [#233](https://github.com/stevennt/abn.os.enterprise/issues/233) | Sync enterprise tags to tenant pins | done | [d37ddc5](https://github.com/stevennt/abn.platform.opengate/commit/d37ddc54a02502633c2598b75739f40e597874dd), [06cb032](https://github.com/stevennt/abn.os.enterprise/commit/06cb03253900fe3b439e2c5887fb1edd4adfba39) |
| 234 | [#234](https://github.com/stevennt/abn.os.enterprise/issues/234) | Pilot: single-entity tenant end to end | done | [368c875](https://github.com/stevennt/abn.platform.opengate/commit/368c875825296933e9b232b3dac25cc358fa19b4) |
| 235 | [#235](https://github.com/stevennt/abn.os.enterprise/issues/235) | Pilot: two-company group end to end | done | [86125ae](https://github.com/stevennt/abn.platform.opengate/commit/86125ae55ce91fd46915fea650f1eb32cdd6c4fa) |
| 236 | [#236](https://github.com/stevennt/abn.os.enterprise/issues/236) | Ops runbook: add a company to a group | done | [377b9b0](https://github.com/stevennt/abn.platform.opengate/commit/377b9b0df906c87c7c1baea733f1950efdb1595d) |
| 237 | [#237](https://github.com/stevennt/abn.os.enterprise/issues/237) | Ops runbook: rotate 1ID client secret | done | [6d5d551](https://github.com/stevennt/abn.platform.opengate/commit/6d5d5513134bc24827023676544c16458b585d96), [5724900](https://github.com/stevennt/abn.platform.opengate/commit/5724900be430d0d81de194bb940ccecfe1e59d05) |
| 238 | [#238](https://github.com/stevennt/abn.os.enterprise/issues/238) | Tenant onboarding guide (operator facing) | done | [e287f18](https://github.com/stevennt/abn.platform.opengate/commit/e287f18d6f2984240c19fb4d7f9d7c2a6c4441a9), [3eb0116](https://github.com/stevennt/abn.os.enterprise/commit/3eb0116efff40011f8b2b82bcd2767c344f99e93) |
| 239 | [#239](https://github.com/stevennt/abn.os.enterprise/issues/239) | Tenant readiness scorecard | done | [e0ffb40](https://github.com/stevennt/abn.platform.opengate/commit/e0ffb4060a1f9be76313da036b1b53220c656791), [ca67d70](https://github.com/stevennt/abn.platform.opengate/commit/ca67d70eae843d74627af3f2e9b56a8a3d2f0102), [e3ce80c](https://github.com/stevennt/abn.os.enterprise/commit/e3ce80c3f4e8a2e1046234e9720736ce2397174a) |
| 240 | [#240](https://github.com/stevennt/abn.os.enterprise/issues/240) | Program review: what the 100 issues changed | this review | — |

## The open 22, one by one

**Delivered, issue not closed (1)**

- **#203 — Org chart viewer.** Commit `1e0c1da`; page and tests are in `HEAD`.
  The issue was never closed. Bookkeeping, not engineering: close it.

**Covered by another issue (5)** — the capability exists, the issue was left open:

- **#149 — Role to company scoping.** Units are company-local and cross-company
  references are refused (`tenant_registry.find_unit`, #148); an account carries
  a unit, so its role is scoped to that company.
- **#150 — Tenant config audit trail.** Config changes write one audit chain
  (domains, companies, branding, accounts) via `companies.core.auditAppend`
  (#207).
- **#158 — Headcount plan vs actual.** The roster page merges `positions[]`
  (plan) against accounts + pending invites (actual) (#204).
- **#175 — Pack composition per tenant plan.** `onboarding/plans.json` defines
  each plan's pack list; plan change enables/disables packs with a checklist
  (#221/#227).
- **#186 — Platform admin vs tenant admin separation.** `platform-admin` is a
  distinct role with `tenant='*'`; `/ops`, `/audit`, `/benchmark`, `/exit` are
  platform-only (#207 phase A, `0e46aeaf`).

**Partial (4)**

- **#142 — 1ID per-tenant OIDC via sso.json.** Schema, validator and the
  rotation runbook shipped (#237); the login itself is #208.
- **#145 — tenant-template v2, group-aware.** Groups are provisioned by
  `gateway/provision.py` and documented (#238); the template itself is still
  single-entity.
- **#151 — Company org schema: units, positions, heads.** Units and roles are in
  `schemas/org.json`, positions in `schemas/positions.json` (#204); there is no
  unit `head` field.
- **#170 — Storage usage metering per company.** Metering events are attributed
  per company and carry a storage dimension (#214/#215), but the storage gauge
  is tenant-level.

**Blocked (1)**

- **#208 — Admin console: identity status.** Blocked on the unmerged SSO layer
  (`sso.service.ts`, `sso.controller.ts`, `web/app/login/sso` are untracked);
  the blocker comment on the issue has the details.

**Not started (11)**

#143 (claim mapping), #160 (unit→pack mapping), #180 (industry→pack mapping),
#182 (token tenant enforcement), #188 (per-tenant rate limits), #191–#194
(onboarding wizard v2: group/single, companies, 1ID, departments), #201
(switcher), #202 (company-scoped dashboard).

## Top-5 blockers

1. **1ID login is not merged (#208, #142, #143, #182).** At `HEAD`,
   `GET /auth/sso/status` returns 404 — the run behind `docs/onboarding-tenant.md`
   proved it against a `git archive HEAD` checkout. `sso.service.ts`,
   `sso.controller.ts` and `web/app/login/sso/` are another session's untracked
   work; `openid-client` is imported only by the untracked `sso.service.ts`.
   Everything around it shipped; the door is missing.
2. **A group tenant cannot use the portal.** The API loads one tenant-level
   chart (`OrgService` reads `customers/<tenant>/org.json`); a group keeps one
   chart per company. The same run logged in as a group admin and every guarded
   request returned 403 `unknown unit 'hr' in tenant 'grp'`. #201, #202, #149,
   #151, #158 all sit behind this.
3. **People onboarding is not shippable.** At `HEAD`, `/admin/invites` is not
   mapped (`admin.controller.ts` has no invite routes; `invite.service.ts` is
   untracked), mail is a log stub, and the first admin must be hand-written into
   `accounts.json` or come from `/signup`. #222 shipped seat and invite
   *validation* in Python, not the delivery path.
4. **Go-live evidence cannot include a real login.** Gate 9 of the scorecard
   (#239) proves the SSO *configuration*; #237's Step 4 is a recorded human
   smoke test; no external IdP was reachable in any run. Today a tenant can be
   "ready" with an identity path nobody has exercised.
5. **No per-tenant rate limits or abuse controls at the API edge (#188).** Only
   signup has a limiter (per-IP, kill-switch). Uploads, exports and every
   authenticated route are unbounded. Before a customer portal is on the
   internet, that is a blocker, not a nicety.

## Next loop: the pilot loop (proposal)

**Principle: depth over breadth.** Loop 6 does not start a 100th surface. It
finishes the two paths the loop promised and takes one real customer through
them. Exit is a signed go/no-go, not a merged PR count.

Six workstreams, each with an exit test:

| # | Workstream | Exit test |
|---|---|---|
| A | **1ID end to end** — merge the SSO layer, claim→tenant/company mapping, token enforcement, `ssoOnly`, step-up policy | a real login against a staging IdP for a `ssoOnly` tenant, and a rotation drill recorded |
| B | **Group portal** — per-company chart resolution, company context on every request, switcher, company dashboard, unit heads | a two-company tenant where both companies sign in and see only their own chart and folders |
| C | **People and invites** — invite routes, real mail delivery, first-admin path, seat enforcement at the edge, offboarding | a tenant admin invites, onboards and offboards a person without a shell |
| D | **Lifecycle surface** — scorecard page, plan/terms/statements pages, export/import UI | a tenant admin reaches `/readiness` 100% and sees the scorecard without the CLI |
| E | **Trust and abuse** — per-tenant rate limits, audit-chain verify in CI, red-team rerun | the red-team suite green with limits on |
| F | **The real pilot** — one customer, one IdP, one go/no-go, one offboarding | a recorded `go` in `go-no-go.jsonl` and a clean offboarding certificate |

First 24 issues (the rest are cut after the pilot, not invented now):

| ID | Issue | Workstream |
|---|---|---|
| L6-001 | Merge the SSO service + controller with tests (unblocks #208) | A |
| L6-002 | Claim → tenant/company mapping (`sub`, email fallback, uniqueness) | A |
| L6-003 | Token tenant enforcement: no cross-tenant session | A |
| L6-004 | `ssoOnly` + kill-switch semantics, login page hides the password form | A |
| L6-005 | MFA / step-up policy per tenant (or a written no-MFA decision) | A |
| L6-006 | Per-company chart resolution in `OrgService` + tests | B |
| L6-007 | Company context on every guarded request | B |
| L6-008 | Tenant/company switcher in the web app | B |
| L6-009 | Company-scoped dashboard | B |
| L6-010 | Unit `head` + headcount plan vs actual on `/roster` | B |
| L6-011 | Invite routes at `HEAD` (`/admin/invites` CRUD) + tests | C |
| L6-012 | Real mail sender for invites (verification, bounce handling) | C |
| L6-013 | First-admin path without a shell (platform or signup) | C |
| L6-014 | Seat enforcement at the API edge + offboarding | C |
| L6-015 | Scorecard page + `GET /admin/scorecard` (read-only) | D |
| L6-016 | Plan / terms / statements pages wired to the existing routes | D |
| L6-017 | Export / import UI over the existing bundles | D |
| L6-018 | Readiness → scorecard handoff (one list, one gate) | D |
| L6-019 | Per-tenant rate limits (#188) | E |
| L6-020 | Audit-chain verify in CI, with a receipt per run | E |
| L6-021 | Red-team rerun with limits on | E |
| L6-022 | Staging run against a real IdP (Entra or Keycloak) | F |
| L6-023 | One real tenant through the scorecard, signed | F |
| L6-024 | Offboarding drill + certificate | F |

**Not doing next loop:** more industry packs, more domain scaffolds, SAML, a
second portal, or another 100-issue sweep. Those are breadth; the loop just
learned what breadth alone buys.

**Entry gate:** the five blockers above are closed or explicitly waived with an
owner and a date. **Exit gate:** `docs/core/readiness-scorecard.md`'s ten gates
pass for a real tenant, the decision is recorded, and this review is repeated
with the next 100.

## Method and limits

- Status is mechanical where it can be: GitHub issue state plus a commit naming
  the issue (`Issue #NNN:`) in either repo. `scripts/loop_ledger_check.py`
  re-checks the ledger offline — commits exist and name their issue, the
  summary adds up, and this review's table matches the ledger row for row.
- The 22 open issues without a commit are classified by hand, each with a
  pointer to the code or the blocker, in `docs/core/loop5-ledger.json`. "Covered"
  is a judgement: the capability exists under another issue, which does not make
  the issue's own intent fully met.
- **#203 is the one bookkeeping failure**: delivered (`1e0c1da`), never closed.
  Close it in loop 6 and adopt the rule the late loop-5 dispatches used — a
  commit either closes its issue or says why not.
- Numbers are from the repositories at the close-out: platform code at
  `e0ffb40` (this review's platform half is `110e610`), contract at this commit.
  They are reproducible from the ledger, not from memory.

## Pointers

- `docs/core/loop5-ledger.json` — the data behind the table (100 rows)
- `docs/core/onboarding-tenant.md` — the operator guide the loop produced
- `docs/core/readiness-scorecard.md` — the go/no-go gate
- `docs/core/commercial-onboarding.md`, `company-mapping.md`, `pack-mapping.md` —
  the commercial and contract edges
- `abn.platform.opengate` → `docs/program-review.md` — the platform close-out
