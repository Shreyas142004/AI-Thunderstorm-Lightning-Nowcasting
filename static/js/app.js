/**
 * AeroCast AI — Convective Nowcasting Frontend Engine
 * Handles real-time telemetry updates, interactive Leaflet Doppler radar,
 * free-form Karnataka place search, out-of-bounds warning alert, and Gemini AI synoptic advisory.
 */

// Global State
let currentTheme = localStorage.getItem('aerocast_theme') || 'light';
let currentLocation = 'Puttur';
let currentRadarCenter = [12.7667, 75.2016]; // Default Puttur coordinates

// Leaflet Map Handles
let radarMap = null;
let tileLayer = null;
let radarLayersGroup = null;
let stationMarkersGroup = null;


// Initialize Application
document.addEventListener('DOMContentLoaded', () => {
  setAppTheme(currentTheme);
  startLiveClock();
  initRadarMap();
  fetchNowcast(currentLocation);
});


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
      zoomControl: false,
      scrollWheelZoom: false,
      doubleClickZoom: false,
      touchZoom: false,
      boxZoom: false,
      keyboard: false,
      dragging: true,
      attributionControl: false,
      minZoom: 10,
      maxZoom: 10
    }).setView(currentRadarCenter, 10);

    // Apply theme tiles
    updateMapTiles();

    // Create persistent layer groups
    radarLayersGroup = L.layerGroup().addTo(radarMap);
    stationMarkersGroup = L.layerGroup().addTo(radarMap);

    // Force dimension check
    setTimeout(() => {
      if (radarMap) radarMap.invalidateSize();
    }, 200);
  } catch (err) {
    console.error("Error creating Leaflet radar map:", err);
  }
}


/**
 * Update Leaflet Map Tile Theme
 */
