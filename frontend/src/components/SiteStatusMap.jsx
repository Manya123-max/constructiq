import React, { useState, useEffect } from 'react'
import { useStore } from '../store/useStore'

// Indian Basin & River Geocoding GIS Coordinates Registry
const BASIN_GEO_REGISTRY = {
  // Ganga Basin & Sub-basins
  'Ganga Basin': { lat: 30.3753, lng: 78.4744, bbox: '77.5,29.5,79.5,31.2', basin: 'Ganga Basin (Uttarakhand)' },
  'Alaknanda River': { lat: 30.5600, lng: 79.1600, bbox: '78.5,30.0,79.8,31.0', basin: 'Alaknanda Valley Basin' },
  'Bhagirathi River': { lat: 30.9800, lng: 78.9300, bbox: '78.3,30.4,79.5,31.5', basin: 'Bhagirathi Catchment Basin' },
  'Yamuna Basin': { lat: 31.0100, lng: 78.4500, bbox: '77.8,30.2,79.0,31.4', basin: 'Upper Yamuna Basin' },
  'Mandakini River': { lat: 30.7300, lng: 79.0600, bbox: '78.8,30.4,79.4,31.0', basin: 'Mandakini Hydro Regime' },

  // Sutlej & Indus Basins
  'Sutlej River Basin': { lat: 31.4200, lng: 77.6500, bbox: '77.0,30.8,78.5,32.0', basin: 'Sutlej River Basin (Himachal)' },
  'Beas River Basin': { lat: 31.9500, lng: 77.1500, bbox: '76.5,31.2,77.8,32.4', basin: 'Beas Alpine Basin' },
  'Ravi River Basin': { lat: 32.5500, lng: 76.1200, bbox: '75.5,32.0,76.8,33.0', basin: 'Ravi River Basin' },
  'Chenab River Basin': { lat: 33.1500, lng: 75.3200, bbox: '74.8,32.5,76.2,34.0', basin: 'Chenab High-Head Basin (J&K)' },
  'Jhelum River Basin': { lat: 34.0800, lng: 74.8000, bbox: '74.2,33.5,75.5,34.5', basin: 'Jhelum River Basin' },
  'Indus River Basin': { lat: 34.1526, lng: 77.5771, bbox: '76.5,33.2,78.5,35.0', basin: 'Upper Indus Basin (Ladakh)' },
  'Zanskar River Basin': { lat: 33.7800, lng: 76.9200, bbox: '76.2,33.2,77.5,34.2', basin: 'Zanskar Trans-Himalayan Basin' },

  // Brahmaputra, Siang, Subansiri, Teesta
  'Subansiri River Basin': { lat: 27.8500, lng: 94.2000, bbox: '93.5,27.0,95.2,28.5', basin: 'Subansiri Basin (Arunachal)' },
  'Siang River Basin': { lat: 28.1000, lng: 95.0500, bbox: '94.2,27.5,95.8,29.0', basin: 'Siang / Brahmaputra Basin' },
  'Dibang River Basin': { lat: 28.2500, lng: 95.8500, bbox: '95.2,27.8,96.5,29.0', basin: 'Dibang Ultra-Large Basin' },
  'Kameng River Basin': { lat: 27.3200, lng: 92.6500, bbox: '92.0,26.8,93.2,28.0', basin: 'Kameng River Basin' },
  'Teesta River Basin': { lat: 27.5330, lng: 88.5122, bbox: '88.0,27.0,89.0,28.0', basin: 'Teesta Alpine Basin (Sikkim)' },
  'Rangeet River Basin': { lat: 27.1800, lng: 88.3000, bbox: '88.0,27.0,88.6,27.5', basin: 'Rangeet Sub-Basin' },
  'Brahmaputra Basin': { lat: 26.2006, lng: 92.9376, bbox: '91.5,25.5,94.0,27.5', basin: 'Brahmaputra Mainstem Basin' },
  'Kopili River Basin': { lat: 25.5788, lng: 91.8933, bbox: '90.5,25.0,92.5,26.0', basin: 'Kopili River Basin' },

  // Peninsular Basins
  'Periyar River Basin': { lat: 9.8517, lng: 76.9744, bbox: '76.2,9.2,77.5,10.5', basin: 'Periyar Hydro System (Kerala)' },
  'Chalakkudy River Basin': { lat: 10.3000, lng: 76.6500, bbox: '76.2,10.0,77.0,10.6', basin: 'Chalakkudy Western Ghats Basin' },
  'Sharavathi River Basin': { lat: 14.2000, lng: 74.8000, bbox: '74.2,13.8,75.8,14.8', basin: 'Sharavathi Valley Basin (Karnataka)' },
  'Cauvery River Basin': { lat: 12.3000, lng: 76.6000, bbox: '75.8,11.8,77.5,12.8', basin: 'Cauvery River Basin' },
  'Godavari River Basin': { lat: 18.7000, lng: 79.5000, bbox: '78.5,17.5,80.5,19.5', basin: 'Godavari Major Basin (Telangana/AP)' },
  'Krishna River Basin': { lat: 16.0886, lng: 78.8953, bbox: '78.0,15.2,79.8,16.8', basin: 'Krishna River Basin (AP)' },
  'Koyna River Basin': { lat: 17.3986, lng: 73.7431, bbox: '73.0,16.5,75.0,18.5', basin: 'Koyna Complex (Maharashtra)' },
  'Narmada River Basin': { lat: 21.8133, lng: 73.7483, bbox: '72.5,21.0,74.5,22.8', basin: 'Narmada River Basin (MP/Gujarat)' },
  'Mahanadi Basin': { lat: 19.8135, lng: 85.8312, bbox: '84.0,19.0,86.5,21.0', basin: 'Mahanadi Basin (Odisha)' },
}

