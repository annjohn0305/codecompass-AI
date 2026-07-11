document.addEventListener('DOMContentLoaded', () => {
  const form = document.getElementById('what-if-form');
  const input = document.getElementById('scenario_input');
  const scenarioType = document.getElementById('scenario_type');
  const statusEl = document.getElementById('what-if-status');
  const resultsEl = document.getElementById('what-if-results');

  if (!form || !input || !scenarioType || !statusEl || !resultsEl) return;

  const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]')?.value;
  const projectId = window.__PROJECT_ID__;

  function escapeHtml(str) {
    return String(str)
      .replaceAll('&', '&amp;')
      .replaceAll('<', '<')
      .replaceAll('>', '>')
      .replaceAll('"', '"')
      .replaceAll("'", '&#039;');
  }

  function render(payload) {
    resultsEl.innerHTML = '';
    const answers = payload?.answers || [];

    if (!answers.length) {
      resultsEl.innerHTML = '<p>No scenario branches returned.</p>';
      return;
    }

    answers.forEach((item, idx) => {
      const wrapper = document.createElement('div');
      wrapper.className = 'result-card';
      wrapper.style.marginBottom = '14px';

      const changes = Array.isArray(item.changes) ? item.changes : [];

      wrapper.innerHTML = `
        <h4 style="margin-top:0;">${escapeHtml(item.title || `Outcome ${idx + 1}`)}</h4>
        ${item.likelihood ? `<div style="font-weight:600;margin-bottom:6px;">Likelihood: ${escapeHtml(item.likelihood)}</div>` : ''}
        ${item.impact ? `<div style="margin-bottom:6px;"><strong>Impact:</strong> ${escapeHtml(item.impact)}</div>` : ''}
        ${changes.length ? `<ul>${changes.map(c => `<li>${escapeHtml(c)}</li>`).join('')}</ul>` : ''}
        ${item.reasoning ? `<p style="opacity:.95; margin-top:8px;">${escapeHtml(item.reasoning)}</p>` : ''}
      `;

      resultsEl.appendChild(wrapper);
    });
  }

  form.addEventListener('submit', async (e) => {
    e.preventDefault();

    const scenario_input = input.value.trim();
    const scenario_type = scenarioType.value;

    if (!scenario_input) return;
    if (!projectId) {
      statusEl.textContent = 'Missing project context.';
      return;
    }

    statusEl.textContent = 'Running simulation...';
    resultsEl.innerHTML = '';

    try {
      const res = await fetch(`/what-if-api/${projectId}/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': csrfToken || ''
        },
        body: JSON.stringify({ scenario_input, scenario_type })
      });

      if (!res.ok) {
        const t = await res.text();
        throw new Error(t || `Request failed: ${res.status}`);
      }

      const payload = await res.json();
      render(payload);
      statusEl.textContent = 'Done ✅';
    } catch (err) {
      console.error(err);
      statusEl.textContent = 'Simulation failed.';
      resultsEl.innerHTML = `<p style="color:#b00020;">${escapeHtml(err.message || err)}</p>`;
    }
  });
});

