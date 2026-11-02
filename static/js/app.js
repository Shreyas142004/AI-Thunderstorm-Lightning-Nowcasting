/**
 * AeroCast AI — Convective Nowcasting Frontend Engine
 * Handles real-time telemetry updates, interactive Leaflet Doppler radar,
 * free-form Karnataka place search, out-of-bounds warning alert, and Gemini AI synoptic advisory.
 */

// Global State
let currentTheme = localStorage.getItem('aerocast_theme') || 'light';
let currentLocation = 'Puttur';
let currentRadarCenter = [12.7667, 75.2016]; // Default Puttur coordinates

const INITIAL_CITY_COORDS = {
  'puttur': [12.7667, 75.2016],
  'bajpe': [12.9803, 74.8832],
  'bajipe': [12.9803, 74.8832],
  'mangaluru': [12.9141, 74.8560],
  'mangalore': [12.9141, 74.8560],
  'bengaluru': [12.9716, 77.5946],
  'bangalore': [12.9716, 77.5946],
  'hubballi': [15.3647, 75.1240],
  'hubli': [15.3647, 75.1240],
  'mysuru': [12.2958, 76.6394],
  'mysore': [12.2958, 76.6394],
  'udupi': [13.3409, 74.7421],
  'manipal': [13.3525, 74.7865],
  'bantwal': [12.8944, 75.0347],
  'sullia': [12.5562, 75.3897],
  'belthangady': [12.9984, 75.2575],
  'hassan': [13.0072, 76.1030],
  'shivamogga': [13.9299, 75.5681],
  'belagavi': [15.8497, 74.4977]
};

// Leaflet Map Handles
let radarMap = null;
let tileLayer = null;
let radarLayersGroup = null;
let stationMarkersGroup = null;

// Thunderstorm Alert State Tracker
let lastThunderstormAlertSig = null;
let currentActiveAlert = null;

// Active Timeline & Microzone State Tracker
let activeMainTimeline = null;
let activeMainStationName = '';
let lastRenderedData = null;
let selectedMicroZoneIdx = null;


// Initialize Application
function initApp() {
  setAppTheme(currentTheme);
  startLiveClock();

  const inputEl = document.getElementById('locationInput');
  const userLoc = (document.body.dataset.userLocality || '').trim() || (inputEl ? inputEl.value.trim() : 'Puttur');
  const townKey = userLoc.split(',')[0].trim().toLowerCase();
  if (INITIAL_CITY_COORDS[townKey]) {
    currentRadarCenter = INITIAL_CITY_COORDS[townKey];
  }

  initRadarMap();

  // If location query parameter is present in URL (e.g. from Search History page), execute nowcast for it
  const urlParams = new URLSearchParams(window.location.search);
  const qLoc = urlParams.get('location') || urlParams.get('q');
  if (qLoc && qLoc.trim()) {
    const cleanQ = qLoc.trim();
    if (inputEl) inputEl.value = cleanQ;
    currentLocation = cleanQ;
    fetchNowcast(cleanQ);
  } else {
    // Default search input and current location to the logged-in user's locality
    if (inputEl && userLoc) inputEl.value = userLoc;
    currentLocation = userLoc;
    // Do NOT automatically predict on fresh dashboard load:
    setIdleDashboardState();
  }
}

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', initApp);
} else {
  initApp();
}


/**
 * Dynamic 12-Hour IST Clock (Indian Standard Time, UTC+5:30)
 */
function startLiveClock() {
  const clockEl = document.getElementById('liveClock');
  function tick() {
    const now = new Date();
    try {
      const timeStr = now.toLocaleTimeString('en-US', {
        timeZone: 'Asia/Kolkata',
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit',
        hour12: true
      });
      if (clockEl) {
        clockEl.textContent = `${timeStr} IST`;
      }
    } catch (e) {
      // Fallback
      if (clockEl) {
        clockEl.textContent = now.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit', second: '2-digit', hour12: true }) + ' IST';
      }
    }
  }
  tick();
  setInterval(tick, 1000);
}


/**
 * Theme Switcher
 */
function setAppTheme(theme) {
  currentTheme = theme;
  document.documentElement.setAttribute('data-theme', theme);
  document.body.setAttribute('data-theme', theme);
  localStorage.setItem('aerocast_theme', theme);

  const btnLight = document.getElementById('btnLight');
  const btnDark = document.getElementById('btnDark');

  if (theme === 'light') {
    if (btnLight) btnLight.classList.add('active');
    if (btnDark) btnDark.classList.remove('active');
  } else {
    if (btnDark) btnDark.classList.add('active');
    if (btnLight) btnLight.classList.remove('active');
  }

  // Swap Map Tiles for current theme
  updateMapTiles();
}


/**
 * Initialize Interactive Leaflet Doppler Radar Map
 */
function initRadarMap() {
  const mapContainer = document.getElementById('radarLeafletMap');
  if (!mapContainer || typeof L === 'undefined') {
    console.warn("Leaflet container or library not ready, retrying...");
    setTimeout(initRadarMap, 300);
    return;
  }

  if (radarMap) {
    try { radarMap.remove(); } catch (e) {}
    radarMap = null;
  }

  try {
    radarMap = L.map('radarLeafletMap', {
      zoomControl: true,
      scrollWheelZoom: true,
      doubleClickZoom: true,
      touchZoom: true,
      boxZoom: true,
      keyboard: true,
      dragging: true,
      attributionControl: false,
      zoomSnap: 0.25,
      zoomDelta: 0.5,
      minZoom: 8,
      maxZoom: 16
    }).setView(currentRadarCenter, 12.5);

    // Apply theme tiles
    updateMapTiles();

    // Create persistent layer groups
    radarLayersGroup = L.layerGroup().addTo(radarMap);
    stationMarkersGroup = L.layerGroup().addTo(radarMap);

    // Force dimension check
    setTimeout(() => {
      if (radarMap) radarMap.invalidateSize();
    }, 200);

    // Automatic mobile orientation & resize adaptation
    window.addEventListener('resize', () => {
      if (radarMap) radarMap.invalidateSize();
    }, { passive: true });
    window.addEventListener('orientationchange', () => {
      setTimeout(() => { if (radarMap) radarMap.invalidateSize(); }, 250);
    }, { passive: true });
  } catch (err) {
    console.error("Error creating Leaflet radar map:", err);
  }
}


/**
 * Update Leaflet Map Tile Theme (Consistently OpenStreetMap across both Dark and Light Themes)
 */
function updateMapTiles() {
  if (!radarMap || typeof L === 'undefined') return;

  const tileUrl = 'https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png';

  // If tileLayer is already loaded with OpenStreetMap, keep it seamlessly without flicker
  if (tileLayer && tileLayer._url === tileUrl) {
    return;
  }

  if (tileLayer) {
    try { radarMap.removeLayer(tileLayer); } catch (e) {}
  }

  // Consistent OpenStreetMap across all themes (rich topography, towns, villages & boundaries)
  tileLayer = L.tileLayer(tileUrl, {
    maxZoom: 18,
    subdomains: ['a', 'b', 'c']
  }).addTo(radarMap);
}


/**
 * Update Radar Layer with Range Rings, dBZ Reflectivity Contours & Stations
 */
/**
 * Update Radar Layer with Range Rings, dBZ Reflectivity Contours & Stations
 */
function updateRadarMap(lat, lon, locationName, probability, microZones, isKarnataka) {
  if (!lat || !lon) {
    lat = 12.7667;
    lon = 75.2016;
  }
  currentRadarCenter = [lat, lon];

  if (!radarMap) {
    initRadarMap();
  }

  if (!radarMap) return;

  // Taluk-level zoom target:
  // Zoom 12.5 spans ~18 km width x 10 km height on the radar container,
  // framing strictly the active Taluk (e.g. Mangalore Taluk or Puttur Taluk).
  const targetZoom = isKarnataka ? 12.5 : 7.0;
  radarMap.flyTo([lat, lon], targetZoom, { duration: 1.2 });

  if (radarLayersGroup) radarLayersGroup.clearLayers();
  if (stationMarkersGroup) stationMarkersGroup.clearLayers();

  const hasProb = isKarnataka && (probability !== null && probability !== undefined);
  const prob = hasProb ? parseFloat(probability) : 0;

  // Circles removed per user request: Clean, unobstructed OpenStreetMap view

  // 3. Focal Station Marker
  const mainDotClass = hasProb
    ? (prob >= 70 ? 'pin-dot-red' : (prob >= 35 ? 'pin-dot-amber' : 'pin-dot-green'))
    : 'pin-dot-neutral';

  // Format clean, concise place name without redundant duplicate city tokens (e.g. "Bengaluru Urban" instead of "Bengaluru Urban, Bengaluru")
  function formatPillLocation(rawName) {
    if (!rawName) return 'Karnataka';
    const parts = rawName.split(',').map(p => p.trim()).filter(Boolean);
    if (!parts.length) return rawName;
    let main = parts[0];
    // Remove parenthetical noise like "(Airport Zone)" or "(Ct)" for sleek pill display
    main = main.replace(/\s*\([^)]*\)/g, '').trim();
    return main || parts[0];
  }

  const cleanLocName = formatPillLocation(locationName);
  const labelText = hasProb ? `${cleanLocName} (${prob.toFixed(1)}%)` : `${cleanLocName} (Outside KA)`;

  const focalIcon = L.divIcon({
    className: 'leaflet-radar-marker',
    html: `
      <div class="radar-station-blip" style="border: 2px solid ${hasProb && prob >= 70 ? 'var(--accent-terracotta)' : 'var(--card-border)'}; box-shadow: 0 4px 16px rgba(0,0,0,0.25);">
        <span class="pin-dot ${mainDotClass}"></span>
        <span class="blip-text">${labelText}</span>
      </div>
    `,
    iconSize: null,
    iconAnchor: null
  });

  L.marker([lat, lon], { icon: focalIcon, zIndexOffset: 2000 })
    .bindPopup(hasProb
      ? `<strong>${locationName} Observatory</strong><br>Convective Storm Probability: <strong>${prob.toFixed(1)}%</strong>`
      : `<strong>${locationName}</strong><br><em>Located outside Karnataka state boundary. AeroCast convective prediction disabled.</em>`
    )
    .addTo(stationMarkersGroup);

  // 4. Micro-Zone Stations (Only display if inside Karnataka and micro-zones exist)
  if (microZones && microZones.length > 0) {
    microZones.forEach((zone, idx) => {
      // Skip central hub duplicate (already marked by primary focal station)
      if (zone.is_center) return;
      const cleanZoneName = zone.name.split('&')[0].split('(')[0].trim();
      const cleanLower = cleanZoneName.toLowerCase();
      const locLower = locationName.toLowerCase();
      if (cleanLower === locLower || 
          (cleanLower.includes(locLower) && (cleanLower.includes('centre') || cleanLower.includes('center') || cleanLower.includes('hub') || cleanLower.includes('observatory') || cleanLower.includes('stand')))) {
        return;
      }

      // Determine Coordinates
      let zLat = zone.lat;
      let zLon = zone.lon;

      if (!zLat || !zLon) {
        const angles = [0.4, 1.8, 3.2, 4.8];
        const angle = angles[idx % angles.length];
        zLat = lat + (0.038 * Math.cos(angle));
        zLon = lon + (0.042 * Math.sin(angle));
      }

      // Check distance from focal point (if under ~1.2 km, nudge slightly to prevent label overlap)
      const distFromCenter = Math.hypot(zLat - lat, zLon - lon);
      if (distFromCenter < 0.012) {
        if (zLat >= lat) zLat += 0.016;
        else zLat -= 0.016;
      }

      const zProb = (zone.probability !== null && zone.probability !== undefined) ? parseFloat(zone.probability) : prob;
      const zDotClass = zProb >= 70 ? 'pin-dot-red' : (zProb >= 35 ? 'pin-dot-amber' : 'pin-dot-green');

      // Short clean display name (e.g. "Vitla", "Sullia", "Darbe", "Nehru Nagar")
      const shortName = cleanZoneName.split(' ')[0].trim();

      const subIcon = L.divIcon({
        className: 'leaflet-subzone-marker',
        html: `
          <div class="radar-subzone-chip" title="${zone.name} (${zProb.toFixed(1)}%)">
            <span class="subzone-dot ${zDotClass}"></span>
            <span class="subzone-name">${shortName}</span>
            <span class="subzone-prob">${zProb.toFixed(1)}%</span>
          </div>
        `,
        iconSize: null,
        iconAnchor: null
      });

      L.marker([zLat, zLon], { icon: subIcon, zIndexOffset: 800 })
        .bindPopup(`
          <div style="font-family: inherit; font-size: 0.82rem; line-height: 1.4; padding: 2px;">
            <strong>${zone.name}</strong><br>
            <span style="color: var(--text-muted);">Zone Convective Risk:</span> 
            <strong style="color: ${zProb >= 70 ? 'var(--accent-terracotta)' : (zProb >= 35 ? 'var(--accent-honey)' : 'var(--accent-sage)')};">${zProb.toFixed(1)}%</strong>
            <div style="margin-top: 8px;">
              <button type="button" onclick="openMicrozoneModalByIndex(${idx})" style="background: var(--accent-terracotta); color: #fff; border: none; border-radius: 6px; padding: 5px 10px; font-size: 0.72rem; font-weight: 700; cursor: pointer; display: inline-flex; align-items: center; gap: 4px;">
                <span>View 30-90m Pop-Up ↗</span>
              </button>
            </div>
          </div>
        `)
        .addTo(stationMarkersGroup);
    });
  }
}

