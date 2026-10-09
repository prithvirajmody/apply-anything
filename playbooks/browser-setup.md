# Browser setup

Read this once per session, before you open the first form. Every platform playbook assumes it.

## Launch a dedicated automation Chrome

Use a Chrome profile that exists only for applications, with remote debugging on port 9222:

```bash
google-chrome --remote-debugging-port=9222 --user-data-dir="$HOME/.cache/apply-anything-chrome"
```

- macOS: `"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"` with the same two flags.
- Write the path with `$HOME`, not `~`. The shell doesn't expand `~` in the middle of an argument like `--user-data-dir=~/...`, so Chrome would receive a literal `~`.
- A separate `--user-data-dir` is required anyway: Chrome 136 and later ignore `--remote-debugging-port` on the default profile.
- Check that it's up: `curl -s http://127.0.0.1:9222/json/version`.
- The user may close this window between sessions. If the port doesn't answer, relaunch with the same command. The profile keeps its portal sessions between launches.

**Keep the profile clean.** The automation profile holds application-portal sessions and nothing else. Tell the user not to sign it into everyday accounts it doesn't need: Google, LinkedIn, their mailbox, password-manager sync. As a result, "Sign in with Google/LinkedIn" buttons won't work in it; use the email sign-in path. Read emailed codes and links through the session's mail tool, not by opening the mailbox in this profile.

## Work in background tabs, not new windows

A window per application eats RAM, and stealing focus disrupts the user. Open each form as a background tab in the existing window:

```text
Target.createTarget(url=URL, background=True)      # no newWindow
Target.attachToTarget(targetId=ID, flatten=True)   # attach without showing it; returns the sessionId for page commands
Emulation.setFocusEmulationEnabled(enabled=True)   # the page behaves as if focused
```

- The user's visible tab doesn't change, and most forms fill fine this way.
- If a background tab stalls (an upload spins, a list never renders, a click does nothing), call `Target.activateTarget(targetId=ID)` and retry. That brings the tab to the front, so tell the user first if they are working in that window.
- Activate the tab before uploads on platforms known to freeze (see `phenom.md`).
- One tab per application. Close it with `Target.closeTarget` after the user submits, and never before: a closed tab can lose an unsaved draft, and some submits wait on a code the user types in.

## Input that works

**Wrap every snippet** you pass to `Runtime.evaluate` in an arrow function that calls itself. Snippets run in the page's global scope, so a second `const el` fails with "Identifier 'el' has already been declared".

```js
(() => { const el = document.querySelector('#first_name'); return el ? el.value : null; })()
```

Pass `returnByValue: true` and return plain data (strings, numbers, small objects).

**Scroll before you click.** Some pages use smooth scrolling, so an element keeps moving after you read its position. Call `el.scrollIntoView({behavior: 'instant', block: 'center'})`, then read `getBoundingClientRect()` again.

**Typing.** Click-then-type sometimes misses. This works on React forms and on Workday:

1. `Runtime.evaluate`: `(() => { const el = document.querySelector(SEL); el.focus(); el.select(); })()`
2. `Input.insertText(text=VALUE)`
3. Read `el.value` back to confirm.

For an autocomplete that only suggests results as keys arrive, send one `Input.insertText` per character (or `Input.dispatchKeyEvent` key events), then wait for the options.

**Clicking.** Try `el.click()` first. When the page ignores it (account-creation buttons, menu options, some checkboxes), send a real mouse click at the element's center:

```text
Input.dispatchMouseEvent(type='mousePressed',  x=X, y=Y, button='left', clickCount=1)
Input.dispatchMouseEvent(type='mouseReleased', x=X, y=Y, button='left', clickCount=1)
```

`X` and `Y` come from `getBoundingClientRect()` (`left + width/2`, `top + height/2`), in CSS pixels relative to the top-level viewport. For an element inside an iframe, add the iframe's own rect offset.

**Native selects on React pages.** Changing `selectedIndex` gets reverted. Use the native value setter, then fire `change`:

```js
(() => {
  const s = document.querySelector(SEL);
  Object.getOwnPropertyDescriptor(HTMLSelectElement.prototype, 'value').set.call(s, VALUE);
  s.dispatchEvent(new Event('change', {bubbles: true}));
  return s.value;
})()
```

**Lists that appear late.** Options can take 2–3 seconds after the click or keystroke, longer for server lookups. Poll for them. Don't conclude "no options" from a single read.

## File uploads

Set files with `DOM.setFileInputFiles` and absolute paths. Never try to drive the operating system's file dialog.

