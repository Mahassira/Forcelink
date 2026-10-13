/* FORCE LINK GENERAL TRADING LLC — site behaviour (no dependencies) */
(function () {
  'use strict';

  var EMAIL = 'info@forcelink-ae.com';
  var doc = document;
  var html = doc.documentElement;
  var reduceMotion = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  html.classList.add('js');

  /* Footer year (dynamic) */
  var yearEls = doc.querySelectorAll('[data-year]');
  for (var y = 0; y < yearEls.length; y++) {
    yearEls[y].textContent = String(new Date().getFullYear());
  }

  /* Header elevation on scroll */
  var header = doc.querySelector('.site-header');
  function onScroll() {
    if (header) header.classList.toggle('is-scrolled', window.scrollY > 8);
  }
  window.addEventListener('scroll', onScroll, { passive: true });
  onScroll();

  /* Mobile navigation */
  var toggle = doc.querySelector('.menu-toggle');
  var panel = doc.getElementById('mobile-nav');
  if (toggle && panel) {
    var setOpen = function (open) {
      toggle.setAttribute('aria-expanded', String(open));
      panel.classList.toggle('is-open', open);
    };
    toggle.addEventListener('click', function () {
      setOpen(toggle.getAttribute('aria-expanded') !== 'true');
    });
    doc.addEventListener('keydown', function (e) {
      if (e.key === 'Escape' && panel.classList.contains('is-open')) {
        setOpen(false);
        toggle.focus();
      }
    });
    var wide = window.matchMedia('(min-width: 960px)');
    var onWide = function (e) { if (e.matches) setOpen(false); };
    if (wide.addEventListener) wide.addEventListener('change', onWide);
  }

  /* Reveal on scroll */
  var reveals = [].slice.call(doc.querySelectorAll('.reveal'));
  if ('IntersectionObserver' in window && !reduceMotion) {
    var revealIO = new IntersectionObserver(function (entries, obs) {
      entries.forEach(function (entry) {
        if (entry.isIntersecting) {
          entry.target.classList.add('is-in');
          obs.unobserve(entry.target);
        }
      });
    }, { threshold: 0.12 });
    reveals.forEach(function (el) { revealIO.observe(el); });
  } else {
    reveals.forEach(function (el) { el.classList.add('is-in'); });
  }

  /* Count-up metrics. Final values are already in the HTML, so the figures
     remain correct without JavaScript or when motion is reduced. */
  function countUp(el) {
    var target = parseFloat(el.getAttribute('data-count'));
    var decimals = parseInt(el.getAttribute('data-decimals') || '0', 10);
    var duration = 1100;
    var start = null;
    function step(ts) {
      if (start === null) start = ts;
      var p = Math.min((ts - start) / duration, 1);
      var eased = 1 - Math.pow(1 - p, 3);
      el.textContent = (target * eased).toFixed(decimals);
      if (p < 1) window.requestAnimationFrame(step);
      else el.textContent = target.toFixed(decimals);
    }
    el.textContent = (0).toFixed(decimals);
    window.requestAnimationFrame(step);
  }
  var counters = [].slice.call(doc.querySelectorAll('[data-count]'));
  if (counters.length && 'IntersectionObserver' in window && !reduceMotion) {
    var countIO = new IntersectionObserver(function (entries, obs) {
      entries.forEach(function (entry) {
        if (entry.isIntersecting) {
          countUp(entry.target);
          obs.unobserve(entry.target);
        }
      });
    }, { threshold: 0.6 });
    counters.forEach(function (el) { countIO.observe(el); });
  }

  /* Contact inquiry form.
     This is a static site: nothing is sent by the website. The form prepares
     the inquiry, copies it to the clipboard where possible, and opens the
     visitor's own email app addressed to the company. The visitor sends the
     email themselves. The UI never claims that a message has been delivered. */
  var form = doc.getElementById('inquiry-form');
  if (form) {
    var status = doc.getElementById('form-status');
    var summaryWrap = doc.getElementById('summary-wrap');
    var summary = doc.getElementById('inquiry-summary');
    var submitBtn = form.querySelector('button[type="submit"]');

    var productSelect = form.elements.product;
    var preset = new URLSearchParams(window.location.search).get('product');
    if (preset && productSelect) {
      for (var i = 0; i < productSelect.options.length; i++) {
        if (productSelect.options[i].value === preset) {
          productSelect.value = preset;
          break;
        }
      }
    }

    function fieldIsValid(input) {
      if (input.type === 'email') {
        return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(input.value.trim());
      }
      return input.value.trim() !== '';
    }

    function validate() {
      var firstInvalid = null;
      var required = form.querySelectorAll('[required]');
      for (var r = 0; r < required.length; r++) {
        var input = required[r];
        var valid = fieldIsValid(input);
        var wrap = input.closest('.field');
        wrap.classList.toggle('is-invalid', !valid);
        input.setAttribute('aria-invalid', String(!valid));
        if (!valid && !firstInvalid) firstInvalid = input;
      }
      return firstInvalid;
    }

    function setStatus(message, isError) {
      status.textContent = message;
      status.classList.toggle('is-error', !!isError);
      status.classList.add('is-visible');
    }

    form.addEventListener('submit', function (e) {
      e.preventDefault();
      var firstInvalid = validate();
      if (firstInvalid) {
        firstInvalid.focus();
        setStatus('Please correct the highlighted fields before continuing.', true);
        return;
      }

      var f = form.elements;
      var productText = productSelect.options[productSelect.selectedIndex].text;
      var marketText = f.market.value || 'Not specified';
      var lines = [
        'Business inquiry — FORCE LINK GENERAL TRADING LLC website',
        '',
        'Full name: ' + f.fullName.value.trim(),
        'Company name: ' + f.company.value.trim(),
        'Business email: ' + f.email.value.trim(),
        'Telephone: ' + (f.phone.value.trim() || 'Not provided'),
        'Product of interest: ' + productText,
        'Destination market: ' + marketText,
        'Estimated quantity / requirements: ' + (f.quantity.value.trim() || 'Not provided'),
        '',
        'Message:',
        f.message.value.trim()
      ];
      var text = lines.join('\n');
      var subject = 'Business inquiry: ' + productText;

      if (submitBtn) submitBtn.disabled = true;

      var openMailApp = function () {
        window.location.href = 'mailto:' + EMAIL + '?subject=' + encodeURIComponent(subject);
      };

      var finish = function (copied) {
        if (copied) {
          setStatus('Your inquiry details have been copied to your clipboard and your email app is opening with the subject line filled in. Paste the details into the email, review it, and send it. Nothing has been sent from this website yet.');
          if (summaryWrap) summaryWrap.hidden = true;
        } else {
          summary.value = text;
          if (summaryWrap) summaryWrap.hidden = false;
          setStatus('Your email app is opening with the subject line filled in. We could not copy the details automatically, so please copy them from the box below into your email, then send it. Nothing has been sent from this website yet. If no email app opens, write to ' + EMAIL + ' directly.');
        }
        openMailApp();
        window.setTimeout(function () { if (submitBtn) submitBtn.disabled = false; }, 4000);
      };

      summary.value = text;
      if (navigator.clipboard && navigator.clipboard.writeText) {
        navigator.clipboard.writeText(text).then(function () { finish(true); }, function () { finish(false); });
      } else {
        finish(false);
      }
    });

    /* Clear field errors while the visitor corrects them */
    form.addEventListener('input', function (e) {
      var input = e.target;
      if (!input.closest) return;
      var wrap = input.closest('.field');
      if (wrap && wrap.classList.contains('is-invalid') && fieldIsValid(input)) {
        wrap.classList.remove('is-invalid');
        input.setAttribute('aria-invalid', 'false');
      }
    });
  }

})();