/**
 * Center Map on Current Station
 */
function centerMapOnCurrentLocation() {
  if (radarMap && currentRadarCenter) {
    radarMap.flyTo(currentRadarCenter, 12.5, { duration: 0.8 });
  }
}

let loadingInterval = null;
let loadingStartTime = 0;

/**
 * Show Fullscreen Atmospheric Loading Screen Animation
 */
function showLoadingScreen(locationName) {
  const overlay = document.getElementById('nowcastLoadingOverlay');
  const targetEl = document.getElementById('loadingTargetName');
  const statusEl = document.getElementById('loadingStatusSub');

  if (targetEl) targetEl.textContent = locationName || 'Karnataka Station';
  if (statusEl) statusEl.textContent = 'Acquiring real-time Doppler radar & AWS surface telemetry...';

  if (overlay) {
    overlay.style.display = 'flex';
    void overlay.offsetWidth; // Force reflow
    overlay.classList.add('active');
  }

  loadingStartTime = Date.now();

  const messages = [
    'Acquiring real-time Doppler radar & AWS surface telemetry...',
    'Computing thermodynamic lapse rates & dew point depression...',
    'Executing 62-feature Soft Voting GBDT Ensemble...',
    'Synthesizing Western Ghats boundary-layer moisture flux...',
    'Querying Gemini AI synoptic meteorological advisory...'
  ];
  let msgIdx = 0;
  if (loadingInterval) clearInterval(loadingInterval);
  loadingInterval = setInterval(() => {
    msgIdx = (msgIdx + 1) % messages.length;
    if (statusEl) statusEl.textContent = messages[msgIdx];
  }, 400);
}

/**
 * Hide Fullscreen Atmospheric Loading Screen Animation
 */
function hideLoadingScreen() {
  if (loadingInterval) {
    clearInterval(loadingInterval);
    loadingInterval = null;
  }
  const overlay = document.getElementById('nowcastLoadingOverlay');
  if (!overlay) return;

  const elapsed = Date.now() - loadingStartTime;
  const remaining = Math.max(0, 750 - elapsed); // Smooth minimum animation display

  setTimeout(() => {
    overlay.classList.remove('active');
    setTimeout(() => {
      overlay.style.display = 'none';
    }, 300);
  }, remaining);
}

/**
 * Sets Dashboard to Idle / Ready State without running auto-predictions
 */
function setIdleDashboardState() {
  const overlay = document.getElementById('nowcastLoadingOverlay');
  if (overlay) {
    overlay.classList.remove('active');
    overlay.style.display = 'none';
  }

  // Ensure floating toast is dismissed on standby load
  if (typeof window.closeStormToast === 'function') {
    window.closeStormToast();
  } else {
    closeStormToast();
  }

  const alertEl = document.getElementById('riskAlertBanner');
  const alertText = document.getElementById('riskAlertText');
  if (alertEl) alertEl.className = 'risk-alert-pill alert-idle';
  if (alertText) alertText.textContent = 'READY TO NOWCAST • CLICK PREDICT';

  const probVal = document.getElementById('stormProbabilityVal');
  if (probVal) probVal.textContent = '--.-%';

  const fillArc = document.getElementById('dialFillArc');
  if (fillArc) fillArc.style.strokeDashoffset = '314';

  const addressEl = document.getElementById('resolvedAddressText');
  if (addressEl) addressEl.textContent = `Observatory set to ${currentLocation || 'Karnataka'} • Click Predict to evaluate live convective storm conditions`;

  const conditionEl = document.getElementById('conditionVal');
  if (conditionEl) conditionEl.textContent = 'Awaiting Query';

  // Telemetry stack
  const tempVal = document.getElementById('tempVal');
  const feelsLikeSub = document.getElementById('feelsLikeSub');
  if (tempVal) tempVal.textContent = '--.-°C';
  if (feelsLikeSub) feelsLikeSub.textContent = 'Feels like --.-°C';

  const dewVal = document.getElementById('dewVal');
  const dpdSub = document.getElementById('dpdSub');
  if (dewVal) dewVal.textContent = '--.-°C';
  if (dpdSub) dpdSub.textContent = 'Dew Point Depression: --.-°C';

  const humVal = document.getElementById('humVal');
  const vpdSub = document.getElementById('vpdSub');
  if (humVal) humVal.textContent = '--%';
  if (vpdSub) vpdSub.textContent = 'Vapor Deficit (VPD): --.- hPa';

  const cloudVal = document.getElementById('cloudVal');
  const rainSub = document.getElementById('rainSub');
  if (cloudVal) cloudVal.textContent = '--%';
  if (rainSub) rainSub.textContent = 'Precipitation: 0.0 mm';

  // Timeline steps
  for (let step = 1; step <= 3; step++) {
    const timeEl = document.getElementById(`step${step}Time`);
    const statusEl = document.getElementById(`step${step}Status`);
    const tempEl = document.getElementById(`step${step}Temp`);
    const cloudEl = document.getElementById(`step${step}Cloud`);
    const humEl = document.getElementById(`step${step}Hum`);
    const probEl = document.getElementById(`step${step}Prob`);
    const footerEl = document.getElementById(`step${step}FooterPill`);
    const pillTextEl = document.getElementById(`step${step}PillText`);

    if (timeEl) timeEl.textContent = step === 1 ? '+30 Mins' : (step === 2 ? '+60 Mins' : '+90 Mins');
    if (statusEl) statusEl.textContent = 'Pending Prediction';
    if (tempEl) tempEl.textContent = '--.-°C';
    if (cloudEl) cloudEl.textContent = '--%';
    if (humEl) humEl.textContent = '--%';
    if (probEl) probEl.textContent = '--.-%';
    if (footerEl) footerEl.className = 'step-footer-pill pill-muted';
    if (pillTextEl) pillTextEl.textContent = 'Standby';
  }

  // Gemini advisory placeholders
  const bulletinEl = document.getElementById('geminiBulletinText');
  if (bulletinEl) bulletinEl.textContent = 'Type any Karnataka location above and click "Predict" to see live weather, thunderstorm risk, and simple daily safety advice.';

  const agriEl = document.getElementById('geminiAgriText');
  if (agriEl) agriEl.textContent = 'Awaiting location query...';

  const travelEl = document.getElementById('geminiTravelText');
  if (travelEl) travelEl.textContent = 'Awaiting location query...';

  const outdoorEl = document.getElementById('geminiOutdoorText');
  if (outdoorEl) outdoorEl.textContent = 'Awaiting location query...';

  // Reset Thunderstorm Alert Panel to Idle
  resetThunderstormAlertToIdle();
}

/**
 * Free-Form Location Search Handler
 */
function handleLocationSearch(event) {
  if (event) event.preventDefault();
  const inputEl = document.getElementById('locationInput');
  let query = inputEl ? inputEl.value.trim() : '';

  if (!query) {
    query = 'Puttur';
    if (inputEl) inputEl.value = 'Puttur';
  }

  currentLocation = query;
  fetchNowcast(query);
}

/**
 * Direct Quick Search from Buttons
 */
function searchLocationDirect(locName) {
  const inputEl = document.getElementById('locationInput');
  if (inputEl) inputEl.value = locName;
  currentLocation = locName;
  dismissOutOfBoundsWarning();
  fetchNowcast(locName);
}

/**
 * Dismiss Out of Bounds Warning Banner
 */
function dismissOutOfBoundsWarning() {
  const banner = document.getElementById('outOfBoundsWarning');
  if (banner) banner.style.display = 'none';
  const inputWrap = document.querySelector('.location-search-wrapper');
  if (inputWrap) inputWrap.style.borderColor = '';
}


/**
 * Main Asynchronous Data Fetcher
 */
async function fetchNowcast(location) {
  setLoadingState(true);
  showLoadingScreen(location);

  // If page is loaded as local file:/// or on another port (e.g. 5500), target Flask at 127.0.0.1:5000
  let apiBase = '';
  if (window.location.protocol === 'file:' || (window.location.port && window.location.port !== '5000')) {
    apiBase = 'http://127.0.0.1:5000';
  }

  try {
    const response = await fetch(`${apiBase}/api/nowcast?location=${encodeURIComponent(location)}`, {
      mode: 'cors'
    });
    if (!response.ok) {
      throw new Error(`API returned ${response.status}`);
    }
    const data = await response.json();
    
    // Hide offline banner if previously shown
    const connBanner = document.getElementById('connectionBanner');
    if (connBanner) connBanner.style.display = 'none';

    renderDashboard(data);
  } catch (err) {
    console.warn("Could not reach live Flask backend at " + (apiBase || window.location.origin) + ". Loading fallback preview telemetry:", err);
    
    // Show offline connection notice
    const connBanner = document.getElementById('connectionBanner');
    if (connBanner) connBanner.style.display = 'block';

    const fallbackData = getFallbackNowcastData(location);
    renderDashboard(fallbackData);
  } finally {
    setLoadingState(false);
    hideLoadingScreen();
  }
}

/**
 * Generate Realistic Offline Nowcast Data
 */