// Fallback State Geocoding
const STATE_COORDINATES = {
  'Uttarakhand': BASIN_GEO_REGISTRY['Ganga Basin'],
  'Himachal Pradesh': BASIN_GEO_REGISTRY['Sutlej River Basin'],
  'Jammu & Kashmir': BASIN_GEO_REGISTRY['Chenab River Basin'],
  'Ladakh': BASIN_GEO_REGISTRY['Indus River Basin'],
  'Sikkim': BASIN_GEO_REGISTRY['Teesta River Basin'],
  'Arunachal Pradesh': BASIN_GEO_REGISTRY['Subansiri River Basin'],
  'Assam': BASIN_GEO_REGISTRY['Brahmaputra Basin'],
  'Meghalaya': BASIN_GEO_REGISTRY['Kopili River Basin'],
  'Kerala': BASIN_GEO_REGISTRY['Periyar River Basin'],
  'Karnataka': BASIN_GEO_REGISTRY['Sharavathi River Basin'],
  'Maharashtra': BASIN_GEO_REGISTRY['Koyna River Basin'],
  'Andhra Pradesh': BASIN_GEO_REGISTRY['Krishna River Basin'],
  'Telangana': BASIN_GEO_REGISTRY['Godavari River Basin'],
  'Odisha': BASIN_GEO_REGISTRY['Mahanadi Basin'],
  'Madhya Pradesh': BASIN_GEO_REGISTRY['Narmada River Basin'],
  'Gujarat': BASIN_GEO_REGISTRY['Narmada River Basin'],
  'West Bengal': BASIN_GEO_REGISTRY['Teesta River Basin']
}

