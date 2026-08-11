/*
 * geocode-widget.js - Address autocomplete backed by the KCAA geocoding API
 * (Mapbox primary, Nominatim fallback). Pure place lookup - no database.
 *
 * Design rules (do not regress):
 *  - Searching only starts after the user PAUSES typing (debounce), so typing
 *    "jkia" never fires a search on "jk" or "jki".
 *  - Typing is NEVER blocked: no alerts, no focus stealing, no preventDefault
 *    except Enter-with-a-selection, and any status message disappears the
 *    moment the user types another character.
 *  - In-flight requests are aborted when a newer one starts.
 *  - Empty/error states only appear once the query has settled unchanged.
 *
 * Usage:
 *   initGeocodeSearch({
 *     input: document.getElementById('addressSearch'),
 *     latInputId: 'latitude',          // optional
 *     lonInputId: 'longitude',         // optional
 *     onSubmit: function(result) {},   // optional; result = {lat, lon, display_name, text}
 *   });
 *
 * Returns { close, refresh }.
 */
(function (global) {
  'use strict';

  var API_URL = '/obstacle-compliance/api/geocode/';
  var DEBOUNCE_MS = 400;
  var MIN_CHARS = 3;

  function initGeocodeSearch(options) {
    if (!options || !options.input) return;
    var input = options.input;

    var dropdown = document.createElement('div');
    dropdown.className = 'geocode-dropdown';
    dropdown.setAttribute('role', 'listbox');
    dropdown.style.display = 'none';
    input.parentNode.insertBefore(dropdown, input.nextSibling);

    var timer = null;
    var controller = null;
    var activeIndex = -1;
    var items = [];
    var settledQuery = null; // last query the current UI state reflects

    input.setAttribute('autocomplete', 'off');
    input.setAttribute('spellcheck', 'false');

    function close() {
      settledQuery = null;
      dropdown.style.display = 'none';
      dropdown.innerHTML = '';
      items = [];
      activeIndex = -1;
    }

    function select(result) {
      if (options.latInputId) {
        var latEl = document.getElementById(options.latInputId);
        if (latEl) latEl.value = Number(result.lat).toFixed(6);
      }
      if (options.lonInputId) {
        var lonEl = document.getElementById(options.lonInputId);
        if (lonEl) lonEl.value = Number(result.lon).toFixed(6);
      }
      if (typeof options.onSubmit === 'function') options.onSubmit(result);
      close();
    }

    function highlight(index) {
      if (index < 0 || index >= items.length) return;
      var prev = dropdown.querySelector('.geocode-item.active');
      if (prev) prev.classList.remove('active');
      activeIndex = index;
      items[index].classList.add('active');
      items[index].scrollIntoView({ block: 'nearest' });
    }

    function showStatus(className, html) {
      dropdown.innerHTML = '<div class="geocode-item ' + className + '">' + html + '</div>';
      dropdown.style.display = 'block';
      items = [];
      activeIndex = -1;
    }

    function buildResults(data) {
      items = [];
      dropdown.innerHTML = '';
      var results = data.results || [];
      results.forEach(function (result, i) {
        var item = document.createElement('div');
        item.className = 'geocode-item';
        item.setAttribute('role', 'option');
        var label = document.createElement('span');
        label.className = 'geocode-label';
        label.textContent = result.display_name || result.text || '';
        var type = document.createElement('small');
        type.className = 'geocode-type';
        type.textContent = result.type || '';
        item.appendChild(label);
        item.appendChild(type);
        item.addEventListener('mousedown', function (e) {
          e.preventDefault();
          select(result);
        });
        item.addEventListener('mouseenter', function () { highlight(i); });
        dropdown.appendChild(item);
        items.push(item);
      });
      dropdown.style.display = 'block';
      if (items.length) highlight(0);
    }

    function search() {
      var q = input.value.trim();
      if (q.length < MIN_CHARS) { close(); return; }
      settledQuery = q;
      if (controller) controller.abort();
      controller = new AbortController();
      showStatus('loading', '<span class="geocode-spinner"></span> Searching&hellip;');

      fetch(API_URL + '?address=' + encodeURIComponent(q), { signal: controller.signal })
        .then(function (r) { return r.json(); })
        .then(function (data) {
          // User kept typing while the request was in flight - discard.
          if (input.value.trim() !== settledQuery) return;
          if (!data.results || !data.results.length) {
            showStatus('empty', 'No matches found');
            return;
          }
          buildResults(data);
        })
        .catch(function (err) {
          if (err.name === 'AbortError') return;
          // Only surface the error if the query is still current.
          if (input.value.trim() === settledQuery) {
            showStatus('empty', 'Search unavailable - please try again');
          }
        });
    }

    input.addEventListener('input', function () {
      clearTimeout(timer);
      // Any pending status is immediately stale once the user types.
      settledQuery = null;
      if (input.value.trim().length < MIN_CHARS) {
        close();
        return;
      }
      timer = setTimeout(search, DEBOUNCE_MS);
    });

    input.addEventListener('keydown', function (e) {
      if (e.key === 'Escape') {
        close();
        return;
      }
      if (e.key === 'ArrowDown' || e.key === 'ArrowUp') {
        if (dropdown.style.display !== 'block' || !items.length) return;
        e.preventDefault();
        highlight(
          e.key === 'ArrowDown'
            ? Math.min(activeIndex + 1, items.length - 1)
            : Math.max(activeIndex - 1, 0)
        );
        return;
      }
      // Enter only intercepts when there is a real selection to make.
      if (e.key === 'Enter' && dropdown.style.display === 'block' && items.length) {
        var target = items[activeIndex >= 0 ? activeIndex : 0];
        if (target) {
          e.preventDefault();
          target.dispatchEvent(new MouseEvent('mousedown', { bubbles: true }));
        }
      }
    });

    input.addEventListener('blur', function () {
      setTimeout(close, 150);
    });

    document.addEventListener('click', function (e) {
      if (!dropdown.contains(e.target) && e.target !== input) close();
    });

    return { close: close, refresh: search };
  }

  global.initGeocodeSearch = initGeocodeSearch;
})(window);