function getFallbackNowcastData(location) {
  const locLower = location.toLowerCase();
  const isPuttur = locLower.includes('puttur');
  const prob = isPuttur ? 88.5 : 42.0;

  // Check known out of karnataka cities in offline mode
  const nonKaCities = [
    'goa', 'sikkim', 'andhra', 'andhra pradesh', 'kerala', 'tamil nadu', 'maharashtra',
    'telangana', 'delhi', 'mumbai', 'chennai', 'kolkata', 'hyderabad', 'london', 'new york',
    'kochi', 'panaji', 'gangtok', 'jaipur', 'lucknow', 'ahmedabad', 'pune', 'bihar', 'gujarat'
  ];
  const isOutside = nonKaCities.some(c => locLower.includes(c));

  // Determine realistic coordinates (Never default outside places to Mangalore/Puttur!)
  let outLat = 20.5937, outLon = 78.9629;
  if (locLower.includes('goa') || locLower.includes('panaji')) { outLat = 15.2993; outLon = 74.1240; }
  else if (locLower.includes('sikkim') || locLower.includes('gangtok')) { outLat = 27.5330; outLon = 88.5122; }
  else if (locLower.includes('andhra')) { outLat = 15.9129; outLon = 79.7400; }
  else if (locLower.includes('mumbai')) { outLat = 19.0760; outLon = 72.8777; }
  else if (locLower.includes('delhi')) { outLat = 28.6139; outLon = 77.2090; }
  else if (locLower.includes('chennai')) { outLat = 13.0827; outLon = 80.2707; }
  else if (locLower.includes('hyderabad')) { outLat = 17.3850; outLon = 78.4867; }

  return {
    location: location,
    resolved_address: `${location}, ${isOutside ? 'India / Global (Outside Karnataka Grid)' : 'Karnataka, India'} (Preview Mode)`,
    latitude: isOutside ? outLat : (isPuttur ? 12.7667 : 12.9716),
    longitude: isOutside ? outLon : (isPuttur ? 75.2016 : 77.5946),
    is_karnataka: !isOutside,
    warning: isOutside ? `Warning: '${location}' is located outside Karnataka state boundary! AeroCast AI convective models and S-band Doppler radar are specifically calibrated for Karnataka & Western Ghats atmospheric physics (11.5°N - 18.6°N, 74.0°E - 78.6°E). Weather display and predictions are disabled for out-of-state locations.` : null,
    timestamp: new Date().toLocaleTimeString('en-GB') + ' IST (Cached)',
    telemetry: isOutside ? {
      temp: null,
      humidity: null,
      dew: null,
      dpd: null,
      vpd: null,
      pressure: null,
      pressure_drop: null,
      windspeed: null,
      winddir: null,
      cloudcover: null,
      conditions: "Prediction Disabled (Outside Karnataka)"
    } : {
      temp: 26.2,
      humidity: 94.0,
      dew: 25.1,
      dpd: 1.1,
      vpd: 0.3,
      pressure: 1004.2,
      pressure_drop: -1.8,
      windspeed: 3.2,
      winddir: 130
    },
    prediction: {
      convective_probability: isOutside ? null : prob,
      binary_prediction: isOutside ? null : (prob >= 50 ? 1 : 0),
      risk_level: isOutside ? 'PREDICTION DISABLED (Outside Karnataka Boundary)' : (prob >= 70 ? 'CRITICAL (Severe Thunderstorm / Heavy Rain Alert)' : 'MODERATE (Thunderstorm Watch / Cell Initiation)'),
      alert_code: isOutside ? 'DISABLED' : (prob >= 70 ? 'RED' : 'YELLOW'),
      is_available: !isOutside
    },
    timeline: [
      {
        label: "+30 Mins Later",
        time_str: "+30m",
        temp: 26.0,
        humidity: 96,
        cloudcover: 95,
        conditions: isOutside ? "Regional Observation" : "Towering Cumulus / Cell Formation",
        probability: isOutside ? null : Math.min(100, prob + 4),
        windspeed: 3.5,
        alert_code: isOutside ? 'DISABLED' : (prob >= 70 ? 'RED' : 'YELLOW')
      },
      {
        label: "+60 Mins Later",
        time_str: "+60m",
        temp: 25.5,
        humidity: 98,
        cloudcover: 100,
        conditions: isOutside ? "Regional Observation" : "Active Convective Downdrafts",
        probability: isOutside ? null : Math.min(100, prob + 7),
        windspeed: 4.8,
        alert_code: isOutside ? 'DISABLED' : 'RED'
      },
      {
        label: "+90 Mins Later",
        time_str: "+90m",
        temp: 25.1,
        humidity: 99,
        cloudcover: 98,
        conditions: isOutside ? "Regional Observation" : "Heavy Rain / Lightning Discharge",
        probability: isOutside ? null : Math.min(100, prob + 5),
        windspeed: 4.0,
        alert_code: isOutside ? 'DISABLED' : 'RED'
      }
    ],
    micro_zones: isOutside ? [] : (isPuttur ? [
      { name: "Puttur Town Centre & Bus Stand", probability: prob, is_center: true, lat: 12.7667, lon: 75.2016 },
      { name: "Darbe & Bedrala Zone", probability: prob, lat: 12.7480, lon: 75.2010 },
      { name: "Nehru Nagar & Kabaka Zone", probability: prob, lat: 12.7950, lon: 75.2050 },
      { name: "Vitla (Vittla) Town Belt", probability: prob, lat: 12.7674, lon: 75.1012 },
      { name: "Sullia Foothills Belt", probability: prob, lat: 12.5606, lon: 75.3905 }
    ] : [
      { name: `${location} Core / Urban Hub`, probability: prob, is_center: true, lat: 12.7667, lon: 75.2016 },
      { name: `${location} North Ridge`, probability: Math.min(100, prob + 3), lat: 12.85, lon: 75.22 },
      { name: `${location} South Valley`, probability: Math.max(0, prob - 5), lat: 12.68, lon: 75.18 },
      { name: `${location} West Corridor`, probability: prob, lat: 12.76, lon: 75.08 }
    ]),
    gemini_advisory: {
      status: "preview",
      model: "Gemini Flash (Preview Mode)",
      synoptic_bulletin: `Pre-convective boundary layer saturation observed over ${location}. Surface dew point depression is under 2°C, coupled with positive moisture flux convergence along the Ghats. High probability of localized convective cell formation within 60 minutes.`,
      agriculture_advisory: "Cover open areca nut, pepper drying yards, and rubber harvests immediately. Clear field drainage channels to prevent flash waterlogging.",
      travel_safety_advisory: "Exercise caution on state highways due to sudden downdraft wind gusts and slick road surfaces. Do not shelter beneath isolated tall trees during lightning events.",
      aviation_outdoor_warning: "Moderate to severe low-level turbulence and cloud-to-ground lightning hazard expected within the next 45 to 90 minutes."
    },
    thunderstorm_alert: isOutside ? {
      status: "unavailable",
      level: "NONE",
      probability: null,
      location: location,
      lead_time: "N/A",
      headline: "No current thunderstorm alert data available",
      explanation: `Warning: '${location}' is located outside Karnataka state boundary. Convective storm predictions are disabled for out-of-state sectors.`,
      timestamp: new Date().toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit', hour12: true }) + ' IST'
    } : {
      status: "active",
      level: prob >= 70 ? "CRITICAL" : (prob >= 35 ? "MODERATE" : "LOW"),
      probability: prob,
      location: location,
      lead_time: "+30 to +60 Mins",
      headline: prob >= 70 
        ? "High thunderstorm risk detected. Avoid exposed outdoor areas and monitor official weather warnings."
        : (prob >= 35 
            ? "Thunderstorm conditions may develop. Please monitor weather updates."
            : "Low thunderstorm risk. Calm and stable weather expected across the region."),
      explanation: prob >= 70 
        ? `Critical convective atmospheric instability observed across ${location}. Intense lightning, heavy downbursts, and gusty winds anticipated within forecast window.`
        : (prob >= 35 
            ? `Elevated moisture and convective instability detected over ${location}. Towering cumulus development and sudden passing showers possible within forecast window.`
            : `Boundary-layer thermodynamic energy over ${location} is stable. Convective storm initiation is not expected within the forecast window.`),
      timestamp: new Date().toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit', hour12: true }) + ' IST'
    }
  };
}


/**
 * Render All Dashboard Components
 */
function renderDashboard(data) {
  const tel = data.telemetry || {};
  const pred = data.prediction || {};
  const timeItems = data.timeline || [];
  const gemini = data.gemini_advisory || {};

  // 1. Out of Karnataka Boundary Warning Detection
  const outOfBoundsEl = document.getElementById('outOfBoundsWarning');
  const outOfBoundsText = document.getElementById('outOfBoundsText');
  const inputWrap = document.querySelector('.location-search-wrapper');

  if (data.is_karnataka === false || data.warning) {
    if (outOfBoundsEl) {
      outOfBoundsEl.style.display = 'flex';
      if (outOfBoundsText) {
        outOfBoundsText.textContent = data.warning || `Warning: '${data.location}' is located outside Karnataka state boundary! AeroCast AI convective models and S-band Doppler radar are specifically calibrated for Karnataka & Western Ghats atmospheric physics (11.5°N - 18.6°N, 74.0°E - 78.6°E). Predictions shown are experimental.`;
      }
    }
    if (inputWrap) {
      inputWrap.style.borderColor = 'var(--accent-terracotta)';
      inputWrap.style.boxShadow = '0 0 0 3px rgba(217, 83, 79, 0.25)';
    }
  } else {
    if (outOfBoundsEl) {
      outOfBoundsEl.style.display = 'none';
    }
    if (inputWrap) {
      inputWrap.style.borderColor = '';
      inputWrap.style.boxShadow = '';
    }
  }

  // Sync Input Value if changed externally
  const inputEl = document.getElementById('locationInput');
  if (inputEl && document.activeElement !== inputEl) {
    inputEl.value = data.location;
  }

  // 2. Resolved Address & Timestamp
  document.getElementById('resolvedAddressText').textContent = data.resolved_address || data.location;
  document.getElementById('radarUpdateTag').textContent = `Observed: ${data.timestamp || 'Live'}`;

  // 3. Convective Risk Core (Concentric Dial)
  const isKa = (data.is_karnataka !== false && !data.warning);
  const hasProb = isKa && (pred.convective_probability !== null && pred.convective_probability !== undefined && !isNaN(pred.convective_probability));
  const probValEl = document.getElementById('stormProbabilityVal');
  const fillArc = document.getElementById('dialFillArc');
  const banner = document.getElementById('riskAlertBanner');
  const alertText = document.getElementById('riskAlertText');
  const probLabelEl = document.querySelector('.dial-prob-label');

  if (!hasProb) {
    // Outside Karnataka: HIDE / DO NOT SHOW WEATHER PROBABILITY
    probValEl.textContent = 'N/A';
    probValEl.style.fontSize = '2.4rem';
    probValEl.style.color = 'var(--text-muted)';
    if (probLabelEl) probLabelEl.textContent = 'Prediction Inactive';
    fillArc.style.strokeDashoffset = 314; // Empty arc (0%)

    banner.className = 'risk-alert-pill alert-muted';
    alertText.textContent = 'PREDICTION DISABLED (OUTSIDE KARNATAKA)';
  } else {
    const prob = parseFloat(pred.convective_probability);
    probValEl.textContent = `${prob.toFixed(1)}%`;
    probValEl.style.fontSize = '';
    probValEl.style.color = '';
    if (probLabelEl) probLabelEl.textContent = 'Convective Potential';
    const offset = Math.max(0, 314 - (314 * (prob / 100)));
    fillArc.style.strokeDashoffset = offset;

    banner.className = 'risk-alert-pill';
    if (prob >= 70.0) {
      banner.classList.add('alert-red');
      alertText.textContent = 'CRITICAL CONVECTIVE ALERT';
    } else if (prob >= 35.0) {
      banner.classList.add('alert-yellow');
      alertText.textContent = 'MODERATE CONVECTIVE WATCH';
    } else {
      banner.classList.add('alert-green');
      alertText.textContent = 'FAIR WEATHER / LOW RISK';
    }
  }

  // 4. Telemetry Stack (Disabled & Hidden for Out-of-Karnataka Locations)
  if (isKa && tel.temp !== null && tel.temp !== undefined) {
    document.getElementById('tempVal').textContent = `${tel.temp}°C`;
    document.getElementById('feelsLikeSub').textContent = `Feels like ${(tel.temp + 2.5).toFixed(1)}°C`;
  } else {
    document.getElementById('tempVal').textContent = '--';
    document.getElementById('feelsLikeSub').textContent = 'Outside Karnataka Grid';
  }

  const dpdSub = document.getElementById('dpdStatusSub');
  if (isKa && tel.dpd !== null && tel.dpd !== undefined) {
    document.getElementById('dpdVal').textContent = `${tel.dpd}°C`;
    if (tel.dpd < 3.0) {
      dpdSub.textContent = "Near Saturation (<3°C)";
      dpdSub.className = "telemetry-sub accent-terracotta-text";
    } else if (tel.dpd <= 6.0) {
      dpdSub.textContent = "High Moisture (3-6°C)";
      dpdSub.className = "telemetry-sub accent-sage-text";
    } else {
      dpdSub.textContent = "Dry Boundary Layer";
      dpdSub.className = "telemetry-sub";
    }
  } else {
    document.getElementById('dpdVal').textContent = '--';
    dpdSub.textContent = 'Disabled (Out of Bounds)';
    dpdSub.className = 'telemetry-sub';
  }

  document.getElementById('vpdVal').textContent = (isKa && tel.vpd !== null && tel.vpd !== undefined) ? `${tel.vpd} hPa` : '--';
  document.getElementById('pressureDropVal').textContent = (isKa && tel.pressure_drop !== null && tel.pressure_drop !== undefined) ? `${tel.pressure_drop} hPa` : '--';

  // Save state for timeline restoration & microzone navigation
  lastRenderedData = data;
  activeMainTimeline = data.timeline || [];
  activeMainStationName = data.location || 'Observatory';
  selectedMicroZoneIdx = null;

  const timelineHeading = document.getElementById('timelineTrackHeading');
  if (timelineHeading) timelineHeading.textContent = 'Timeline Nowcasting Track';
  const timelineSub = document.getElementById('timelineTrackSub');
  if (timelineSub) timelineSub.textContent = '3-Step short-term convective cell evolution (+30m, +60m, +90m)';
  const resetBtn = document.getElementById('btnResetTimeline');
  if (resetBtn) resetBtn.style.display = 'none';

  // 5. Update Interactive Leaflet Doppler Radar Map
  updateRadarMap(data.latitude, data.longitude, data.location, hasProb ? pred.convective_probability : null, data.micro_zones, isKa);

  // 5b. Update Places & Micro-Zones Panel on the Right of the Radar Map
  renderPlacesDetails(data);

  // 6. 3-Step Timeline Progression
  renderTimelineTrack(timeItems, hasProb);

  // 7. Gemini AI Meteorological Advisory
  renderGeminiAdvisory(gemini);

  // 8. In-Dashboard Thunderstorm Alert Messages
  renderThunderstormAlert(data);
}


/**
 * Render 3-Step Timeline Progression (Dynamic Risk Theming per Minute Card)
 * - Low / No Risk (< 35%): Green (Sage)
 * - Less / Moderate Risk (35% - 69.9%): Yellow / Orange (Honey)
 * - High / Critical Risk (>= 70%): Red (Terracotta)
 */