- **An `input[type=file]`, visible or hidden:** find it (`DOM.getDocument` + `DOM.querySelector`, or `Runtime.evaluate` returning the element without `returnByValue`), then `DOM.setFileInputFiles(files=[PATH], nodeId=N)`. It also accepts `backendNodeId` or `objectId`.
- **An input inside shadow DOM:** `DOM.querySelector` can't reach it. Evaluate a snippet that walks the `shadowRoot`s and returns the element. Take the result's `objectId`, run `DOM.describeNode(objectId=...)` for its `backendNodeId`, then `DOM.setFileInputFiles(backendNodeId=..., files=[PATH])`.
- **A button that opens a file chooser, with no input you can find:** call `Page.setInterceptFileChooserDialog(enabled=True)`, click the button, and wait for the `Page.fileChooserOpened` event. It carries the input's `backendNodeId`; pass that to `DOM.setFileInputFiles`. Turn interception off afterwards.
- After an upload, wait for any resume parser to finish, then re-check every field it may have touched.

## Check your work

- **Late hydration.** Some pages finish loading after you start and wipe typed values or uploads. Before you hand off, re-read every field: names, contact details, every required field, and the attached file names.
- **Parsers.** A resume upload can overwrite fields you typed earlier and fill others wrongly (location, phone country code, junk skills). Upload first, then type, then re-check. [`../docs/knockout-questions.md`](../docs/knockout-questions.md) explains why location and phone matter.
- **Length limits.** Read `maxLength`, and any "N characters" hint, before you write an answer.
- **Screenshots time out** on background tabs, especially while the user works in another tab of the same window. Read the DOM instead:

```js
(() => [...document.querySelectorAll('input, select, textarea')]
  .filter(e => e.type !== 'hidden')
  .map(e => ({
    id: e.id, name: e.name, type: e.type, required: e.required,
    value: (e.type === 'checkbox' || e.type === 'radio') ? e.checked : e.value,
    label: ((e.labels && e.labels[0] && e.labels[0].innerText) || e.getAttribute('aria-label') || '').slice(0, 80),
  })))()
```

- **Did it go through?** Look for the confirmation page, the confirmation email, or the portal's candidate dashboard. Don't read the browser's history database.

## Raw-CDP fallback

If your browser tool (for example a browser MCP server) can't connect, drive the same Chrome directly with Python `websockets` (`pip install websockets`).

- Open a tab. Current Chrome requires `PUT`: `curl -s -X PUT "http://127.0.0.1:9222/json/new?https://example.com/apply"`. The reply holds the tab's `id` and `webSocketDebuggerUrl`.
- List tabs: `curl -s http://127.0.0.1:9222/json/list`.
- Send `Runtime.evaluate`, `Input.insertText` and `Input.dispatchMouseEvent` over the tab's websocket.
- Pass JavaScript on stdin, never inside a quoted shell string, so quotes and backticks survive.

Save this as `cdp.py` in your scratch directory, not in the repo:

```python
"""Minimal CDP client for the automation Chrome. Usage:
    python3 cdp.py WS_URL Runtime.evaluate < snippet.js
    python3 cdp.py WS_URL Input.insertText '{"text": "hello"}'
"""
import asyncio, json, sys
import websockets

async def call(ws_url, method, params):
    async with websockets.connect(ws_url, max_size=None) as ws:
        await ws.send(json.dumps({"id": 1, "method": method, "params": params}))
        while True:
            msg = json.loads(await ws.recv())
            if msg.get("id") == 1:
                return msg

ws_url, method = sys.argv[1], sys.argv[2]
if method == "Runtime.evaluate" and len(sys.argv) == 3:
    params = {"expression": sys.stdin.read(), "returnByValue": True, "awaitPromise": True}
else:
    params = json.loads(sys.argv[3]) if len(sys.argv) > 3 else {}
print(json.dumps(asyncio.run(call(ws_url, method, params)), indent=1))
```

```bash
python3 cdp.py "$WS_URL" Runtime.evaluate <<'JS'
(() => document.title)()
JS
```

## Share the browser carefully

- One agent drives the automation Chrome at a time. While forms are open, research subagents must use `curl` or a fetch tool, never the shared browser: a subagent that opens tabs can move the attached tab in the middle of a form. Stop running research agents before you start filling.
- Don't touch tabs you didn't open. The user may be working in the same window.
- Close each application's tab once the user has submitted it.

## Accounts and passwords

- Portal accounts (Workday tenants, Avature, iCIMS, amazon.jobs, event sites) belong to the user. Either the user creates the account, or their password manager generates and fills the password.
- Never store a password in the repo, in `profile/`, in notes, in scripts or in any plain file. Don't generate passwords in shell commands. If a permission check blocks a credential step, that is the intended outcome: hand the step to the user.
- Fill the rest of a sign-up page (name, email) and stop at the password field.
- Emailed codes and links (security codes, sign-in codes, activation and reset links): find the email and show the code or link to the user. The user enters codes; open a link only when the user asks you to.
- When a session expires mid-form, a password reset by email is usually the way back in. The user sets the new password.
