// Tables remain complete and readable with JavaScript disabled.
document.querySelectorAll('[data-filter]').forEach((input) => {
  const table = document.getElementById(input.dataset.filter);
  const rows = Array.from(table.tBodies[0].rows);
  const output = document.getElementById(input.dataset.filter + '-count');
  const empty = document.getElementById(input.dataset.filter + '-empty');
  input.addEventListener('input', () => {
    const terms = input.value.toLocaleLowerCase().trim().split(/\s+/).filter(Boolean);
    let visible = 0;
    rows.forEach((row) => {
      const text = row.textContent.toLocaleLowerCase();
      row.hidden = !terms.every((term) => text.includes(term));
      if (!row.hidden) visible += 1;
    });
    output.textContent = `${visible} of ${rows.length} entries`;
    empty.hidden = visible !== 0;
  });
});