function renderTimelineTrack(timeline, hasProb) {
  if (!timeline || timeline.length < 3) return;

  const steps = [
    { card: 'stepCard1', iconBox: 'step1IconBox', time: 'step1Time', temp: 'step1Temp', cond: 'step1Condition', cloud: 'step1Cloud', hum: 'step1Hum', prob: 'step1Prob', pill: 'step1PillText', footerPill: 'step1FooterPill' },
    { card: 'stepCard2', iconBox: 'step2IconBox', time: 'step2Time', temp: 'step2Temp', cond: 'step2Condition', cloud: 'step2Cloud', hum: 'step2Hum', prob: 'step2Prob', pill: 'step2PillText', footerPill: 'step2FooterPill' },
    { card: 'stepCard3', iconBox: 'step3IconBox', time: 'step3Time', temp: 'step3Temp', cond: 'step3Condition', cloud: 'step3Cloud', hum: 'step3Hum', prob: 'step3Prob', pill: 'step3PillText', footerPill: 'step3FooterPill' }
  ];

  let maxProb = 0;

  steps.forEach((cfg, idx) => {
    const item = timeline[idx];
    if (!item) return;

    const timeEl = document.getElementById(cfg.time);
    const tempEl = document.getElementById(cfg.temp);
    const condEl = document.getElementById(cfg.cond);
    const cloudEl = document.getElementById(cfg.cloud);
    const humEl = document.getElementById(cfg.hum);
    const probEl = document.getElementById(cfg.prob);
    const pillTextEl = document.getElementById(cfg.pill);
    const cardEl = document.getElementById(cfg.card);
    const iconBoxEl = document.getElementById(cfg.iconBox);
    const footerPillEl = document.getElementById(cfg.footerPill);

    if (timeEl) timeEl.textContent = item.time_str || '--:--';
    if (tempEl) tempEl.textContent = `${item.temp}°C`;
    if (condEl) condEl.textContent = item.conditions || 'Developing';
    if (cloudEl) cloudEl.textContent = `${item.cloudcover}%`;
    if (humEl) humEl.textContent = `${item.humidity}%`;

    if (!hasProb || item.probability === null || item.probability === undefined || isNaN(item.probability)) {
      if (probEl) probEl.textContent = 'N/A';
      if (pillTextEl) pillTextEl.textContent = '— Outside Grid';
      if (cardEl) cardEl.className = 'step-card card-muted';
      if (iconBoxEl) iconBoxEl.className = 'step-icon-box box-muted';
      if (footerPillEl) footerPillEl.className = 'step-footer-pill pill-muted';
    } else {
      const p = parseFloat(item.probability);
      if (probEl) probEl.textContent = `${p.toFixed(1)}%`;
      if (p > maxProb) maxProb = p;

      // Dynamically theme each minute card by its OWN predicted risk
      if (p >= 70.0) {
        // High Risk -> RED (Terracotta)
        if (cardEl) cardEl.className = 'step-card card-terracotta';
        if (iconBoxEl) {
          iconBoxEl.className = 'step-icon-box box-terracotta';
          iconBoxEl.innerHTML = `
            <svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
              <path d="M17.5 19H9a7 7 0 1 1 6.71-9h1.79a4.5 4.5 0 1 1 0 9Z"/>
              <line x1="9" y1="20" x2="8" y2="22"/><line x1="13" y1="20" x2="12" y2="22"/><line x1="17" y1="20" x2="16" y2="22"/>
              <path d="m14 11-3 5h3l-2 4"/>
            </svg>
          `;
        }
        if (footerPillEl) footerPillEl.className = 'step-footer-pill pill-terracotta';
        if (pillTextEl) pillTextEl.textContent = '⛈️ Critical Alert';
      } else if (p >= 35.0) {
        // Less / Moderate Risk -> YELLOW / ORANGE (Honey)
        if (cardEl) cardEl.className = 'step-card card-honey';
        if (iconBoxEl) {
          iconBoxEl.className = 'step-icon-box box-honey';
          iconBoxEl.innerHTML = `
            <svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
              <path d="M17.5 19H9a7 7 0 1 1 6.71-9h1.79a4.5 4.5 0 1 1 0 9Z"/>
              <path d="m13 13-2 4h3l-2 4"/>
            </svg>
          `;
        }
        if (footerPillEl) footerPillEl.className = 'step-footer-pill pill-honey';
        if (pillTextEl) pillTextEl.textContent = '⚡ Cell Formation';
      } else {
        // No Risk / Low Risk -> GREEN (Sage)
        if (cardEl) cardEl.className = 'step-card card-sage';
        if (iconBoxEl) {
          iconBoxEl.className = 'step-icon-box box-sage';
          iconBoxEl.innerHTML = `
            <svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
              <path d="M12 2v2M4.93 4.93l1.41 1.41M2 12h2M6.34 17.66l-1.41 1.41"/>
              <circle cx="12" cy="12" r="4"/>
              <path d="M17.5 19H9a7 7 0 1 1 6.71-9h1.79a4.5 4.5 0 1 1 0 9Z"/>
            </svg>
          `;
        }
        if (footerPillEl) footerPillEl.className = 'step-footer-pill pill-sage';
        if (pillTextEl) pillTextEl.textContent = '● Calm / Fair';
      }
    }
  });

  // Flow Arrows color progression to match downstream target step
  const arrow1 = document.getElementById('stepFlowArrow1');
  const arrow2 = document.getElementById('stepFlowArrow2');
  if (arrow1 && timeline[1]) {
    const p1 = hasProb ? parseFloat(timeline[1].probability || 0) : null;
    const stroke1 = (p1 === null || isNaN(p1)) ? 'var(--card-border)' : (p1 >= 70.0 ? 'var(--accent-terracotta)' : (p1 >= 35.0 ? 'var(--accent-honey)' : 'var(--accent-sage)'));
    const svg1 = arrow1.querySelector('svg');
    if (svg1) svg1.setAttribute('stroke', stroke1);
  }
  if (arrow2 && timeline[2]) {
    const p2 = hasProb ? parseFloat(timeline[2].probability || 0) : null;
    const stroke2 = (p2 === null || isNaN(p2)) ? 'var(--card-border)' : (p2 >= 70.0 ? 'var(--accent-terracotta)' : (p2 >= 35.0 ? 'var(--accent-honey)' : 'var(--accent-sage)'));
    const svg2 = arrow2.querySelector('svg');
    if (svg2) svg2.setAttribute('stroke', stroke2);
  }

  // Update Timeline Indicator Pill
  const topPill = document.getElementById('timelineIndicatorPill');
  if (topPill) {
    if (!hasProb) {
      topPill.className = 'timeline-indicator-pill indicator-muted';
      topPill.textContent = '— Regional Meteorological Track';
    } else if (maxProb >= 70.0) {
      topPill.className = 'timeline-indicator-pill indicator-terracotta';
      topPill.textContent = '⛈️ Critical Convective Discharges';
    } else if (maxProb >= 35.0) {
      topPill.className = 'timeline-indicator-pill indicator-honey';
      topPill.textContent = '⚡ Developing Pre-Storm Moisture Surge';
    } else {
      topPill.className = 'timeline-indicator-pill indicator-sage';
      topPill.textContent = '● Stable Boundary Layer (Low Risk)';
    }
  }
}


/**
 * Render Gemini AI Advisory
 */
function renderGeminiAdvisory(gemini) {
  document.getElementById('geminiBulletinText').textContent = 
    gemini.synoptic_bulletin || "Atmospheric boundary layer is under continuous observation across Karnataka.";

  document.getElementById('geminiAgriText').textContent = 
    gemini.agriculture_advisory || "Monitor ongoing rainfall and maintain drainage in plantation crops.";

  document.getElementById('geminiTravelText').textContent = 
    gemini.travel_safety_advisory || "Normal transit with isolated convective rain showers possible.";

  document.getElementById('geminiOutdoorText').textContent = 
    gemini.aviation_outdoor_warning || "Exercise standard outdoor thunderstorm safety during afternoon hours.";

  const modelTag = document.getElementById('geminiModelTag');
  modelTag.textContent = gemini.model || 'Gemini Flash';
}


/**
 * Render Places Details & Micro-Zones Panel on the Right of the Radar Map
 */
function renderPlacesDetails(data) {
  const pred = data.prediction || {};
  const isKa = (data.is_karnataka !== false && !data.warning);
  const hasProb = isKa && (pred.convective_probability !== null && pred.convective_probability !== undefined && !isNaN(pred.convective_probability));
  const prob = hasProb ? parseFloat(pred.convective_probability) : null;

  // 1. Region Badge
  const regBadge = document.getElementById('placesRegionBadge');
  if (regBadge) {
    if (isKa) {
      regBadge.textContent = 'Karnataka Grid';
      regBadge.className = 'places-region-badge';
    } else {
      regBadge.textContent = 'Outside KA Grid';
      regBadge.className = 'places-region-badge out-of-bounds';
    }
  }

  // 2. Active Focal Place Card
  const activeName = document.getElementById('activePlaceName');
  const activeRisk = document.getElementById('activePlaceRiskBadge');
  const activeCoords = document.getElementById('activePlaceCoords');
  const activeStatus = document.getElementById('activePlaceStatus');

  if (activeName) activeName.textContent = `${data.location} Observatory`;
  if (activeCoords && data.latitude && data.longitude) {
    activeCoords.textContent = `${data.latitude.toFixed(4)}°N, ${data.longitude.toFixed(4)}°E`;
  }
  if (activeStatus) {
    activeStatus.textContent = isKa ? 'Primary Radar Focal Point' : 'Prediction Disabled — Outside Karnataka Boundary';
    activeStatus.style.color = isKa ? 'var(--text-secondary)' : 'var(--accent-terracotta)';
  }

  if (activeRisk) {
    if (hasProb) {
      activeRisk.textContent = `${prob.toFixed(1)}%`;
      activeRisk.className = 'place-risk-pill ' + (prob >= 70 ? 'risk-pill-red' : (prob >= 35 ? 'risk-pill-amber' : 'risk-pill-green'));
    } else {
      activeRisk.textContent = 'N/A';
      activeRisk.className = 'place-risk-pill risk-pill-muted';
    }
  }

  // 3. Sub-Zones / Taluks List
  const listBody = document.getElementById('placesListBody');
  const zoneCountTag = document.getElementById('placesZoneCount');
  if (!listBody) return;

  listBody.innerHTML = '';

  if (!isKa) {
    if (zoneCountTag) zoneCountTag.textContent = '0 Zones';
    listBody.innerHTML = `
      <div class="out-of-bounds-note-card">
        <div class="out-of-bounds-note-title">⚠️ Outside Karnataka Radar Coverage</div>
        <div class="out-of-bounds-note-desc">
          Telemetry for <strong>${data.location}</strong> is shown for reference. Micro-zone convective radar modeling is calibrated exclusively for Karnataka's 31 districts & Western Ghats.
        </div>
        <div class="out-of-bounds-quick-links">
          <button type="button" class="out-of-bounds-quick-btn" onclick="searchLocationDirect('Puttur')">Puttur</button>
          <button type="button" class="out-of-bounds-quick-btn" onclick="searchLocationDirect('Bengaluru')">Bengaluru</button>
          <button type="button" class="out-of-bounds-quick-btn" onclick="searchLocationDirect('Mangaluru')">Mangaluru</button>
        </div>
      </div>
    `;
    return;
  }

  const zones = data.micro_zones || [];
  if (zoneCountTag) zoneCountTag.textContent = `${zones.length} Zones`;

  if (zones.length === 0) {
    listBody.innerHTML = `<div style="font-size: 0.76rem; color: var(--text-muted); padding: 12px; text-align: center;">No micro-zones mapped for this location.</div>`;
    return;
  }

  zones.forEach((zone, idx) => {
    const zProb = parseFloat(zone.probability !== undefined && zone.probability !== null ? zone.probability : (prob || 28.0));
    const pillClass = zProb >= 70 ? 'risk-pill-red' : (zProb >= 35 ? 'risk-pill-amber' : 'risk-pill-green');
    const zTemp = zone.temp ? `${zone.temp.toFixed(1)}°C` : `${(data.telemetry?.temp || 26.5).toFixed(1)}°C`;
    const zHum = zone.humidity ? `${zone.humidity.toFixed(0)}% Hum` : `${(data.telemetry?.humidity || 85).toFixed(0)}% Hum`;

    const row = document.createElement('div');
    row.className = 'place-item-card';
    row.id = `placeCard_${idx}`;
    row.title = `Click to view +30m, +60m, +90m weather prediction pop-up window for ${zone.name}`;
    row.innerHTML = `
      <div class="place-item-info">
        <span class="place-item-name">${zone.name}</span>
        <span class="place-item-sub">${zTemp} • ${zHum}</span>
      </div>
      <div style="display: flex; align-items: center; gap: 8px;">
        <span class="place-item-risk ${pillClass}">${zProb.toFixed(1)}%</span>
        <button type="button" class="place-view-modal-btn" title="Open 30, 60, 90 mins prediction pop-up" aria-label="Open prediction pop-up">
          <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.3" stroke-linecap="round" stroke-linejoin="round">
            <path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"></path>
            <polyline points="15 3 21 3 21 9"></polyline>
            <line x1="10" y1="14" x2="21" y2="3"></line>
          </svg>
        </button>
      </div>
    `;

    // Click to open detailed 30, 60, 90 mins prediction pop-up window (keeps main weather intact)
    row.addEventListener('click', (e) => {
      e.stopPropagation();
      document.querySelectorAll('.place-item-card.active').forEach(el => el.classList.remove('active'));
      row.classList.add('active');
      openMicrozoneModal(zone, data);
    });

    listBody.appendChild(row);
  });
}

