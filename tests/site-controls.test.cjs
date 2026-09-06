// Isolated control regressions; actual browser QA is separate.
const fs = require('node:fs');
const vm = require('node:vm');
const crypto = require('node:crypto');
const assert = require('node:assert/strict');
const sourcePath = require('node:path').resolve(__dirname, '../docs/site-controls.js');
const source = fs.readFileSync(sourcePath, 'utf8');
class Element {
  constructor(attrs = {}) {
    this.attrs = attrs; this.listeners = {}; this.textContent = ''; this.disabled = false;
    const values = new Set();
    this.classList = {contains: x => values.has(x), remove: x => values.delete(x),
      toggle: x => { if(values.has(x)) { values.delete(x); return false; } values.add(x); return true; }};
  }
  addEventListener(type, fn) { this.listeners[type] = fn; }
  setAttribute(key, value) { this.attrs[key] = value; }
  getAttribute(key) { return this.attrs[key]; }
  focus() { this.focused = true; }
  scrollIntoView(opts) { this.scrolled = opts; }
}
function setup(clipboard) {
  const menu = new Element({'aria-expanded': 'false'}), links = new Element(), body = new Element();
  const feature = new Element(), status = new Element(), button = new Element();
  button.textContent = 'Copy';
  button.closest = selector => { assert.equal(selector, '.code-block'); return {
    querySelector: selector => {assert.equal(selector, 'code'); return {textContent: '  bash muse/scripts/install.sh --tool codex --target /my/project  '};}
  };};
  const anchors = ['#', '#features', '#missing'].map(href => new Element({href}));
  const timers = new Map(); let next = 1;
  const document = new Element(); document.body = body;
  document.querySelector = selector => ({'.nav-toggle': menu, '.nav-links': links})[selector];
  document.querySelectorAll = selector => selector === '.copy-btn' ? [button] : anchors;
  document.getElementById = id => ({features: feature, 'copy-status': status})[id];
  vm.runInNewContext(source, {document, navigator: {clipboard},
    setTimeout: fn => { const id = next++; timers.set(id,fn); return id; },
    clearTimeout: id => timers.delete(id)}, {filename: sourcePath});
  const event = () => ({preventDefault() {this.prevented = true;}});
  return {menu, links, body, feature, status, button, anchors, timers, document, event};
}
(async () => {
  const cases = [];
  async function test(name, fn) {await fn(); cases.push({name, verdict:'PASS'});}
  await test('Clipboard success waits for actual resolved write and resets label', async () => {
    let resolveWrite, captured;
    const x = setup({writeText: text => {captured = text; return new Promise(r => {resolveWrite = r;});}});
    const pending = x.button.listeners.click();
    assert.equal(x.button.disabled, true); assert.equal(x.button.textContent, 'Copying…');
    assert.equal(x.status.textContent, ''); assert.equal(captured, 'bash muse/scripts/install.sh --tool codex --target /my/project');
    resolveWrite(); await pending;
    assert.equal(x.button.disabled, false); assert.equal(x.button.textContent, 'Copied');
    assert.equal(x.status.textContent, 'Command copied to clipboard.');
    [...x.timers.values()][0](); assert.equal(x.button.textContent, 'Copy');
  });
  await test('Clipboard rejected permission announces manual fallback without false success', async () => {
    const x = setup({writeText: async () => {throw new Error('NotAllowedError');}});
    await x.button.listeners.click();
    assert.equal(x.button.disabled, false); assert.equal(x.button.textContent, 'Copy');
    assert.equal(x.status.textContent, 'Clipboard unavailable. Select and copy the command above.');
  });
  await test('Clipboard API absent announces fallback and re-enables control', async () => {
    const x = setup(undefined); await x.button.listeners.click();
    assert.equal(x.button.disabled, false); assert.equal(x.button.textContent, 'Copy');
    assert.match(x.status.textContent, /Clipboard unavailable/);
  });
  await test('Mobile menu toggles expanded state both directions', () => {
    const x = setup(); x.menu.listeners.click();
    assert.equal(x.links.classList.contains('open'), true); assert.equal(x.menu.attrs['aria-expanded'], 'true');
    x.menu.listeners.click(); assert.equal(x.links.classList.contains('open'), false); assert.equal(x.menu.attrs['aria-expanded'], 'false');
  });
  await test('Escape closes menu and returns focus to toggle', () => {
    const x = setup(); x.menu.listeners.click(); x.document.listeners.keydown({key: 'Escape'});
    assert.equal(x.links.classList.contains('open'), false); assert.equal(x.menu.attrs['aria-expanded'], 'false'); assert.equal(x.menu.focused, true);
  });
  await test('Home href # scrolls to body without an invalid selector exception', () => {
    const x = setup(); const e = x.event(); x.menu.listeners.click(); x.anchors[0].listeners.click(e);
    assert.equal(e.prevented, true); assert.equal(x.body.scrolled.behavior, 'smooth'); assert.equal(x.links.classList.contains('open'), false);
  });
  await test('Existing anchor scrolls its target and closes menu', () => {
    const x = setup(); const e = x.event(); x.menu.listeners.click(); x.anchors[1].listeners.click(e);
    assert.equal(e.prevented, true); assert.equal(x.feature.scrolled.behavior, 'smooth'); assert.equal(x.menu.attrs['aria-expanded'], 'false');
  });
  await test('Unknown anchor safely preserves native browser behavior', () => {
    const x = setup(); const e = x.event(); x.anchors[2].listeners.click(e);
    assert.equal(e.prevented, undefined);
  });
  console.log(JSON.stringify({verdict:'SCOPED_NON_UI_PASS', source_path:sourcePath,
    source_sha256:crypto.createHash('sha256').update(source).digest('hex'), tests:cases,
    limits:'VM DOM stubs only; not browser, clipboard permissions, keyboard focus traversal, screen-reader, visual or deployment evidence.'}, null, 2));
})().catch(error => {console.error(error); process.exitCode=1;});
