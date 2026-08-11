import React, { useState, useEffect } from 'react'
import { useStore } from '../store/useStore'

// Indian State & Basin Geocoding Coordinates Registry
const STATE_COORDINATES = {
  'Uttarakhand': { lat: 30.3753, lng: 78.4744, bbox: '77.5,29.5,79.5,31.2', basin: 'Ganga Basin' },
  'Himachal Pradesh': { lat: 31.5644, lng: 77.9754, bbox: '77.0,30.8,78.8,32.2', basin: 'Sutlej / Indus Basin' },
  'Jammu & Kashmir': { lat: 33.3100, lng: 75.7700, bbox: '75.0,32.5,76.8,34.0', basin: 'Chenab / Jhelum Basin' },
  'Ladakh': { lat: 34.1526, lng: 77.5771, bbox: '76.5,33.2,78.5,35.0', basin: 'Indus Basin' },
  'Sikkim': { lat: 27.5330, lng: 88.5122, bbox: '88.0,27.0,89.0,28.0', basin: 'Teesta / Brahmaputra' },
  'Arunachal Pradesh': { lat: 27.5500, lng: 94.2600, bbox: '93.5,26.8,95.0,28.2', basin: 'Siang / Subansiri Basin' },
  'Assam': { lat: 26.2006, lng: 92.9376, bbox: '91.5,25.5,94.0,27.5', basin: 'Brahmaputra Basin' },
  'Meghalaya': { lat: 25.5788, lng: 91.8933, bbox: '90.5,25.0,92.5,26.0', basin: 'Kopili Basin' },
  'Kerala': { lat: 9.8517, lng: 76.9744, bbox: '76.2,9.2,77.5,10.5', basin: 'Periyar / West Flowing' },
  'Karnataka': { lat: 14.5204, lng: 75.7224, bbox: '74.5,13.5,76.8,15.5', basin: 'Sharavathi / Cauvery' },
  'Maharashtra': { lat: 17.3986, lng: 73.7431, bbox: '73.0,16.5,75.0,18.5', basin: 'Koyna / Krishna Basin' },
  'Andhra Pradesh': { lat: 16.0886, lng: 78.8953, bbox: '78.0,15.2,79.8,16.8', basin: 'Krishna / Godavari Basin' },
  'Telangana': { lat: 17.8496, lng: 79.1151, bbox: '78.0,17.0,80.0,18.8', basin: 'Godavari Basin' },
  'Odisha': { lat: 19.8135, lng: 85.8312, bbox: '84.0,19.0,86.5,21.0', basin: 'Mahanadi Basin' },
  'Madhya Pradesh': { lat: 22.9734, lng: 78.6569, bbox: '77.0,21.5,80.0,24.0', basin: 'Narmada Basin' },
  'Gujarat': { lat: 21.8133, lng: 73.7483, bbox: '72.5,21.0,74.5,22.8', basin: 'Narmada / Tapti Basin' },
  'West Bengal': { lat: 27.0410, lng: 88.2663, bbox: '87.5,26.5,89.0,27.5', basin: 'Teesta / Ganga Basin' }
}

export function SiteStatusMap({ compact = false }) {
  const estimationResult = useStore((s) => s.estimationResult)
  const googleApiKey = import.meta.env.VITE_GOOGLE_MAPS_API_KEY
  const mapboxToken = import.meta.env.VITE_MAPBOX_TOKEN

  const activeState = estimationResult?.project_inputs?.state || 'Uttarakhand'
  const activeCap = estimationResult?.project_inputs?.capacity_mw || 250
  const activeType = estimationResult?.project_inputs?.project_type || 'run-of-river'

  const siteInfo = STATE_COORDINATES[activeState] || STATE_COORDINATES['Uttarakhand']

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