/**
 * Active Pop-Up Modal Zone References
 */
let currentModalZone = null;
let currentModalData = null;

/**
 * Open Micro-Zone Weather Prediction Pop-Up Window (+30m, +60m, +90m)
 */
function openMicrozoneModal(zone, data) {
  currentModalZone = zone;
  currentModalData = data;

  const modal = document.getElementById('microzoneModal');
  if (!modal) return;

  const mzmTitle = document.getElementById('mzmTitle');
  const mzmSub = document.getElementById('mzmSubheading');
  const mzmRiskBadge = document.getElementById('mzmRiskBadge');
  const mzmCoordsBadge = document.getElementById('mzmCoordsBadge');
  const mzmSummaryMeta = document.getElementById('mzmSummaryMeta');
  const mzmStepsGrid = document.getElementById('mzmStepsGrid');
  const mzmHeaderIcon = document.getElementById('mzmHeaderIcon');

  if (mzmTitle) mzmTitle.textContent = `${zone.name} Nowcast`;

  const zLat = zone.lat || data.latitude || 12.9141;
  const zLon = zone.lon || data.longitude || 74.8560;
  if (mzmCoordsBadge) mzmCoordsBadge.textContent = `${zLat.toFixed(4)}°N, ${zLon.toFixed(4)}°E`;
  if (mzmSub) mzmSub.textContent = `High-Resolution 30, 60 & 90-Minute Convective Prediction • ${data.location || 'Karnataka'} Sector`;

  const zProb = parseFloat(zone.probability !== undefined && zone.probability !== null ? zone.probability : (data.prediction?.convective_probability || 30.0));
  const zTemp = zone.temp !== undefined ? zone.temp : (data.telemetry?.temp || 26.5);
  const zHum = zone.humidity !== undefined ? zone.humidity : (data.telemetry?.humidity || 82.0);
  const zCloud = zone.cloudcover !== undefined ? zone.cloudcover : (data.telemetry?.cloudcover || 75.0);

  if (mzmRiskBadge) {
    if (zProb >= 70.0) {
      mzmRiskBadge.textContent = `⛈️ CRITICAL RISK (${zProb.toFixed(1)}%)`;
      mzmRiskBadge.className = 'mzm-badge-risk risk-red';
      if (mzmHeaderIcon) mzmHeaderIcon.textContent = '⛈️';
    } else if (zProb >= 35.0) {
      mzmRiskBadge.textContent = `⚡ MODERATE RISK (${zProb.toFixed(1)}%)`;
      mzmRiskBadge.className = 'mzm-badge-risk risk-amber';
      if (mzmHeaderIcon) mzmHeaderIcon.textContent = '⚡';
    } else {
      mzmRiskBadge.textContent = `🌤️ LOW RISK (${zProb.toFixed(1)}%)`;
      mzmRiskBadge.className = 'mzm-badge-risk risk-green';
      if (mzmHeaderIcon) mzmHeaderIcon.textContent = '🌤️';
    }
  }

  if (mzmSummaryMeta) {
    mzmSummaryMeta.textContent = `Current Baseline: ${zTemp.toFixed(1)}°C • ${zHum.toFixed(0)}% Hum • ${zCloud.toFixed(0)}% Clouds`;
  }

  // Obtain or synthesize 3-step timeline (+30m, +60m, +90m)
  let zTimeline = zone.timeline;
  if (!zTimeline || !Array.isArray(zTimeline) || zTimeline.length < 3) {
    const now = new Date();
    const offsets = [
      { label: "+30 Mins Later", mins: 30, dt: 0.0, dh: 0.0, dc: 0.0 },
      { label: "+60 Mins Later", mins: 60, dt: -0.4, dh: 3.0, dc: 5.0 },
      { label: "+90 Mins Later", mins: 90, dt: -0.8, dh: 5.0, dc: 8.0 }
    ];

    zTimeline = offsets.map((off, oIdx) => {
      const tDate = new Date(now.getTime() + off.mins * 60000);
      const timeStr = tDate.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
      let sProb = zProb;
      let cond = "Scattered Clouds / Partly Cloudy";
      let code = "GREEN";
      let rLvl = "LOW (Convective Instability Unlikely)";

      if (zProb >= 70.0) {
        sProb = Math.min(100.0, zProb + (oIdx === 1 ? 2.0 : (oIdx === 2 ? -1.5 : 0.0)));
        cond = sProb >= 75 ? "Severe Thunderstorm / Squall" : "Thunderstorm with Heavy Downpours";
        code = "RED";
        rLvl = "CRITICAL (Severe Thunderstorm / Heavy Rain Alert)";
      } else if (zProb >= 35.0) {
        sProb = Math.min(90.0, Math.max(20.0, zProb + (oIdx === 1 ? 3.5 : 1.0)));
        cond = sProb >= 50 ? "Developing Thunderstorm / Towering Cumulus" : "Pre-Storm Instability";
        code = "YELLOW";
        rLvl = "MODERATE (Thunderstorm Watch / Cell Initiation)";
      } else {
        sProb = Math.max(5.0, zProb + (oIdx * 1.5));
        cond = sProb < 25 ? "Partly Cloudy / Fair" : "Isolated Cloud Buildup";
        code = "GREEN";
      }

      const sTemp = parseFloat((zTemp + off.dt).toFixed(1));
      const sHum = Math.min(100, Math.round(zHum + off.dh));
      const sDew = parseFloat((sTemp - ((100 - sHum) / 5)).toFixed(1));

      return {
        label: off.label,
        time_str: timeStr,
        temp: sTemp,
        dew: sDew,
        humidity: sHum,
        cloudcover: Math.min(100, Math.round(zCloud + off.dc)),
        windspeed: parseFloat((3.2 + (zProb >= 50 ? oIdx * 0.8 : 0.2)).toFixed(1)),
        probability: parseFloat(sProb.toFixed(1)),
        conditions: cond,
        alert_code: code,
        risk_level: rLvl
      };
    });
  }

  // Populate 3 step cards in modal grid
  if (mzmStepsGrid) {
    mzmStepsGrid.innerHTML = '';
    const stepLabels = ['+30 Mins Later', '+60 Mins Later', '+90 Mins Later'];
    zTimeline.slice(0, 3).forEach((step, sIdx) => {
      const p = parseFloat(step.probability !== undefined && step.probability !== null ? step.probability : zProb);
      const cardClass = p >= 70.0 ? 'step-red' : (p >= 35.0 ? 'step-amber' : 'step-green');
      const riskPillText = p >= 70.0 ? 'Critical Alert' : (p >= 35.0 ? 'Pre-Storm Watch' : 'Calm / Fair');
      const labelText = step.label || stepLabels[sIdx];
      const dewVal = step.dew !== undefined ? `${step.dew}°C` : `${(step.temp - 2.5).toFixed(1)}°C`;
      const windVal = step.windspeed !== undefined ? `${step.windspeed} km/h` : '4.2 km/h';

      const card = document.createElement('div');
      card.className = `mzm-step-card-full ${cardClass}`;
      card.innerHTML = `
        <div class="mzm-step-head">
          <span class="mzm-step-label">${labelText}</span>
          <span class="mzm-step-time-badge">${step.time_str || '--:--'}</span>
        </div>
        <div class="mzm-step-prob-row">
          <span class="mzm-step-big-prob">${p.toFixed(1)}%</span>
          <span class="mzm-step-risk-pill">${riskPillText}</span>
        </div>
        <div class="mzm-step-condition" title="${step.conditions}">
          ${step.conditions || 'Cloud Development'}
        </div>
        <div class="mzm-step-metrics-grid">
          <div class="mzm-metric-item">
            <span class="mzm-metric-lbl">🌡️ Temperature</span>
            <span class="mzm-metric-val">${step.temp}°C</span>
          </div>
          <div class="mzm-metric-item">
            <span class="mzm-metric-lbl">💧 Humidity</span>
            <span class="mzm-metric-val">${step.humidity}%</span>
          </div>
          <div class="mzm-metric-item">
            <span class="mzm-metric-lbl">☁️ Cloud Cover</span>
            <span class="mzm-metric-val">${step.cloudcover}%</span>
          </div>
          <div class="mzm-metric-item">
            <span class="mzm-metric-lbl">💨 Wind Speed</span>
            <span class="mzm-metric-val">${windVal}</span>
          </div>
        </div>
      `;
      mzmStepsGrid.appendChild(card);
    });
  }

  // Display pop-up window
  modal.style.display = 'flex';
  document.body.style.overflow = 'hidden';
}

/**
 * Close Micro-Zone Pop-Up Window
 * Ensures main dashboard telemetry, timeline, and radar remain on primary location
 */
function closeMicrozoneModal() {
  const modal = document.getElementById('microzoneModal');
  if (modal) modal.style.display = 'none';
  document.body.style.overflow = '';

  // Remove active highlight from microzone cards in the list
  document.querySelectorAll('.place-item-card.active').forEach(el => el.classList.remove('active'));

  // Ensure radar map view remains centered on the main searched location
  if (lastRenderedData && radarMap && lastRenderedData.latitude && lastRenderedData.longitude) {
    radarMap.flyTo([lastRenderedData.latitude, lastRenderedData.longitude], 12, { duration: 0.5 });
  }

  // Ensure timeline track remains on the primary observatory forecast
  if (typeof resetTimelineTrack === 'function') {
    resetTimelineTrack();
  }
}

/**
 * Handle clicking outside modal card (Backdrop click)
 */
function handleMicrozoneModalBackdrop(e) {
  if (e.target.id === 'microzoneModal') {
    closeMicrozoneModal();
  }
}

/**
 * Fly radar directly to active modal zone
 */
function flyRadarToActiveZone() {
  if (currentModalZone && radarMap) {
    const destLat = currentModalZone.lat || currentModalData?.latitude;
    const destLon = currentModalZone.lon || currentModalData?.longitude;
    if (destLat && destLon) {
      radarMap.flyTo([destLat, destLon], 13.5, { duration: 0.8 });
    }
  }
  closeMicrozoneModal();
}

/**
 * Sync active modal zone to main dashboard Timeline track
 */
function syncModalToTimelineTrack() {
  if (currentModalZone) {
    const zTimeline = currentModalZone.timeline;
    if (zTimeline && zTimeline.length >= 3) {
      const heading = document.getElementById('timelineTrackHeading');
      if (heading) heading.innerHTML = `Timeline Track — <span style="color: var(--accent-terracotta);">${currentModalZone.name}</span>`;
      const sub = document.getElementById('timelineTrackSub');
      if (sub) sub.textContent = `Localized 3-step convective nowcast (+30m, +60m, +90m) for ${currentModalZone.name}`;

      const resetBtn = document.getElementById('btnResetTimeline');
      if (resetBtn) {
        resetBtn.style.display = 'inline-flex';
        resetBtn.innerHTML = `
          <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
            <polyline points="1 4 1 10 7 10"/><path d="M3.51 15a9 9 0 1 0 2.13-9.36L1 10"/>
          </svg>
          <span>Reset to ${activeMainStationName}</span>
        `;
      }
      renderTimelineTrack(zTimeline, true);
    }
  }
  closeMicrozoneModal();
  focusTimelineTrack();
}

/**
 * Helper to open modal by micro-zone index (e.g. from Leaflet map popup)
 */
function openMicrozoneModalByIndex(idx) {
  if (lastRenderedData && lastRenderedData.micro_zones && lastRenderedData.micro_zones[idx]) {
    openMicrozoneModal(lastRenderedData.micro_zones[idx], lastRenderedData);
  }
}

/**
 * Reset Timeline Track Back to Main Observatory Forecast
 */
function resetToFocalTimeline(e) {
  if (e) {
    e.stopPropagation();
    e.preventDefault();
  }
  selectedMicroZoneIdx = null;

  document.querySelectorAll('.place-item-card.active').forEach(el => el.classList.remove('active'));

  const heading = document.getElementById('timelineTrackHeading');
  if (heading) heading.textContent = 'Timeline Nowcasting Track';
  const sub = document.getElementById('timelineTrackSub');
  if (sub) sub.textContent = '3-Step short-term convective cell evolution (+30m, +60m, +90m)';

  const resetBtn = document.getElementById('btnResetTimeline');
  if (resetBtn) resetBtn.style.display = 'none';

  if (activeMainTimeline && activeMainTimeline.length >= 3) {
    const hasProb = activeMainTimeline.some(t => t.probability !== null && t.probability !== undefined);
    renderTimelineTrack(activeMainTimeline, hasProb);
  }

  if (radarMap && lastRenderedData && lastRenderedData.latitude && lastRenderedData.longitude) {
    radarMap.flyTo([lastRenderedData.latitude, lastRenderedData.longitude], 12.0, { duration: 0.6 });
  }
}

