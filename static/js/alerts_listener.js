/**
 * AeroCast AI — Real-Time Global Thunderstorm Alert Broadcast Listener
 * ===================================================================
 * Ensures that whenever a severe thunderstorm is detected anywhere in Karnataka
 * (by any user, observer, or sensor check), ALL connected users across all devices
 * immediately receive the real-time emergency broadcast notification toast and alert.
 */

(function () {
  let activeAlertId = null;
  let activeAlertLoc = 'Puttur';
  let lastShownAlertSig = null;
  let audioCtx = null;

  // Locality aliases and stopwords for localized alert targeting
  const ALIASES = {
    'bajipe': 'bajpe',
    'mangaluru': 'mangalore', 'mangalore': 'mangalore',
    'bengaluru': 'bangalore', 'bangalore': 'bangalore',
    'hubballi': 'hubli', 'hubli': 'hubli',
    'mysuru': 'mysore', 'mysore': 'mysore',
    'belagavi': 'belgaum', 'belgaum': 'belgaum',
    'kalaburagi': 'gulbarga', 'gulbarga': 'gulbarga',
    'shivamogga': 'shimoga', 'shimoga': 'shimoga',
    'vijayapura': 'bijapur', 'bijapur': 'bijapur',
    'ballari': 'bellary', 'bellary': 'bellary'
  };

  const STOPWORDS = new Set([
    'urban', 'rural', 'north', 'south', 'east', 'west', 'city', 'district', 'dist',
    'taluk', 'dk', 'karnataka', 'india', 'state', 'dakshina', 'kannada', 'uttara'
  ]);

  function extractPrimaryTown(str) {
    if (!str) return '';
    const parts = str.split(',').map(s => s.trim()).filter(Boolean);
    if (!parts.length) return '';
    const cleaned = parts[0].toLowerCase().replace(/[^a-z0-9\s]/g, ' ').trim();
    const words = cleaned.split(/\s+/).filter(w => !STOPWORDS.has(w));
    if (words.length > 0) {
      return words.map(w => ALIASES[w] || w).join(' ');
    }
    return ALIASES[cleaned] || cleaned;
  }

  function isLocationMatch(userLoc, alertLoc) {
    if (!userLoc || !alertLoc) return false;
    const alertClean = alertLoc.trim().toLowerCase();
    if (alertClean === 'karnataka' || alertClean === 'statewide' || alertClean === 'all') {
      return true;
    }
    const uTown = extractPrimaryTown(userLoc);
    const aTown = extractPrimaryTown(alertLoc);
    if (!uTown || !aTown) return false;
    return uTown === aTown || uTown.includes(aTown) || aTown.includes(uTown);
  }

  /**
   * Generates a soft, dual-tone emergency meteorological broadcast chime
   */
  function playAlertChime() {
    try {
      const AudioContext = window.AudioContext || window.webkitAudioContext;
      if (!AudioContext) return;
      if (!audioCtx) audioCtx = new AudioContext();

      if (audioCtx.state === 'suspended') {
        audioCtx.resume();
      }

      const now = audioCtx.currentTime;
      const osc1 = audioCtx.createOscillator();
      const osc2 = audioCtx.createOscillator();
      const gain = audioCtx.createGain();

      osc1.type = 'sine';
      osc1.frequency.setValueAtTime(587.33, now); // D5
      osc1.frequency.exponentialRampToValueAtTime(880.0, now + 0.18); // A5

      osc2.type = 'triangle';
      osc2.frequency.setValueAtTime(880.0, now);
      osc2.frequency.exponentialRampToValueAtTime(1174.66, now + 0.25); // D6

      gain.gain.setValueAtTime(0.01, now);
      gain.gain.linearRampToValueAtTime(0.18, now + 0.05);
      gain.gain.exponentialRampToValueAtTime(0.001, now + 0.45);

      osc1.connect(gain);
      osc2.connect(gain);
      gain.connect(audioCtx.destination);

      osc1.start(now);
      osc2.start(now);
      osc1.stop(now + 0.46);
      osc2.stop(now + 0.46);
    } catch (e) {
      // Audio playback restrictions fallback
    }
  }

  /**
   * Ensures the floating thunderstorm toast notification DOM element exists on current page
   */
  function ensureToastDOM() {
    let toast = document.getElementById('stormToastNotification');
    if (!toast) {
      toast = document.createElement('div');
      toast.id = 'stormToastNotification';
      toast.className = 'storm-toast-notification';
      toast.style.display = 'none';

      toast.innerHTML = `
        <div class="toast-header">
          <span class="toast-icon">⚡🚨</span>
          <span class="toast-title">CRITICAL THUNDERSTORM ALERT</span>
          <button type="button" class="toast-close" onclick="closeStormToast()" title="Dismiss">&times;</button>
        </div>
        <div class="toast-body">
          <p id="toastMessage" class="toast-msg">High thunderstorm risk detected. Avoid exposed outdoor areas and monitor official weather warnings.</p>
          <div class="toast-meta">
            <span id="toastRisk">88.5% Critical Risk</span> &bull; <span id="toastLoc">Puttur</span> &bull; <span id="toastTime">+30m Projection</span>
          </div>
          <div class="toast-action-row" style="margin-top: 10px; display: flex; gap: 8px; align-items: center; flex-wrap: wrap;">
            <button type="button" id="btnToastViewRadar" class="toast-action-btn" onclick="handleToastViewRadar()" style="background: var(--accent-terracotta); color: #fff; border: none; padding: 6px 14px; border-radius: 8px; font-size: 0.78rem; font-weight: 700; cursor: pointer; display: inline-flex; align-items: center; gap: 5px;">
              ⚡ View Live Storm Radar
            </button>
            <span id="toastBroadcastBadge" style="font-size: 0.72rem; color: #2e7d32; font-weight: 700;">📍 Local Alert for Your Area</span>
          </div>
        </div>
      `;
      document.body.appendChild(toast);
    } else {
      // If toast exists but lacks action row, inject it
      let bodyWrap = toast.querySelector('.toast-body');
      if (bodyWrap && !toast.querySelector('#btnToastViewRadar')) {
        const actionRow = document.createElement('div');
        actionRow.className = 'toast-action-row';
        actionRow.style.cssText = 'margin-top: 10px; display: flex; gap: 8px; align-items: center; flex-wrap: wrap;';
        actionRow.innerHTML = `
          <button type="button" id="btnToastViewRadar" class="toast-action-btn" onclick="handleToastViewRadar()" style="background: var(--accent-terracotta); color: #fff; border: none; padding: 6px 14px; border-radius: 8px; font-size: 0.78rem; font-weight: 700; cursor: pointer; display: inline-flex; align-items: center; gap: 5px;">
            ⚡ View Live Storm Radar
          </button>
          <span id="toastBroadcastBadge" style="font-size: 0.72rem; color: #2e7d32; font-weight: 700;">📍 Local Alert for Your Area</span>
        `;
        bodyWrap.appendChild(actionRow);
      }
    }
    return toast;
  }

  /**
   * Action handler when user clicks "View Live Storm Radar" on toast
   */
  window.handleToastViewRadar = function () {
    const loc = activeAlertLoc || 'Puttur';
    // If currently on dashboard with live radar
    if (typeof window.searchLocationDirect === 'function') {
      window.searchLocationDirect(loc);
      window.scrollTo({ top: 0, behavior: 'smooth' });
    } else {
      // On another page (About, History, Profile)
      window.location.href = '/?location=' + encodeURIComponent(loc);
    }
  };

  /**
   * Dismiss floating toast and remember dismissal across browser reloads
   */
  window.closeStormToast = function () {
    const toast = document.getElementById('stormToastNotification');
    if (toast) toast.style.display = 'none';
    if (activeAlertId) {
      try {
        localStorage.setItem('dismissed_alert_' + activeAlertId, '1');
        sessionStorage.setItem('dismissed_alert_' + activeAlertId, '1');
      } catch (e) {}
    }
  };

  /**
   * Render thunderstorm alert popup for all users
   */
  function displayThunderstormBroadcast(alertObj) {
    if (!alertObj || !alertObj.level || (alertObj.level !== 'CRITICAL' && alertObj.level !== 'MODERATE')) {
      return;
    }

    // Strict locality filtering: only display if alert matches user's registered locality
    const userLocality = (document.body.dataset.userLocality || '').trim();
    if (userLocality && !isLocationMatch(userLocality, alertObj.location)) {
      const toast = document.getElementById('stormToastNotification');
      if (toast) toast.style.display = 'none';
      return;
    }

    const alertId = alertObj.id || alertObj._id;
    if (alertId) {
      try {
        if (localStorage.getItem('dismissed_alert_' + alertId) === '1' || sessionStorage.getItem('dismissed_alert_' + alertId) === '1') {
          return;
        }
      } catch (e) {}
    }

    const toast = ensureToastDOM();
    activeAlertId = alertId;
    activeAlertLoc = alertObj.location || 'Karnataka';

    const msg = toast.querySelector('#toastMessage');
    const risk = toast.querySelector('#toastRisk');
    const loc = toast.querySelector('#toastLoc');
    const time = toast.querySelector('#toastTime');
    const title = toast.querySelector('.toast-title');

    if (alertObj.level === 'CRITICAL') {
      if (title) title.textContent = 'CRITICAL THUNDERSTORM ALERT';
      toast.style.borderColor = 'var(--accent-terracotta)';
      toast.style.boxShadow = '0 12px 36px rgba(200, 109, 81, 0.45)';
    } else {
      if (title) title.textContent = 'MODERATE THUNDERSTORM WATCH';
      toast.style.borderColor = 'var(--accent-honey)';
      toast.style.boxShadow = '0 12px 36px rgba(201, 136, 56, 0.35)';
    }

    if (msg) msg.textContent = alertObj.headline || 'High convective storm risk detected over Karnataka.';
    if (risk) risk.textContent = alertObj.probability ? `${Number(alertObj.probability).toFixed(1)}% Risk` : '--%';
    if (loc) loc.textContent = alertObj.location || 'Karnataka';
    if (time) time.textContent = alertObj.lead_time || '+30m Projection';

    toast.style.display = 'block';

    // Play alert chime
    playAlertChime();

    // Auto-dismiss after 16 seconds
    if (window.globalToastTimeout) clearTimeout(window.globalToastTimeout);
    window.globalToastTimeout = setTimeout(() => {
      toast.style.display = 'none';
    }, 16000);
  }

  // Export so app.js can call directly on local searches
  window.displayThunderstormBroadcast = displayThunderstormBroadcast;

  /**
   * Periodic Poller: Checks server every 8 seconds for active global alerts.
   * If there is no active alert or user dismissed it, ensures toast stays hidden.
   */
  async function checkActiveGlobalAlert() {
    try {
      const res = await fetch('/api/alerts/active', { cache: 'no-cache' });
      if (!res.ok) return;
      const data = await res.json();

      if (data && data.active && data.alert) {
        const alert = data.alert;
        const alertId = alert.id || alert._id;
        const sig = `${alertId}_${alert.location}_${alert.level}_${alert.probability}`;

        // Don't pop up again if user dismissed it in this browser
        try {
          if (localStorage.getItem('dismissed_alert_' + alertId) === '1' || sessionStorage.getItem('dismissed_alert_' + alertId) === '1') {
            return;
          }
        } catch (e) {}

        // Freshness verification:
        // Use created_at_epoch_ms if available, or parse ISO string with UTC 'Z' guarantee
        if (alert.created_at_epoch_ms || alert.created_at) {
          try {
            let createdAtMs = alert.created_at_epoch_ms;
            if (!createdAtMs && alert.created_at) {
              const rawStr = String(alert.created_at);
              const utcStr = (rawStr.endsWith('Z') || rawStr.includes('+')) ? rawStr : rawStr + 'Z';
              createdAtMs = new Date(utcStr).getTime();
            }
            if (createdAtMs && !isNaN(createdAtMs)) {
              const ageMs = Date.now() - createdAtMs;
              // Surface active alerts within the fresh 3-minute window (180,000 ms)
              if (ageMs > 180000 || ageMs < -60000) {
                return;
              }
            }
          } catch (e) {}
        }

        // Strict locality check: only alert users in the same location
        const userLocality = (document.body.dataset.userLocality || '').trim() || (document.getElementById('locationInput')?.value || '').trim();
        if (userLocality && !isLocationMatch(userLocality, alert.location)) {
          // Alert is for a different town/area: keep toast hidden for this user
          const toast = document.getElementById('stormToastNotification');
          if (toast && toast.style.display !== 'none') {
            toast.style.display = 'none';
          }
          return;
        }

        if (sig !== lastShownAlertSig) {
          lastShownAlertSig = sig;
          displayThunderstormBroadcast(alert);
        }
      } else {
        // No active severe thunderstorm alert in system: keep toast hidden
        const toast = document.getElementById('stormToastNotification');
        if (toast && toast.style.display !== 'none') {
          toast.style.display = 'none';
        }
      }
    } catch (e) {
      // Network interruption fallback
    }
  }

  // Initial check after 2 seconds
  setTimeout(checkActiveGlobalAlert, 2000);
  // Recurring check every 8 seconds across all connected user devices
  setInterval(checkActiveGlobalAlert, 8000);
})();

