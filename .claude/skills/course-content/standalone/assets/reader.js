/* Progressive teaching controls. Topic content stays in the authored HTML. */
(() => {
  document.querySelectorAll('[data-stepper], .walkthrough').forEach(walk => {
    const buttons = [...walk.querySelectorAll('[data-step]')];
    const panels = [...walk.querySelectorAll('.step-panel')];
    const controls = walk.querySelector('.step-controls');
    const footer = walk.querySelector('.step-footer');
    const previous = walk.querySelector('[data-walk="previous"]');
    const next = walk.querySelector('[data-walk="next"]');
    const status = walk.querySelector('.step-status');
    const targets = buttons.map(button => panels.find(panel => panel.id === button.getAttribute('aria-controls')));
    if (!panels.length || buttons.length !== panels.length || targets.some(panel => !panel) || new Set(targets).size !== panels.length || !controls || !footer || !previous || !next || !status) return;
    const requestedColumns = Number(controls.dataset.columns);
    const columns = Number.isInteger(requestedColumns) && requestedColumns >= 1 && requestedColumns <= 4
      ? requestedColumns : (buttons.length === 4 ? 2 : Math.min(3, buttons.length));
    controls.style.setProperty('--step-columns', String(columns));
    let current = 0;
    function show(index, announce = true) {
      current = Math.max(0, Math.min(buttons.length - 1, index));
      panels.forEach(panel => { panel.hidden = panel !== targets[current]; });
      buttons.forEach((button, i) => button.setAttribute('aria-pressed', String(i === current)));
      previous.disabled = current === 0;
      next.disabled = current === buttons.length - 1;
      status.textContent = 'Stage ' + (current + 1) + ' of ' + panels.length;
      if (announce && ((document.activeElement === previous && previous.disabled) || (document.activeElement === next && next.disabled))) buttons[current].focus({preventScroll: true});
    }
    buttons.forEach((button, i) => button.addEventListener('click', () => show(i)));
    previous.addEventListener('click', () => show(current - 1));
    next.addEventListener('click', () => show(current + 1));
    controls.hidden = false;
    footer.hidden = false;
    show(0, false);
  });
  document.querySelectorAll('[data-comparison], .evidence-switcher').forEach(compare => {
    const buttons = [...compare.querySelectorAll('[data-mode]')];
    const panels = [...compare.querySelectorAll('.mode-panel')];
    const controls = compare.querySelector('.mode-controls');
    const status = compare.querySelector('.switch-status');
    const targets = buttons.map(button => panels.find(panel => panel.id === button.getAttribute('aria-controls')));
    if (buttons.length < 2 || buttons.length !== panels.length || targets.some(panel => !panel) || new Set(targets).size !== panels.length || !controls || !status) return;
    function show(index) {
      panels.forEach(panel => { panel.hidden = panel !== targets[index]; });
      buttons.forEach((button, i) => button.setAttribute('aria-pressed', String(i === index)));
      status.textContent = targets[index].dataset.announcement || (buttons[index].textContent.trim() + ' selected.');
    }
    buttons.forEach((button, i) => button.addEventListener('click', () => show(i)));
    controls.hidden = false;
    show(0);
  });
})();