/**
 * Smoothly scroll to the main Timeline track
 */
function focusTimelineTrack(e) {
  if (e) e.stopPropagation();
  const el = document.getElementById('timelineTrackHeading') || document.querySelector('.timeline-section');
  if (el) {
    el.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
  }
}

/**
 * Visual Loading State
 */
function setLoadingState(isLoading) {
  const dialText = document.getElementById('stormProbabilityVal');
  const searchBtn = document.getElementById('searchSubmitBtn');
  if (isLoading) {
    if (dialText) dialText.style.opacity = '0.5';
    if (searchBtn) {
      searchBtn.disabled = true;
      searchBtn.style.opacity = '0.6';
    }
  } else {
    if (dialText) dialText.style.opacity = '1';
    if (searchBtn) {
      searchBtn.disabled = false;
      searchBtn.style.opacity = '1';
    }
  }
}


/**
 * Reset Thunderstorm Alert Notification Panel to Idle / Standby
 */
function resetThunderstormAlertToIdle() {
  lastThunderstormAlertSig = null;
  const panel = document.getElementById('thunderstormAlertBanner');
  if (!panel) return;

  panel.className = 'thunderstorm-alert-panel alert-state-idle';

  const iconText = document.getElementById('alertIconText');
  if (iconText) iconText.textContent = '⚡';

  const severityPill = document.getElementById('alertSeverityPill');
  if (severityPill) severityPill.textContent = 'System Standby';

  const riskPill = document.getElementById('alertRiskPill');
  if (riskPill) riskPill.style.display = 'none';

  const locPill = document.getElementById('alertLocationPill');
  if (locPill) locPill.style.display = 'none';

  const leadPill = document.getElementById('alertLeadTimePill');
  if (leadPill) leadPill.style.display = 'none';

  const headlineEl = document.getElementById('alertHeadlineTitle');
  if (headlineEl) headlineEl.textContent = 'No current thunderstorm alert data available';

  const explanationEl = document.getElementById('alertExplanationText');
  if (explanationEl) explanationEl.textContent = 'Select or search any Karnataka location above and click "Predict" to evaluate live convective storm conditions.';

  const timestampEl = document.getElementById('alertTimestamp');
  if (timestampEl) timestampEl.textContent = 'Awaiting Query';
}


/**
 * Render In-Dashboard Thunderstorm Alert Notification Panel
 * Connects directly to existing GBDT predictions & timeline lead times.
 * Avoids re-triggering / flickering if prediction has not changed.
 */
function renderThunderstormAlert(data) {
  const panel = document.getElementById('thunderstormAlertBanner');

  let alertObj = data.thunderstorm_alert;

  // Client-side fallback if server payload did not include thunderstorm_alert
  if (!alertObj) {
    const isKa = (data.is_karnataka !== false && !data.warning);
    const pred = data.prediction || {};
    const prob = pred.convective_probability;

    if (isKa && prob !== null && prob !== undefined && !isNaN(prob)) {
      const p = parseFloat(prob);
      let lvl = 'LOW';
      let headline = 'Low thunderstorm risk. Calm and stable weather expected across the region.';
      let exp = `Boundary-layer thermodynamic energy over ${data.location || 'the area'} is stable. Convective storm initiation is not expected within the forecast window.`;

      if (p >= 70.0) {
        lvl = 'CRITICAL';
        headline = 'High thunderstorm risk detected. Avoid exposed outdoor areas and monitor official weather warnings.';
        exp = `Critical convective atmospheric instability observed across ${data.location || 'the area'}. Intense lightning, heavy downbursts, and gusty winds anticipated.`;
      } else if (p >= 35.0) {
        lvl = 'MODERATE';
        headline = 'Thunderstorm conditions may develop. Please monitor weather updates.';
        exp = `Elevated moisture and convective instability detected over ${data.location || 'the area'}. Towering cumulus development and sudden passing showers possible.`;
      }

      alertObj = {
        status: 'active',
        level: lvl,
        probability: p,
        location: data.location,
        lead_time: '+30 to +90 Mins',
        headline: headline,
        explanation: exp,
        timestamp: data.timestamp || 'Live'
      };
    } else {
      alertObj = {
        status: 'unavailable',
        level: 'NONE',
        probability: null,
        location: data.location,
        lead_time: 'N/A',
        headline: 'No current thunderstorm alert data available',
        explanation: data.warning || 'Select or search any Karnataka location to evaluate live convective storm conditions.',
        timestamp: data.timestamp || 'Live'
      };
    }
  }

  currentActiveAlert = alertObj;

  // Deduplication check: Avoid re-rendering if exact same prediction is active
  const alertSig = `${alertObj.status}_${alertObj.level}_${alertObj.probability}_${alertObj.location}_${alertObj.lead_time}_${alertObj.headline}`;
  if (alertSig === lastThunderstormAlertSig) {
    return; // No change in prediction state
  }
  lastThunderstormAlertSig = alertSig;

  const iconText = document.getElementById('alertIconText');
  const severityPill = document.getElementById('alertSeverityPill');
  const riskPill = document.getElementById('alertRiskPill');
  const riskVal = document.getElementById('alertRiskValue');
  const locPill = document.getElementById('alertLocationPill');
  const locName = document.getElementById('alertLocationName');
  const leadPill = document.getElementById('alertLeadTimePill');
  const leadTimeText = document.getElementById('alertLeadTimeText');
  const headlineEl = document.getElementById('alertHeadlineTitle');
  const explanationEl = document.getElementById('alertExplanationText');
  const timestampEl = document.getElementById('alertTimestamp');

  // Case 1: Out of bounds, error, or no valid prediction available
  if (alertObj.status === 'unavailable' || alertObj.level === 'NONE' || alertObj.probability === null) {
    if (panel) panel.className = 'thunderstorm-alert-panel alert-state-idle';
    if (iconText) iconText.textContent = 'ℹ️';
    if (severityPill) severityPill.textContent = 'No Active Alert';
    if (riskPill) riskPill.style.display = 'none';

    if (locPill) {
      if (alertObj.location) {
        locPill.style.display = 'inline-flex';
        if (locName) locName.textContent = alertObj.location;
      } else {
        locPill.style.display = 'none';
      }
    }

    if (leadPill) leadPill.style.display = 'none';
    if (headlineEl) headlineEl.textContent = alertObj.headline || 'No current thunderstorm alert data available';
    if (explanationEl) explanationEl.textContent = alertObj.explanation || 'Select or search any Karnataka location to evaluate live convective storm conditions.';
    if (timestampEl) timestampEl.textContent = alertObj.timestamp || 'Live';
    return;
  }

  // Case 2: Valid prediction with risk level (LOW, MODERATE, CRITICAL)
  const lvl = alertObj.level.toUpperCase();

  if (lvl === 'CRITICAL') {
    if (panel) panel.className = 'thunderstorm-alert-panel alert-state-critical';
    if (iconText) iconText.textContent = '⚡🚨';
    if (severityPill) severityPill.textContent = 'CRITICAL ALERT (≥70%)';
  } else if (lvl === 'MODERATE') {
    if (panel) panel.className = 'thunderstorm-alert-panel alert-state-moderate';
    if (iconText) iconText.textContent = '⚠️';
    if (severityPill) severityPill.textContent = 'MODERATE ALERT (35%–70%)';
  } else {
    if (panel) panel.className = 'thunderstorm-alert-panel alert-state-low';
    if (iconText) iconText.textContent = '🛡️';
    if (severityPill) severityPill.textContent = 'LOW RISK (<35%)';
  }

  // Risk % Pill
  if (riskPill && riskVal) {
    riskPill.style.display = 'inline-flex';
    riskVal.textContent = alertObj.probability !== null && alertObj.probability !== undefined
      ? `${Number(alertObj.probability).toFixed(1)}%`
      : '--%';
  }

  // Affected Location Pill
  if (locPill && locName) {
    if (alertObj.location) {
      locPill.style.display = 'inline-flex';
      locName.textContent = alertObj.location;
    } else {
      locPill.style.display = 'none';
    }
  }

  // Forecast Lead Time Pill (+30m, +60m, +90m)
  if (leadPill && leadTimeText) {
    if (alertObj.lead_time && alertObj.lead_time !== 'N/A') {
      leadPill.style.display = 'inline-flex';
      leadTimeText.textContent = alertObj.lead_time;
    } else {
      leadPill.style.display = 'none';
    }
  }

  // Clear Title and Description
  if (headlineEl) headlineEl.textContent = alertObj.headline;
  if (explanationEl) explanationEl.textContent = alertObj.explanation;
  if (timestampEl) timestampEl.textContent = `Issued: ${alertObj.timestamp || 'Live'}`;

  // If Critical or Moderate, trigger floating toast notification alert and auto-broadcast to registered citizens
  if (lvl === 'CRITICAL' || lvl === 'MODERATE') {
    if (typeof window.displayThunderstormBroadcast === 'function') {
      window.displayThunderstormBroadcast(alertObj);
    } else {
      showStormToast(alertObj);
    }
    autoBroadcastThunderstormAlert(alertObj);
  } else {
    closeStormToast();
  }
}

/**
 * Display floating on-screen Thunderstorm Alert Toast
 */
function showStormToast(alertObj) {
  const toast = document.getElementById('stormToastNotification');
  if (!toast) return;

  const msg = document.getElementById('toastMessage');
  const risk = document.getElementById('toastRisk');
  const loc = document.getElementById('toastLoc');
  const time = document.getElementById('toastTime');
  const title = toast.querySelector('.toast-title');

  if (alertObj.level === 'CRITICAL') {
    if (title) title.textContent = 'CRITICAL THUNDERSTORM ALERT';
    toast.style.borderColor = 'var(--accent-terracotta)';
  } else if (alertObj.level === 'MODERATE') {
    if (title) title.textContent = 'MODERATE THUNDERSTORM WATCH';
    toast.style.borderColor = 'var(--accent-honey)';
  } else {
    toast.style.display = 'none';
    return;
  }

  if (msg) msg.textContent = alertObj.headline || 'Thunderstorm conditions detected.';
  if (risk) risk.textContent = alertObj.probability ? `${Number(alertObj.probability).toFixed(1)}% Risk` : '--%';
  if (loc) loc.textContent = alertObj.location || 'Karnataka';
  if (time) time.textContent = alertObj.lead_time || '+30m';

  toast.style.display = 'block';

  // Auto-dismiss after 12 seconds
  if (window.toastTimeout) clearTimeout(window.toastTimeout);
  window.toastTimeout = setTimeout(() => {
    toast.style.display = 'none';
  }, 12000);
}

/**
 * Dismiss floating alert toast
 */
function closeStormToast() {
  const toast = document.getElementById('stormToastNotification');
  if (toast) toast.style.display = 'none';
  if (currentActiveAlert && (currentActiveAlert.id || currentActiveAlert._id)) {
    try {
      const aId = currentActiveAlert.id || currentActiveAlert._id;
      localStorage.setItem('dismissed_alert_' + aId, '1');
      sessionStorage.setItem('dismissed_alert_' + aId, '1');
    } catch (e) {}
  }
}


/* ==========================================================================
   Presentation & Evaluator Thunderstorm Simulation Engine
   ========================================================================== */

/**
 * Interactive Presentation & Evaluator Thunderstorm Simulator
 * Instantly generates coordinated convective storm telemetry,
 * Doppler radar storm cell reflectivity, and alert notifications.
 */
