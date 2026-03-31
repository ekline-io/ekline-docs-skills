# Terminology Rules

These terminology rules are ALWAYS enforced in documentation. Consistent terminology prevents user confusion and improves searchability.

---

## Product and Feature Names

Always use the exact capitalization and spacing shown:

| Correct | Incorrect | Notes |
|---------|-----------|-------|
| Claude Code | claude code, ClaudeCode | Product name |
| API | Api, api | Always capitalized |
| CLI | Cli, cli | Always capitalized |
| SDK | Sdk, sdk | Always capitalized |
| UI | Ui, ui | Always capitalized |
| URL | Url, url | Always capitalized |
| JSON | Json, json | Always capitalized |
| YAML | Yaml, yaml | Always capitalized |
| HTML | Html, html | Always capitalized |
| CSS | Css, css | Always capitalized |

---

## Technical Terms

### Authentication & Security

| Correct | Incorrect | Notes |
|---------|-----------|-------|
| API key | api-key, API Key, Api Key | Two words, "API" caps |
| access token | Access Token, accesstoken | Lowercase unless starting sentence |
| OAuth | Oauth, oauth, OAUTH | Capital O, capital A |
| SSO | Sso, sso | Single sign-on abbreviation |
| 2FA | 2fa, two-factor | Abbreviation preferred |
| two-factor authentication | Two-Factor Authentication | Lowercase, hyphenated |

### Programming Terms

| Correct | Incorrect | Notes |
|---------|-----------|-------|
| JavaScript | Javascript, javascript | Capital J and S |
| TypeScript | Typescript, typescript | Capital T and S |
| Node.js | NodeJS, Nodejs, node.js | Exact casing with period |
| npm | NPM, Npm | Always lowercase |
| React | react, REACT | Capital R only |
| REST | Rest, rest | Representational State Transfer |
| GraphQL | Graphql, graphQL | Capital G, Q, L |
| PostgreSQL | Postgres, postgres, POSTGRESQL | Full name, exact casing |
| MongoDB | Mongodb, mongoDB | Capital M, capital DB |
| Redis | redis, REDIS | Capital R only |
| GitHub | Github, github | Capital G and H |
| GitLab | Gitlab, gitlab | Capital G and L |
| VS Code | VSCode, vscode | Space between VS and Code |

### Infrastructure Terms

| Correct | Incorrect | Notes |
|---------|-----------|-------|
| Kubernetes | kubernetes, K8s | Full name in docs, K8s in informal |
| Docker | docker, DOCKER | Capital D only |
| AWS | Aws, aws | Always capitalized |
| macOS | MacOS, MacOs, macos | Exact casing |
| Linux | linux, LINUX | Capital L only |
| Windows | windows, WINDOWS | Capital W only |

---

## Common Word Forms

### One Word vs Two Words

| Correct (Noun) | Correct (Verb) | Notes |
|----------------|----------------|-------|
| setup | set up | "Complete the setup" vs "Set up your account" |
| login | log in | "Go to the login page" vs "Log in to your account" |
| signup | sign up | "Complete signup" vs "Sign up for free" |
| checkout | check out | "Proceed to checkout" vs "Check out the docs" |
| backup | back up | "Create a backup" vs "Back up your data" |
| startup | start up | "During startup" vs "Start up the server" |

### Hyphenation Rules

| As Noun | As Adjective | Example |
|---------|--------------|---------|
| front end | front-end | "front-end development" |
| back end | back-end | "back-end services" |
| real time | real-time | "real-time updates" |
| open source | open-source | "open-source project" |
| command line | command-line | "command-line interface" |
| end user | end-user | "end-user documentation" |

---

## Action Verbs

Use these verbs consistently for these actions:

| Action | Preferred Verb | Avoid |
|--------|---------------|-------|
| Making something new | Create | Make, Add, Generate |
| Removing permanently | Delete | Remove (unless soft-delete) |
| Removing from view | Hide | Remove, Delete |
| Changing settings | Configure | Setup, Set up |
| Starting a process | Start | Begin, Initiate, Launch |
| Stopping a process | Stop | End, Terminate, Kill |
| Picking from options | Select | Choose, Pick |
| Entering text | Enter | Type, Input |
| Pressing a button | Click | Press, Hit, Tap |
| Turning on | Enable | Turn on, Activate |
| Turning off | Disable | Turn off, Deactivate |

---

## UI Element Terms

| Element Type | Correct Term | Example |
|--------------|--------------|---------|
| Clickable text | link | Click the **Settings** link |
| Action button | button | Click the **Save** button |
| Options list | dropdown | Select from the **Region** dropdown |
| Text entry | field | Enter your email in the **Email** field |
| On/off control | toggle | Enable the **Dark mode** toggle |
| Multiple selection | checkbox | Select the **Remember me** checkbox |
| Single selection | radio button | Select the **Monthly** radio button |
| Navigation section | tab | Click the **Settings** tab |
| Popup window | dialog | The confirmation dialog appears |
| Side section | sidebar | The sidebar shows your files |
| Top section | header | The header contains navigation |
| Main content | page | The dashboard page displays |

---

## Formatting Terms in Prose

When mentioning code elements in prose:

| Element Type | Format | Example |
|--------------|--------|---------|
| File names | `backticks` | Open `config.yaml` |
| Folder names | `backticks` | Navigate to `src/components` |
| Function names | `backticks()` | Call `authenticate()` |
| Variable names | `backticks` | Set the `timeout` variable |
| Parameter names | `backticks` | Pass the `userId` parameter |
| Commands | `backticks` | Run `npm install` |
| Code keywords | `backticks` | Use the `async` keyword |
| UI elements | **bold** | Click the **Submit** button |
| New terms | *italics* | This is called a *webhook* |

---

## Prohibited Terms

Never use these terms in documentation:

| Prohibited | Use Instead | Reason |
|------------|-------------|--------|
| click here | descriptive link text | Accessibility |
| above/below | link to specific section | Fragile reference |
| he/she, his/her | they, their | Inclusive language |
| blacklist/whitelist | blocklist/allowlist | Inclusive language |
| master/slave | primary/replica | Inclusive language |
| sanity check | quick check, validation | Inclusive language |
| dummy | placeholder, sample | Inclusive language |

---

## Numbers and Measurements

| Rule | Example |
|------|---------|
| Spell out 1-9 | "three options available" |
| Use numerals for 10+ | "15 parameters supported" |
| Always use numerals with units | "5 MB", "3 seconds" |
| Use numerals for versions | "version 2.0" |
| Use numerals in technical context | "port 3000", "2 CPU cores" |

---

## Enforcement

These rules are enforced by:
1. `terminology` skill during writing
2. `doc-verifier` agent during verification
3. `style-guide` skill during review

Violations are flagged as:
- **Error**: Product names, acronyms
- **Warning**: Action verbs, hyphenation
- **Info**: Number formatting, UI terms