function updateMapTiles() {
  if (!radarMap || typeof L === 'undefined') return;

  if (tileLayer) {
    try { radarMap.removeLayer(tileLayer); } catch (e) {}
  }

  const isDark = (currentTheme === 'dark');
  // OpenStreetMap for Light Theme (rich topography, towns & boundaries, 100% free, no API key)
  // ESRI World Dark Gray Canvas for Espresso Dark Theme
  const tileUrl = isDark
    ? 'https://server.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Dark_Gray_Base/MapServer/tile/{z}/{y}/{x}'
    : 'https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png';

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

  // Smooth fly to new station location (zoom 10 if in Karnataka, zoom 7 if outside so the user sees real geographical location)
  radarMap.flyTo([lat, lon], isKarnataka ? 10 : 7, { duration: 1.2 });

  if (radarLayersGroup) radarLayersGroup.clearLayers();
  if (stationMarkersGroup) stationMarkersGroup.clearLayers();

  const hasProb = isKarnataka && (probability !== null && probability !== undefined);
  const prob = hasProb ? parseFloat(probability) : 0;

  // 1. Concentric S-Band Doppler Radar Range Rings (ONLY if inside Karnataka)
  if (isKarnataka) {
    const ringColor = hasProb
      ? (prob >= 70 ? 'rgba(217, 83, 79, 0.45)' : (prob >= 35 ? 'rgba(229, 169, 60, 0.45)' : 'rgba(94, 140, 104, 0.45)'))
      : 'rgba(160, 150, 140, 0.35)';

    L.circle([lat, lon], {
      radius: 25000,
      color: ringColor,
      weight: 1.5,
      dashArray: '4, 4',
      fill: false
    }).bindTooltip("25 km Range", { permanent: false, direction: "top" }).addTo(radarLayersGroup);

    L.circle([lat, lon], {
      radius: 50000,
      color: ringColor,
      weight: 1.2,
      dashArray: '6, 6',
      fill: false
    }).bindTooltip("50 km Range", { permanent: false, direction: "top" }).addTo(radarLayersGroup);

    L.circle([lat, lon], {
      radius: 100000,
      color: ringColor,
      weight: 1.0,
      dashArray: '8, 8',
      fill: false
    }).bindTooltip("100 km S-Band Max Scan", { permanent: false, direction: "top" }).addTo(radarLayersGroup);
  }

  // 2. Simulated Convective Reflectivity Intensity Contours (ONLY if inside Karnataka & has probability)
  if (hasProb) {
    if (prob >= 25.0) {
      // Outer convective envelope (Sage/Honey: ~35 dBZ)
      L.circle([lat, lon], {
        radius: 18000,
        color: '#5E8C68',
        fillColor: '#5E8C68',
        fillOpacity: 0.22,
        weight: 1.2
      }).addTo(radarLayersGroup);

      // Mid convective cell (Honey: ~45 dBZ)
      L.circle([lat + 0.03, lon - 0.02], {
        radius: 11000,
        color: '#E5A93C',
        fillColor: '#E5A93C',
        fillOpacity: 0.35,
        weight: 1.2
      }).addTo(radarLayersGroup);
    }

    if (prob >= 60.0) {
      // Severe Convective Core (Terracotta / Crimson: 55-65 dBZ)
      L.circle([lat + 0.015, lon - 0.01], {
        radius: 6500,
        color: '#D9534F',
        fillColor: '#D9534F',
        fillOpacity: 0.55,
        weight: 1.8
      }).addTo(radarLayersGroup);
    }
  }

  // 3. Focal Station Marker
  const mainDotClass = hasProb
    ? (prob >= 70 ? 'pin-dot-red' : (prob >= 35 ? 'pin-dot-amber' : 'pin-dot-green'))
    : 'pin-dot-neutral';
  const labelText = hasProb ? `${locationName} (${prob.toFixed(1)}%)` : `${locationName} (Outside KA)`;

  const focalIcon = L.divIcon({
    className: 'leaflet-radar-marker',
    html: `
      <div class="radar-station-blip" style="border: 2px solid ${hasProb && prob >= 70 ? 'var(--accent-terracotta)' : 'var(--card-border)'}; box-shadow: 0 4px 16px rgba(0,0,0,0.25);">
        <span class="pin-dot ${mainDotClass}"></span>
        <span>${labelText}</span>
      </div>
    `,
    iconSize: [160, 34],
    iconAnchor: [80, 17]
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
        const angles = [0.4, 2.0, 3.6, 5.2];
        const angle = angles[idx % angles.length];
        zLat = lat + (0.11 * Math.cos(angle));
        zLon = lon + (0.13 * Math.sin(angle));
      }

      // Check distance from focal point (if under ~2.5 km, nudge outwards to prevent label overlap)
      const distFromCenter = Math.hypot(zLat - lat, zLon - lon);
      if (distFromCenter < 0.02) {
        if (zLat >= lat) zLat += 0.032;
        else zLat -= 0.032;
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
        iconSize: [100, 24],
        iconAnchor: [50, 12]
      });

      L.marker([zLat, zLon], { icon: subIcon, zIndexOffset: 800 })
        .bindPopup(`
          <div style="font-family: inherit; font-size: 0.82rem; line-height: 1.4;">
            <strong>${zone.name}</strong><br>
            <span style="color: var(--text-muted);">Zone Convective Risk:</span> 
            <strong style="color: ${zProb >= 70 ? 'var(--accent-terracotta)' : (zProb >= 35 ? 'var(--accent-honey)' : 'var(--accent-sage)')};">${zProb.toFixed(1)}%</strong>
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
    radarMap.flyTo(currentRadarCenter, 10, { duration: 0.8 });
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
 * Free-Form Location Search Handler
 */
function handleLocationSearch(event) {
  if (event) event.preventDefault();
  const inputEl = document.getElementById('locationInput');
  const query = inputEl ? inputEl.value.trim() : '';

  if (!query) {
    if (inputEl) inputEl.focus();
    return;
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

  // 5. Update Interactive Leaflet Doppler Radar Map
  updateRadarMap(data.latitude, data.longitude, data.location, hasProb ? pred.convective_probability : null, data.micro_zones, isKa);

  // 5b. Update Places & Micro-Zones Panel on the Right of the Radar Map
  renderPlacesDetails(data);

  // 6. 3-Step Timeline Progression
  renderTimelineTrack(timeItems, hasProb);

  // 7. Gemini AI Meteorological Advisory
  renderGeminiAdvisory(gemini);
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
    const zProb = parseFloat(zone.probability || prob);
    const pillClass = zProb >= 70 ? 'risk-pill-red' : (zProb >= 35 ? 'risk-pill-amber' : 'risk-pill-green');
    const zTemp = zone.temp ? `${zone.temp.toFixed(1)}°C` : `${(data.telemetry?.temp || 26.5).toFixed(1)}°C`;
    const zHum = zone.humidity ? `${zone.humidity.toFixed(0)}% Hum` : `${(data.telemetry?.humidity || 85).toFixed(0)}% Hum`;

    const row = document.createElement('div');
    row.className = 'place-item-card';
    row.title = `Click to pan radar to ${zone.name}`;
    row.innerHTML = `
      <div class="place-item-info">
        <span class="place-item-name">${zone.name}</span>
        <span class="place-item-sub">${zTemp} • ${zHum}</span>
      </div>
      <span class="place-item-risk ${pillClass}">${zProb.toFixed(1)}%</span>
    `;

    // Click to focus or pan
    row.addEventListener('click', () => {
      if (radarMap) {
        const destLat = zone.lat || data.latitude;
        const destLon = zone.lon || data.longitude;
        if (destLat && destLon) {
          radarMap.panTo([destLat, destLon], { duration: 0.6 });
        }
      }
    });

    listBody.appendChild(row);
  });
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