async function triggerPresentationDemo(scenario) {
  // Clear alert deduplication signature so it always animates immediately
  lastThunderstormAlertSig = null;

  const inputEl = document.getElementById('locationInput');
  const loc = (inputEl && inputEl.value.trim()) ? inputEl.value.trim() : (currentLocation || 'Puttur');
  currentLocation = loc;
  let lat = (currentRadarCenter && currentRadarCenter[0]) ? currentRadarCenter[0] : 12.7667;
  let lon = (currentRadarCenter && currentRadarCenter[1]) ? currentRadarCenter[1] : 75.2016;

  // Show "Reset to Live" button
  const liveBtn = document.getElementById('btnRestoreLive');
  if (liveBtn) liveBtn.style.display = 'inline-flex';

  try {
    const res = await fetch(`/api/demo/thunderstorm?scenario=${encodeURIComponent(scenario)}&location=${encodeURIComponent(loc)}`);
    if (res.ok) {
      const serverDemoData = await res.json();
      renderDashboard(serverDemoData);
      return;
    }
  } catch (err) {
    console.warn("Could not reach /api/demo/thunderstorm backend, using fallback:", err);
  }

  let demoData = null;
  const nowTime = new Date().toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit', second: '2-digit', hour12: true }) + ' IST (Simulation Mode)';

  if (scenario === 'critical') {
    demoData = {
      location: loc,
      resolved_address: `${loc} Observatory, Dakshina Kannada, Karnataka (Severe Convective Simulation)`,
      latitude: lat,
      longitude: lon,
      is_karnataka: true,
      warning: null,
      timestamp: nowTime,
      telemetry: {
        temp: 28.8,
        humidity: 94.0,
        dew: 27.6,
        dpd: 1.2,
        vpd: 0.3,
        pressure: 1001.2,
        pressure_drop: -3.8,
        windspeed: 38.5,
        winddir: 245,
        cloudcover: 98.0,
        conditions: "Severe Thunderstorm with Downdraft Gusts"
      },
      prediction: {
        convective_probability: 88.5,
        binary_prediction: 1,
        risk_level: "CRITICAL (Severe Thunderstorm / Heavy Rain Alert)",
        alert_code: "RED",
        weather_condition: "Severe Thunderstorm with Intense Convective Discharges",
        model_source: "Soft Voting Ensemble GBDT (Karnataka Calibrated)",
        is_available: true
      },
      timeline: [
        {
          label: "+30 Mins Later",
          time_label: "+30m Projection",
          time_str: "+30m",
          temp: 26.5,
          humidity: 98,
          cloudcover: 100,
          conditions: "Critical Lightning Discharges & Intense Rain",
          probability: 92.5,
          windspeed: 42.0,
          alert_code: "RED"
        },
        {
          label: "+60 Mins Later",
          time_label: "+60m Projection",
          time_str: "+60m",
          temp: 25.2,
          humidity: 96,
          cloudcover: 95,
          conditions: "Heavy Downdraft Precipitation & Microbursts",
          probability: 86.0,
          windspeed: 36.0,
          alert_code: "RED"
        },
        {
          label: "+90 Mins Later",
          time_label: "+90m Projection",
          time_str: "+90m",
          temp: 25.0,
          humidity: 92,
          cloudcover: 85,
          conditions: "Passing Convective Cell & Dissipating Rain",
          probability: 71.0,
          windspeed: 24.0,
          alert_code: "RED"
        }
      ],
      micro_zones: (loc.toLowerCase().includes('mangalore') || loc.toLowerCase().includes('mangaluru')) ? [
        { name: "Hampankatta (City Centre & Taluk Hub)", lat: 12.8700, lon: 74.8430, probability: 88.5, temp: 28.5, humidity: 94 },
        { name: "Kadri Hills & Mallikatte Zone", lat: 12.8830, lon: 74.8620, probability: 86.0, temp: 28.8, humidity: 92 },
        { name: "Surathkal & NITK Coastal Sector", lat: 13.0070, lon: 74.7940, probability: 91.5, temp: 27.8, humidity: 96 },
        { name: "Panambur Port & Industrial Sector", lat: 12.9460, lon: 74.8120, probability: 89.2, temp: 28.1, humidity: 95 },
        { name: "Ullal Coastal Belt & Estuary", lat: 12.8050, lon: 74.8520, probability: 85.0, temp: 28.6, humidity: 93 },
        { name: "Bajpe (Airport Zone & North Taluk)", lat: 12.9803, lon: 74.8832, probability: 87.8, temp: 28.2, humidity: 94 }
      ] : [
        { name: "Puttur Town & Bus Stand (Taluk Centre)", lat: 12.7667, lon: 75.2016, probability: 88.5, temp: 28.8, humidity: 94 },
        { name: "Darbe Commercial Sector", lat: 12.7580, lon: 75.2050, probability: 87.0, temp: 29.0, humidity: 93 },
        { name: "Kabaka & Polya Agricultural Zone", lat: 12.7880, lon: 75.1850, probability: 90.5, temp: 28.4, humidity: 96 },
        { name: "Bannur & Kemminje Green Corridor", lat: 12.7520, lon: 75.2210, probability: 86.5, temp: 28.9, humidity: 93 },
        { name: "Aryapu & Balnadu Rural Valley", lat: 12.7350, lon: 75.1750, probability: 89.0, temp: 28.5, humidity: 95 },
        { name: "Bettampady & Ariyadka Foothills", lat: 12.7150, lon: 75.2280, probability: 85.0, temp: 28.2, humidity: 96 }
      ],
      gemini_advisory: {
        status: "success",
        model: "Gemini AI + Karnataka Convective Ensemble (Severe Storm Simulation)",
        synoptic_bulletin: `Severe convective storm cell initiation confirmed over ${loc}. Atmospheric thermodynamics indicate extreme instability (CAPE > 2900 J/kg) coupled with active orographic lifting along the Western Ghats. Radar reflectivity echoes exceed 55 dBZ with violent cloud-to-ground lightning discharges, localized microburst downdrafts, and torrential rain rates.`,
        ai_risk_assessment: "CRITICAL",
        agriculture_advisory: `Immediate protective protocol for areca nut, rubber, and paddy plantations in ${loc} and surrounding taluks: clear roadside drainage culverts immediately and secure all harvested crops from direct squall exposure.`,
        travel_safety_advisory: `CRITICAL TRAVEL WARNING: Hazardous transit on State Highway 88 and Ghat passes. Sudden gale-force downdrafts (35-50 km/h) and blinding rain will severely diminish vehicular braking distance. Avoid parking beneath tall roadside trees.`,
        aviation_outdoor_warning: `SEVERE DANGER: Severe low-level wind shear and frequent cloud-to-ground lightning strokes detected within a 25 km radius. Suspend all drone surveys and outdoor sports immediately.`
      },
      thunderstorm_alert: {
        status: "active",
        level: "CRITICAL",
        probability: 88.5,
        location: loc,
        lead_time: "+30m Projection",
        headline: "High thunderstorm risk detected. Avoid exposed outdoor areas and monitor official weather warnings.",
        explanation: `Critical convective atmospheric instability observed across ${loc}. Intense lightning, heavy downbursts, and gusty winds anticipated within +30m Projection.`,
        timestamp: new Date().toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit', hour12: true }) + ' IST (Simulation)'
      }
    };
  } else if (scenario === 'moderate') {
    demoData = {
      location: loc,
      resolved_address: `${loc} Observatory, Karnataka (Convective Watch Simulation)`,
      latitude: lat,
      longitude: lon,
      is_karnataka: true,
      warning: null,
      timestamp: nowTime,
      telemetry: {
        temp: 30.2,
        humidity: 82.0,
        dew: 25.8,
        dpd: 4.4,
        vpd: 0.9,
        pressure: 1005.1,
        pressure_drop: -1.6,
        windspeed: 18.0,
        winddir: 210,
        cloudcover: 72.0,
        conditions: "Towering Cumulus / Developing Thunderstorm Cell"
      },
      prediction: {
        convective_probability: 54.2,
        binary_prediction: 1,
        risk_level: "MODERATE (Thunderstorm Watch / Cell Initiation)",
        alert_code: "YELLOW",
        weather_condition: "Developing Convective Cloud Tower",
        model_source: "Soft Voting Ensemble GBDT (Karnataka Calibrated)",
        is_available: true
      },
      timeline: [
        {
          label: "+30 Mins Later",
          time_label: "+30m Projection",
          time_str: "+30m",
          temp: 29.5,
          humidity: 85,
          cloudcover: 78,
          conditions: "Towering Cumulus Initiation",
          probability: 48.0,
          windspeed: 16.0,
          alert_code: "YELLOW"
        },
        {
          label: "+60 Mins Later",
          time_label: "+60m Projection",
          time_str: "+60m",
          temp: 28.6,
          humidity: 89,
          cloudcover: 86,
          conditions: "Isolated Convective Showers Possible",
          probability: 58.5,
          windspeed: 22.0,
          alert_code: "YELLOW"
        },
        {
          label: "+90 Mins Later",
          time_label: "+90m Projection",
          time_str: "+90m",
          temp: 27.8,
          humidity: 88,
          cloudcover: 80,
          conditions: "Localized Passing Rain",
          probability: 51.0,
          windspeed: 18.0,
          alert_code: "YELLOW"
        }
      ],
      micro_zones: [
        { name: `${loc} Center`, lat: lat, lon: lon, probability: 54.2, temp: 30.2, humidity: 82 },
        { name: `${loc} North`, lat: lat + 0.03, lon: lon, probability: 58.0, temp: 29.8, humidity: 84 },
        { name: `${loc} South`, lat: lat - 0.03, lon: lon, probability: 49.5, temp: 30.5, humidity: 80 }
      ],
      gemini_advisory: {
        status: "success",
        model: "Gemini AI + Karnataka Convective Ensemble (Watch Simulation)",
        synoptic_bulletin: `Moderate convective instability developing over ${loc}. Rising daytime insolation and boundary-layer moisture convergence are generating towering cumulus clouds along local ridgelines. Isolated lightning and sudden passing showers may occur within the next 45 to 90 minutes.`,
        ai_risk_assessment: "MODERATE",
        agriculture_advisory: `Favorable moisture for plantation crops, but prepare cover for drying produce in open yards as brief passing showers are anticipated.`,
        travel_safety_advisory: `Roads remain generally clear with moderate crosswinds. Watch for wet asphalt on shaded forest stretches.`,
        aviation_outdoor_warning: `Monitor localized thermal updrafts. Low risk of direct lightning currently, but maintain vigilance.`
      },
      thunderstorm_alert: {
        status: "active",
        level: "MODERATE",
        probability: 54.2,
        location: loc,
        lead_time: "+60m Projection",
        headline: "Thunderstorm conditions may develop. Please monitor weather updates.",
        explanation: `Elevated moisture and convective instability detected over ${loc}. Towering cumulus development and sudden passing showers possible within +60m Projection.`,
        timestamp: new Date().toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit', hour12: true }) + ' IST (Simulation)'
      }
    };
  } else {
    // Low / Calm weather
    demoData = {
      location: loc,
      resolved_address: `${loc} Observatory, Karnataka (Stable Weather Simulation)`,
      latitude: lat,
      longitude: lon,
      is_karnataka: true,
      warning: null,
      timestamp: nowTime,
      telemetry: {
        temp: 27.5,
        humidity: 62.0,
        dew: 19.5,
        dpd: 8.0,
        vpd: 1.8,
        pressure: 1012.0,
        pressure_drop: 0.2,
        windspeed: 8.5,
        winddir: 180,
        cloudcover: 15.0,
        conditions: "Clear & Stable Atmosphere"
      },
      prediction: {
        convective_probability: 16.5,
        binary_prediction: 0,
        risk_level: "LOW (Stable Boundary Layer)",
        alert_code: "GREEN",
        weather_condition: "Calm & Stable Weather",
        model_source: "Soft Voting Ensemble GBDT (Karnataka Calibrated)",
        is_available: true
      },
      timeline: [
        { label: "+30 Mins Later", time_label: "+30m Projection", time_str: "+30m", temp: 27.2, humidity: 64, cloudcover: 15, conditions: "Clear Sky", probability: 15.0, windspeed: 8.0, alert_code: "GREEN" },
        { label: "+60 Mins Later", time_label: "+60m Projection", time_str: "+60m", temp: 26.8, humidity: 66, cloudcover: 20, conditions: "Scattered Clouds", probability: 17.5, windspeed: 7.5, alert_code: "GREEN" },
        { label: "+90 Mins Later", time_label: "+90m Projection", time_str: "+90m", temp: 26.2, humidity: 68, cloudcover: 20, conditions: "Stable Airflow", probability: 16.0, windspeed: 6.8, alert_code: "GREEN" }
      ],
      micro_zones: [
        { name: `${loc} Main`, lat: lat, lon: lon, probability: 16.5, temp: 27.5, humidity: 62 }
      ],
      gemini_advisory: {
        status: "success",
        model: "Gemini AI + Karnataka Convective Ensemble (Stable Simulation)",
        synoptic_bulletin: `Atmospheric boundary layer over ${loc} exhibits stable thermodynamic stratification. Dew point depression (8.0°C) and steady barometric pressure indicate negligible convective initiation potential. Clear sky conditions prevailing.`,
        ai_risk_assessment: "LOW",
        agriculture_advisory: "Ideal dry weather conditions for plantation fieldwork, pesticide spraying, and crop processing.",
        travel_safety_advisory: "Dry road surfaces and optimal visibility across all regional transport routes.",
        aviation_outdoor_warning: "Calm surface winds and unrestricted visibility. Perfect conditions for outdoor operations."
      },
      thunderstorm_alert: {
        status: "active",
        level: "LOW",
        probability: 16.5,
        location: loc,
        lead_time: "+30 to +90 Mins",
        headline: "Low thunderstorm risk. Calm and stable weather expected across the region.",
        explanation: `Boundary-layer thermodynamic energy over ${loc} is stable. Convective storm initiation is not expected within the forecast window.`,
        timestamp: new Date().toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit', hour12: true }) + ' IST (Simulation)'
      }
    };
  }

  // Render simulated scenario across all dashboard components
  renderDashboard(demoData);
}

