/*
 * geocode-widget.js - Address autocomplete backed by the KCAA geocoding API
 * (Mapbox primary, Nominatim fallback). Shared by property check, quick check
 * and property add/edit forms. Vanilla JS, no dependencies.
 *
 * Usage:
 *   initGeocodeSearch({
 *     input: document.getElementById('addressSearch'),
 *     latInputId: 'latitude',          // optional: id of a lat <input>
 *     lonInputId: 'longitude',         // optional: id of a lon <input>
 *     onSubmit: function(result) {},   // optional; result = {lat, lon, display_name, type}
 *   });
 */
(function (global) {
  'use strict';

  var API_URL = '/obstacle-compliance/api/geocode/';
  var DEBOUNCE_MS = 400;

  function initGeocodeSearch(options) {
    if (!options || !options.input) return;
    var input = options.input;

    var dropdown = document.createElement('div');
    dropdown.className = 'geocode-dropdown';
    dropdown.style.display = 'none';
    input.parentNode.insertBefore(dropdown, input.nextSibling);

    var timer = null;
    var controller = null;

    input.setAttribute('autocomplete', 'off');

    function close() {
      dropdown.style.display = 'none';
      dropdown.innerHTML = '';
    }

    function search() {
      var q = input.value.trim();
      if (q.length < 3) { close(); return; }
      if (controller) controller.abort();
      controller = new AbortController();

      fetch(API_URL + '?address=' + encodeURIComponent(q), { signal: controller.signal })
        .then(function (r) { return r.json(); })
        .then(function (data) {
          if (!data.results || !data.results.length) {
            dropdown.innerHTML = '<div class="geocode-item geocode-empty">No matches found</div>';
            dropdown.style.display = 'block';
            return;
          }
          dropdown.innerHTML = '';
          data.results.forEach(function (result) {
            var item = document.createElement('div');
            item.className = 'geocode-item';
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
            dropdown.appendChild(item);
          });
          dropdown.style.display = 'block';
        })
        .catch(function (err) {
          if (err.name !== 'AbortError') close();
        });
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

    input.addEventListener('input', function () {
      clearTimeout(timer);
      timer = setTimeout(search, DEBOUNCE_MS);
    });
    input.addEventListener('keydown', function (e) {
      if (e.key === 'Escape') close();
      if (e.key === 'Enter' && dropdown.style.display === 'block') {
        e.preventDefault();
        var first = dropdown.querySelector('.geocode-item');
        if (first) first.dispatchEvent(new MouseEvent('mousedown', { bubbles: true }));
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