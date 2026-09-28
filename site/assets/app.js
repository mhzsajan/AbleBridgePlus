/* AbleBridgePlus — landing page behaviour.
   Progressive enhancement only: every section is readable with JS disabled. */
(function () {
  'use strict';

  var reduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  /* ---------------------------------------------------------------------
     Sticky nav border
     --------------------------------------------------------------------- */
  var nav = document.getElementById('nav');
  var onScroll = function () {
    if (nav) nav.classList.toggle('is-stuck', window.scrollY > 8);
  };
  window.addEventListener('scroll', onScroll, { passive: true });
  onScroll();

  /* ---------------------------------------------------------------------
     Mobile menu
     --------------------------------------------------------------------- */
  var toggle = document.getElementById('navToggle');
  var links = document.getElementById('navLinks');
  if (toggle && links) {
    toggle.addEventListener('click', function () {
      var open = links.classList.toggle('is-open');
      toggle.setAttribute('aria-expanded', open ? 'true' : 'false');
    });
    // close after choosing a destination
    links.addEventListener('click', function (e) {
      if (e.target.tagName === 'A') {
        links.classList.remove('is-open');
        toggle.setAttribute('aria-expanded', 'false');
      }
    });
    // and on Escape, per normal menu expectations
    document.addEventListener('keydown', function (e) {
      if (e.key === 'Escape' && links.classList.contains('is-open')) {
        links.classList.remove('is-open');
        toggle.setAttribute('aria-expanded', 'false');
        toggle.focus();
      }
    });
  }

  /* ---------------------------------------------------------------------
     Staged terminal reveal
     --------------------------------------------------------------------- */
  var term = document.getElementById('terminalBody');
  if (term) {
    if (reduced) {
      term.classList.add('is-live');
    } else if ('IntersectionObserver' in window) {
      var seen = new IntersectionObserver(function (entries) {
        entries.forEach(function (e) {
          if (e.isIntersecting) {
            term.classList.add('is-live');
            seen.disconnect();
          }
        });
      }, { threshold: 0.3 });
      seen.observe(term);
    } else {
      term.classList.add('is-live');
    }
  }

  /* ---------------------------------------------------------------------
     Tool-area grid, generated from one list so the HTML stays readable
     --------------------------------------------------------------------- */
  var AREAS = [
    [61, 'Session &amp; transport'],
    [56, 'Clips'],
    [40, 'M4L bridge'],
    [32, 'Presets &amp; templates'],
    [29, 'Tracks'],
    [24, 'Setlist &amp; clock'],
    [19, 'Creative &amp; grid'],
    [19, 'Snapshots'],
    [17, 'Arrangement'],
    [17, 'Show control'],
    [16, 'Video &amp; lighting'],
    [16, 'Analytics'],
    [12, 'Browser'],
    [11, 'MIDI']
  ];
  var areas = document.getElementById('areas');
  if (areas) {
    var html = '';
    for (var i = 0; i < AREAS.length; i++) {
      html += '<div class="area"><b>' + AREAS[i][0] +
              '</b><span>' + AREAS[i][1] + '</span></div>';
    }
    areas.innerHTML = html;
  }

  /* ---------------------------------------------------------------------
     Client-config tabs
     --------------------------------------------------------------------- */
  document.querySelectorAll('[data-tabs]').forEach(function (group) {
    var tabs = group.querySelectorAll('.tab');
    var panels = group.querySelectorAll('.tabpanel');
    if (!tabs.length) return;

    var select = function (tab) {
      tabs.forEach(function (t) {
        var on = t === tab;
        t.classList.toggle('is-active', on);
        t.setAttribute('aria-selected', on ? 'true' : 'false');
      });
      panels.forEach(function (p) {
        var on = p.id === tab.getAttribute('aria-controls');
        p.classList.toggle('is-active', on);
        p.hidden = !on;
      });
    };

    tabs.forEach(function (tab, i) {
      tab.addEventListener('click', function () { select(tab); });
      // left/right arrows, as expected for a tablist
      tab.addEventListener('keydown', function (e) {
        if (e.key !== 'ArrowRight' && e.key !== 'ArrowLeft') return;
        e.preventDefault();
        var next = tabs[(i + (e.key === 'ArrowRight' ? 1 : tabs.length - 1)) % tabs.length];
        next.focus();
        select(next);
      });
    });
  });

  /* ---------------------------------------------------------------------
     Copy buttons
     --------------------------------------------------------------------- */
  document.querySelectorAll('[data-copy]').forEach(function (btn) {
    btn.addEventListener('click', function () {
      var box = btn.closest('.copy');
      var code = box && box.querySelector('pre code');
      if (!code) return;

      var done = function () {
        var prev = btn.textContent;
        btn.textContent = 'Copied';
        btn.classList.add('is-done');
        setTimeout(function () {
          btn.textContent = prev;
          btn.classList.remove('is-done');
        }, 1600);
      };

      // navigator.clipboard needs a secure context; fall back for file://
      if (navigator.clipboard && window.isSecureContext) {
        navigator.clipboard.writeText(code.textContent).then(done, fallback);
      } else {
        fallback();
      }

      function fallback() {
        var ta = document.createElement('textarea');
        ta.value = code.textContent;
        ta.setAttribute('readonly', '');
        ta.style.cssText = 'position:fixed;top:0;left:-9999px';
        document.body.appendChild(ta);
        ta.select();
        try { document.execCommand('copy'); done(); } catch (err) { /* nothing else to try */ }
        document.body.removeChild(ta);
      }
    });
  });

  /* ---------------------------------------------------------------------
     Year stamp
     --------------------------------------------------------------------- */
  var yr = document.querySelector('[data-year]');
  if (yr) yr.textContent = new Date().getFullYear();
})();