let isPresentationDemoActive = false;

const NAV_STORM_SVG_IDLE = '<svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.3" stroke-linecap="round" stroke-linejoin="round"><polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"></polygon></svg>';
const NAV_STORM_SVG_ACTIVE = '<svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.3" stroke-linecap="round" stroke-linejoin="round"><path d="M3 12a9 9 0 0 1 9-9 9.75 9.75 0 0 1 6.74 2.74L21 8"></path><path d="M21 3v5h-5"></path><path d="M21 12a9 9 0 0 1-9 9 9.75 9.75 0 0 1-6.74-2.74L3 16"></path><path d="M8 16H3v5"></path></svg>';

/**
 * Single-button navbar toggle for thunderstorm simulation & live reset
 */
function togglePresentationDemo() {
  const btnText = document.getElementById('navStormAlertText');
  const navBtn = document.getElementById('btnNavStormAlert');

  if (isPresentationDemoActive) {
    isPresentationDemoActive = false;
    if (btnText) btnText.innerHTML = NAV_STORM_SVG_IDLE;
    if (navBtn) {
      navBtn.classList.remove('active-demo');
      navBtn.title = 'Toggle Severe Thunderstorm Alert Simulation (88.5%)';
    }
    restoreLiveTelemetry();
  } else {
    isPresentationDemoActive = true;
    if (btnText) btnText.innerHTML = NAV_STORM_SVG_ACTIVE;
    if (navBtn) {
      navBtn.classList.add('active-demo');
      navBtn.title = 'Reset to Live Nowcast Radar & Telemetry';
    }
    triggerPresentationDemo('critical');
  }
}

/**
 * Restore Live Telemetry from Open-Meteo & Gemini AI
 */
function restoreLiveTelemetry() {
  isPresentationDemoActive = false;
  const btnText = document.getElementById('navStormAlertText');
  const navBtn = document.getElementById('btnNavStormAlert');
  if (btnText) btnText.innerHTML = NAV_STORM_SVG_IDLE;
  if (navBtn) {
    navBtn.classList.remove('active-demo');
    navBtn.title = 'Toggle Severe Thunderstorm Alert Simulation (88.5%)';
  }

  const liveBtn = document.getElementById('btnRestoreLive');
  if (liveBtn) liveBtn.style.display = 'none';

  lastThunderstormAlertSig = null;

  // Immediately close and dismiss floating storm toast
  if (typeof window.closeStormToast === 'function') {
    window.closeStormToast();
  } else {
    closeStormToast();
  }

  // Deactivate active alert on server/database so other clients stop receiving it
  try {
    fetch('/api/alerts/deactivate', { method: 'POST' }).catch(() => {});
  } catch (e) {}

  fetchNowcast(currentLocation || 'Puttur');
}


/* ==========================================================================
   Automated Thunderstorm SMS & Email Emergency Broadcast Controller
   ========================================================================== */

/**
 * Automatically broadcasts thunderstorm alert to registered citizens via Email & SMS
 * without requiring the user or meteorologist to press any button.
 */
let lastAutoDispatchedSig = null;

function autoBroadcastThunderstormAlert(alertObj) {
  if (!alertObj || !alertObj.level || alertObj.level === 'LOW' || alertObj.level === 'NONE') return;

  // The backend (/api/nowcast and /api/demo/thunderstorm) already handles the server-side dispatch.
  // We simply update the toast UI to reflect live emergency broadcast status without double-dispatching.
  const timeEl = document.getElementById('toastTime');
  if (timeEl) {
    timeEl.innerHTML = (alertObj.lead_time || '+30m') + ' &bull; <strong style="color: #2e7d32;">⚡ Alert Auto-Sent to Citizens</strong>';
  }
}

/**
 * Open the Thunderstorm Alert Dispatch Modal
 */
function openDispatchModal() {
  const modal = document.getElementById('notificationDispatchModal');
  if (!modal) return;

  // Ensure an alert object is available
  if (!currentActiveAlert || currentActiveAlert.status === 'unavailable') {
    const inputEl = document.getElementById('locationInput');
    const loc = (inputEl && inputEl.value.trim()) ? inputEl.value.trim() : (currentLocation || 'Puttur');
    currentActiveAlert = {
      status: 'active',
      level: 'CRITICAL',
      probability: 88.5,
      location: loc,
      lead_time: '+30m Projection',
      headline: 'High thunderstorm risk detected. Avoid exposed outdoor areas and monitor official weather warnings.',
      explanation: `Critical convective atmospheric instability observed across ${loc}. Intense lightning, heavy downbursts, and gusty winds anticipated.`,
      timestamp: new Date().toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit', second: '2-digit', hour12: true }) + ' IST'
    };
  }

  // Populate Summary Box
  const lvlEl = document.getElementById('notifModalLevel');
  const probEl = document.getElementById('notifModalProb');
  const leadEl = document.getElementById('notifModalLead');
  const locEl = document.getElementById('notifModalLocation');
  const headEl = document.getElementById('notifModalHeadline');
  const summaryBox = document.getElementById('notifAlertSummaryBox');

  const lvl = (currentActiveAlert.level || 'CRITICAL').toUpperCase();
  if (lvlEl) {
    lvlEl.textContent = `${lvl} ALERT`;
    lvlEl.className = `notif-badge-level level-${lvl.toLowerCase()}`;
  }
  if (summaryBox) {
    summaryBox.className = `notif-alert-summary-box summary-${lvl.toLowerCase()}`;
  }
  if (probEl) {
    const p = currentActiveAlert.probability;
    probEl.textContent = (p !== null && p !== undefined) ? `${Number(p).toFixed(1)}% Storm Risk` : 'High Risk';
  }
  if (leadEl) {
    leadEl.textContent = `⏱️ ${currentActiveAlert.lead_time || '+30m Projection'}`;
  }
  if (locEl) {
    locEl.textContent = `📍 Affected Locality: ${currentActiveAlert.location || 'Karnataka'}`;
  }
  if (headEl) {
    headEl.textContent = currentActiveAlert.headline || 'Convective storm warning active.';
  }

  modal.style.display = 'flex';
}

/**
 * Close Dispatch Modal
 */
function closeDispatchModal() {
  const modal = document.getElementById('notificationDispatchModal');
  if (modal) modal.style.display = 'none';
}

/**
 * Handle clicks outside modal content to dismiss
 */
function handleModalBackdropClick(event) {
  if (event.target.id === 'notificationDispatchModal') {
    closeDispatchModal();
  }
}

/**
 * Execute Emergency Broadcast via SMS & Email APIs
 */
async function executeAlertBroadcast() {
  const chkSms = document.getElementById('chkChannelSms');
  const chkEmail = document.getElementById('chkChannelEmail');
  const btn = document.getElementById('btnExecuteDispatch');
  const btnText = document.getElementById('btnExecuteText');

  const chkTelegram = document.getElementById('chkChannelTelegram');
  const channels = [];
  if (chkSms && chkSms.checked) channels.push('sms');
  if (chkEmail && chkEmail.checked) channels.push('email');
  if (chkTelegram && chkTelegram.checked) channels.push('telegram');

  if (channels.length === 0) {
    alert('Please select at least one broadcast channel (Telegram, Email, or SMS).');
    return;
  }

  if (btn) btn.disabled = true;
  if (btnText) btnText.textContent = 'Transmitting Emergency Alerts to Citizens...';

  try {
    const payload = {
      location: currentActiveAlert?.location || currentLocation || 'Puttur',
      probability: currentActiveAlert?.probability ?? 88.5,
      level: currentActiveAlert?.level || 'CRITICAL',
      lead_time: currentActiveAlert?.lead_time || '+30m Projection',
      headline: currentActiveAlert?.headline || 'High thunderstorm risk detected.',
      explanation: currentActiveAlert?.explanation || 'Severe convective atmospheric instability observed.',
      channels: channels,
      force: true
    };

    const resp = await fetch('/api/notifications/dispatch', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(payload)
    });

    const data = await resp.json();

    if (!resp.ok || !data.success) {
      alert(`Dispatch Error: ${data.error || 'Could not broadcast alerts.'}`);
      return;
    }

    // Render results into table
    renderDispatchResults(data.dispatches || [], data.mode);

  } catch (err) {
    console.error('executeAlertBroadcast failed:', err);
    alert(`Dispatch failed: ${err.message}`);
  } finally {
    if (btn) btn.disabled = false;
    if (btnText) btnText.textContent = 'Broadcast Alerts to All Target Citizens';
  }
}

/**
 * Render notification receipts into modal table
 */
function renderDispatchResults(dispatches, mode) {
  const area = document.getElementById('notifResultsArea');
  const tbody = document.getElementById('notifResultsTbody');
  const countBadge = document.getElementById('resultsCountBadge');
  const headerTitle = document.getElementById('resultsHeaderTitle');

  if (!area || !tbody) return;

  tbody.innerHTML = '';
  area.style.display = 'block';

  if (headerTitle) {
    headerTitle.textContent = mode === 'live'
      ? 'Live Transmission Receipts (Delivered & Logged):'
      : 'Transmission Receipts (MongoDB Recorded):';
  }

  if (countBadge) {
    countBadge.textContent = `${dispatches.length} citizens reached`;
  }

  if (dispatches.length === 0) {
    tbody.innerHTML = `<tr><td colspan="5" style="text-align:center; padding:16px; color:#82786f;">No target registered users found for this locality.</td></tr>`;
    return;
  }

  dispatches.forEach(d => {
    const tr = document.createElement('tr');

    const smsBadge = d.sms_status === 'sent'
      ? '<span class="status-badge status-sent">✓ Sent Live</span>'
      : (d.sms_status === 'simulated'
        ? '<span class="status-badge status-simulated">⚡ Simulation Logged</span>'
        : (d.sms_status === 'skipped' ? '<span class="status-badge status-skipped">Skipped</span>' : '<span class="status-badge status-failed">Failed</span>'));

    const emailBadge = d.email_status === 'sent'
      ? '<span class="status-badge status-sent">✓ Sent Live</span>'
      : (d.email_status === 'simulated'
        ? '<span class="status-badge status-simulated">✉️ Simulation Logged</span>'
        : (d.email_status === 'skipped' ? '<span class="status-badge status-skipped">Skipped</span>' : '<span class="status-badge status-failed">Failed</span>'));

    tr.innerHTML = `
      <td>
        <div class="recipient-name">${d.username || 'Citizen'}</div>
        <div class="recipient-meta">${d.email || ''} &bull; +91 ${d.mobile || ''}</div>
      </td>
      <td><span class="locality-chip">${d.locality || d.alert_location || 'Karnataka'}</span></td>
      <td>${smsBadge}</td>
      <td>${emailBadge}</td>
      <td class="time-col">${d.timestamp_display || 'Just now'}</td>
    `;
    tbody.appendChild(tr);
  });
}

/**
 * Fetch and display notification history from MongoDB
 */
async function fetchAndShowHistory() {
  openDispatchModal();
  const area = document.getElementById('notifResultsArea');
  const tbody = document.getElementById('notifResultsTbody');
  const countBadge = document.getElementById('resultsCountBadge');
  const headerTitle = document.getElementById('resultsHeaderTitle');

  if (area) area.style.display = 'block';
  if (tbody) tbody.innerHTML = `<tr><td colspan="5" style="text-align:center; padding:18px; color:#82786f;">Loading alert history from MongoDB...</td></tr>`;

  try {
    const res = await fetch('/api/notifications/history?limit=15');
    const data = await res.json();

    if (!data.success) {
      if (tbody) tbody.innerHTML = `<tr><td colspan="5" style="text-align:center; padding:18px; color:#c62828;">Error loading history: ${data.error || 'Failed'}</td></tr>`;
      return;
    }

    if (headerTitle) headerTitle.textContent = 'Past Emergency Alert Dispatches (MongoDB Audit History):';
    if (countBadge) countBadge.textContent = `${data.count || data.history.length} records`;

    renderDispatchResults(data.history || [], 'history');
  } catch (err) {
    console.error('fetchAndShowHistory error:', err);
    if (tbody) tbody.innerHTML = `<tr><td colspan="5" style="text-align:center; padding:18px; color:#c62828;">Error fetching history: ${err.message}</td></tr>`;
  }
}

// Global ESC key listener to close modals
document.addEventListener('keydown', (e) => {
  if (e.key === 'Escape') {
    closeMicrozoneModal();
    if (typeof closeDispatchModal === 'function') closeDispatchModal();
  }
});
