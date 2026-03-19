# Documentation Style Rules

These rules are ALWAYS enforced when creating or editing documentation. They ensure consistency across all documentation and match professional technical writing standards.

---

## Voice and Tone

### REQUIRED: Active Voice
Write in active voice. The subject performs the action.

```
✅ CORRECT: "The function returns a promise."
❌ WRONG:   "A promise is returned by the function."

✅ CORRECT: "Configure the database connection."
❌ WRONG:   "The database connection should be configured."
```

### REQUIRED: Second Person
Address the reader as "you" in instructions and how-to content.

```
✅ CORRECT: "You can configure the timeout..."
❌ WRONG:   "Users can configure the timeout..."
❌ WRONG:   "One can configure the timeout..."
```

### REQUIRED: Present Tense
Use present tense for describing behavior and features.

```
✅ CORRECT: "The API returns JSON data."
❌ WRONG:   "The API will return JSON data."

✅ CORRECT: "This method throws an error if..."
❌ WRONG:   "This method would throw an error if..."
```

### REQUIRED: Verb-First for Procedures
Start procedural steps with action verbs.

```
✅ CORRECT: "Install the package using npm."
❌ WRONG:   "The package can be installed using npm."

✅ CORRECT: "Create a new configuration file."
❌ WRONG:   "A new configuration file needs to be created."
```

---

## Banned Phrases

NEVER use these phrases in documentation:

| Banned Phrase | Why | Use Instead |
|---------------|-----|-------------|
| "Simply" | Implies task is easy (it may not be) | Just remove it |
| "Just" | Minimizes complexity | Just remove it |
| "Easy" / "Easily" | Subjective, potentially condescending | Remove or be specific |
| "Obviously" | If obvious, why document it? | Remove |
| "Basically" | Filler word | Remove |
| "Please note that" | Verbose | Use "Note:" callout |
| "In order to" | Verbose | Use "To" |
| "It should be noted" | Passive, verbose | State directly |
| "As mentioned above/below" | Fragile reference | Link directly |
| "etc." | Vague | List all items or use "such as" |
| "And so on" | Vague | Be specific |
| "A number of" | Vague | Use specific number or "several" |
| "In this document we will" | Unnecessary meta | Start with content |
| "This section describes" | Unnecessary meta | Start with content |
| "Click here" | Bad accessibility | Use descriptive link text |

---

## Formatting Standards

### Headings

**Sentence case**: Capitalize only the first word and proper nouns.

```
✅ CORRECT: "Getting started with authentication"
❌ WRONG:   "Getting Started With Authentication"
```

**Hierarchy**: Never skip heading levels.

```
✅ CORRECT:
# Main Title (H1 - one per document)
## Major Section (H2)
### Subsection (H3)

❌ WRONG:
# Main Title
### Skipped H2!
```

### Code Formatting

**Inline code**: Use backticks for:
- File names: `config.yaml`
- Function names: `authenticate()`
- Variable names: `userId`
- Command names: `npm install`
- Parameter names: `timeout`

**Code blocks**: Always specify language.

```typescript
// ✅ CORRECT: Language specified
const config = { timeout: 5000 };
```

### Lists

**Numbered lists**: For sequential steps that must be followed in order.

```
1. Install dependencies.
2. Configure the database.
3. Start the server.
```

**Bullet lists**: For non-sequential items.

```
- Node.js 18 or higher
- PostgreSQL 14 or higher
- 2GB RAM minimum
```

**Parallel structure**: All items should follow the same grammatical pattern.

```
✅ CORRECT:
- Installing the CLI
- Configuring your project
- Running your first command

❌ WRONG:
- Installing the CLI
- Project configuration
- How to run your first command
```

### Tables

Use tables for:
- Parameter/option documentation
- Comparison of features
- Reference data with multiple attributes

```markdown
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `timeout` | number | No | Connection timeout in ms |
| `retries` | number | No | Number of retry attempts |
```

---

## Document Structure

### Required Sections by Type

**Tutorial**:
1. Introduction (what you'll learn)
2. Prerequisites
3. Steps (numbered, with verification points)
4. Summary / Next steps

**How-to Guide**:
1. Goal statement
2. Prerequisites
3. Steps (numbered)
4. Verification
5. Troubleshooting (optional)

**Reference**:
1. Overview/Description
2. Syntax
3. Parameters
4. Return value
5. Examples
6. Related links

**Explanation**:
1. Context/Introduction
2. Core concept
3. How it works
4. Implications/Trade-offs
5. Related topics

---

## Language and Terminology

### American English
Use American English spelling.

```
✅ CORRECT: color, authorize, center, analyze
❌ WRONG:   colour, authorise, centre, analyse
```

### Consistent Terminology
Use the same term for the same concept throughout.

```
✅ CORRECT: Always use "API key"
❌ WRONG:   "API key" in one place, "api-key" in another, "API Key" elsewhere
```

### Product Names
Capitalize product names exactly as branded.

```
✅ CORRECT: JavaScript, TypeScript, Node.js, PostgreSQL
❌ WRONG:   Javascript, typescript, NodeJS, Postgres
```

---

## Code Examples

### REQUIRED: Every code example must be:

1. **Complete**: Can be copied and run (or clearly marked as partial)
2. **Correct**: Actually works as described
3. **Relevant**: Directly illustrates the point
4. **Minimal**: No unnecessary complexity

### Example Structure

```typescript
// Brief comment explaining what this does
import { something } from 'package';

// Setup (if needed)
const config = { ... };

// The actual example
const result = doThing(config);

// Expected output (as comment)
// => { success: true, data: [...] }
```

---

## Callouts and Warnings

Use these callout types consistently:

```markdown
> **Note**: Supplementary information that's helpful but not critical.

> **Tip**: Helpful suggestion or best practice.

> **Important**: Information the reader must know to succeed.

> **Warning**: Potential for data loss, security issues, or breaking changes.

> **Caution**: Action that cannot be undone.
```

---

## Links

### Descriptive Link Text
Link text should describe the destination.

```
✅ CORRECT: See the [authentication guide](/docs/auth) for details.
❌ WRONG:   For details, [click here](/docs/auth).
```

### Relative Links for Internal Content
Use relative paths for internal documentation links.

```
✅ CORRECT: [Configuration options](./configuration.md)
❌ WRONG:   [Configuration options](https://docs.example.com/configuration)
```

---

## Enforcement

These rules are checked by:
1. `style-guide` skill during drafting
2. `doc-verifier` agent during verification
3. `review-docs` command during review

Violations are flagged with severity:
- **High**: Banned phrases, wrong voice
- **Medium**: Formatting inconsistencies
- **Low**: Minor style preferences