export function SiteStatusMap({ compact = false }) {
  const estimationResult = useStore((s) => s.estimationResult)
  const googleApiKey = import.meta.env.VITE_GOOGLE_MAPS_API_KEY
  const mapboxToken = import.meta.env.VITE_MAPBOX_TOKEN

  const activeBasin = estimationResult?.project_inputs?.river_basin
  const activeState = estimationResult?.project_inputs?.state || 'Uttarakhand'
  const activeCap = estimationResult?.project_inputs?.capacity_mw || 250
  const activeType = estimationResult?.project_inputs?.project_type || 'run-of-river'

  const siteInfo = BASIN_GEO_REGISTRY[activeBasin]
    || STATE_COORDINATES[activeState]
    || BASIN_GEO_REGISTRY['Ganga Basin']

  return (
    <div
      style={{
        background: '#0F172A',
        borderRadius: '12px',
        color: '#FFFFFF',
        padding: compact ? '1rem' : '1.25rem',
        display: 'flex',
        flexDirection: 'column',
        gap: '12px',
        position: 'relative',
        minHeight: compact ? '240px' : '380px',
        overflow: 'hidden',
        boxShadow: '0 4px 16px rgba(15,23,42,0.15)'
      }}
    >
      {/* Map Header HUD */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', zIndex: 10 }}>
        <div>
          <div style={{ fontSize: '0.72rem', fontWeight: 800, letterSpacing: '0.08em', color: '#94A3B8', textTransform: 'uppercase' }}>
            SITE LOCATION MAP
          </div>
          <div style={{ fontSize: '0.95rem', fontWeight: 800, color: '#FFFFFF', marginTop: '2px' }}>
            {activeCap} MW {activeType} Hydro ({activeState})
          </div>
        </div>
      </div>

      {/* Embedded Dynamic Map Frame */}
      <div style={{ position: 'relative', width: '100%', height: compact ? '140px' : '220px', borderRadius: '8px', overflow: 'hidden', border: '1px solid #1E293B' }}>
        {googleApiKey ? (
          /* Option A: Google Maps Satellite View Embed */
          <iframe
            title="Google Maps Satellite View"
            width="100%"
            height="100%"
            frameBorder="0"
            src={`https://www.google.com/maps/embed/v1/place?key=${googleApiKey}&q=${siteInfo.lat},${siteInfo.lng}&maptype=satellite&zoom=11`}
            allowFullScreen
          />
        ) : mapboxToken ? (
          /* Option B: Mapbox GL View Embed */
          <iframe
            title="Mapbox Satellite View"
            width="100%"
            height="100%"
            frameBorder="0"
            src={`https://api.mapbox.com/styles/v1/mapbox/satellite-v9/html?access_token=${mapboxToken}#11/${siteInfo.lat}/${siteInfo.lng}`}
          />
        ) : (
          /* Option C: OpenStreetMap Dynamic Geocoded View (No API Key Required) */
          <iframe
            title="OpenStreetMap Geocoded View"
            width="100%"
            height="100%"
            frameBorder="0"
            scrolling="no"
            marginHeight="0"
            marginWidth="0"
            src={`https://www.openstreetmap.org/export/embed.html?bbox=${siteInfo.bbox}&layer=mapnik&marker=${siteInfo.lat},${siteInfo.lng}`}
            style={{ filter: 'invert(90%) hue-rotate(180deg) brightness(85%) contrast(120%)' }}
          />
        )}

        {/* Dynamic Telemetry Badge HUD */}
        <div
          style={{
            position: 'absolute',
            bottom: '8px',
            left: '8px',
            background: 'rgba(15, 23, 42, 0.85)',
            backdropFilter: 'blur(4px)',
            padding: '4px 10px',
            borderRadius: '6px',
            fontSize: '0.7rem',
            fontWeight: 700,
            color: '#00E676',
            border: '1px solid rgba(0, 230, 118, 0.3)',
            display: 'flex',
            alignItems: 'center',
            gap: '6px'
          }}
        >
          <span>📡</span> GIS GPS Target: {siteInfo.lat}° N, {siteInfo.lng}° E
        </div>
      </div>

      {/* State Geocoding Indicator */}
      <div style={{ fontSize: '0.75rem', color: '#94A3B8', borderTop: '1px solid #1E293B', paddingTop: '8px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <span><strong>Basin:</strong> {siteInfo.basin}</span>
        <span style={{ color: '#00E5FF', fontWeight: 700 }}>
          {googleApiKey ? 'Google Maps API Active' : mapboxToken ? 'Mapbox API Active' : 'OpenStreetMap GIS Engine'}
        </span>
      </div>
    </div>
  )
}
