"use client"

import { useEffect, useRef, useState } from "react"
import * as d3 from "d3"

interface RotatingEarthProps {
  width?: number
  height?: number
  className?: string
}

type Feature = GeoJSON.Feature<GeoJSON.Polygon | GeoJSON.MultiPolygon>

export default function RotatingEarth({ width = 800, height = 600, className = "" }: RotatingEarthProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const canvas = canvasRef.current
    if (!canvas) return
    const context = canvas.getContext("2d")
    if (!context) return

    const viewportWidth = Math.max(280, window.innerWidth - 32)
    const viewportHeight = Math.max(320, window.innerHeight - 140)
    const containerWidth = Math.min(width, viewportWidth)
    const containerHeight = Math.min(height, viewportHeight)
    const radius = Math.min(containerWidth, containerHeight) / 2.5
    const dpr = Math.min(window.devicePixelRatio || 1, 1.5)
    canvas.width = containerWidth * dpr
    canvas.height = containerHeight * dpr
    canvas.style.width = `${containerWidth}px`
    canvas.style.height = `${containerHeight}px`
    context.scale(dpr, dpr)

    const dark = document.documentElement.getAttribute("data-theme") === "dark"
    const ink = dark ? "#e6e6e6" : "#000000"
    const dot = dark ? "#777777" : "#999999"
    const projection = d3.geoOrthographic().scale(radius).translate([containerWidth / 2, containerHeight / 2]).clipAngle(90)
    const path = d3.geoPath().projection(projection).context(context)
    const rotation: [number, number] = [0, 0]
    let landFeatures: Feature[] = []
    const allDots: [number, number][] = []

    const pointInPolygon = ([x, y]: [number, number], polygon: number[][]) => {
      let inside = false
      for (let i = 0, j = polygon.length - 1; i < polygon.length; j = i++) {
        const [xi, yi] = polygon[i], [xj, yj] = polygon[j]
        if (yi > y !== yj > y && x < ((xj - xi) * (y - yi)) / (yj - yi) + xi) inside = !inside
      }
      return inside
    }

    const pointInFeature = ([lng, lat]: [number, number], feature: Feature) => {
      const geometry = feature.geometry
      const polygons = geometry.type === "Polygon" ? [geometry.coordinates] : geometry.coordinates
      return polygons.some((polygon) => pointInPolygon([lng, lat], polygon[0]) && !polygon.slice(1).some((ring) => pointInPolygon([lng, lat], ring)))
    }

    const render = () => {
      context.clearRect(0, 0, containerWidth, containerHeight)
      const scale = projection.scale()
      context.beginPath()
      context.arc(containerWidth / 2, containerHeight / 2, scale, 0, Math.PI * 2)
      context.fillStyle = dark ? "#000000" : "#e6e6e6"
      context.fill()
      context.strokeStyle = ink
      context.lineWidth = 1.5
      context.stroke()
      if (!landFeatures.length) return
      context.beginPath(); path(d3.geoGraticule()())
      context.strokeStyle = ink; context.globalAlpha = 0.2; context.lineWidth = 1; context.stroke(); context.globalAlpha = 1
      context.beginPath(); landFeatures.forEach((feature) => path(feature))
      context.strokeStyle = ink; context.lineWidth = 1; context.stroke()
      allDots.forEach(([lng, lat]) => {
        const point = projection([lng, lat])
        if (!point) return
        context.beginPath(); context.arc(point[0], point[1], 1.05, 0, Math.PI * 2); context.fillStyle = dot; context.fill()
      })
    }

    const load = async () => {
      try {
        const response = await fetch("https://raw.githubusercontent.com/martynafford/natural-earth-geojson/refs/heads/master/110m/physical/ne_110m_land.json", { cache: "force-cache" })
        if (!response.ok) throw new Error("Failed to load land data")
        const data = await response.json() as GeoJSON.FeatureCollection<GeoJSON.Polygon | GeoJSON.MultiPolygon>
        landFeatures = data.features
        for (const feature of landFeatures) {
          const [[minLng, minLat], [maxLng, maxLat]] = d3.geoBounds(feature)
          const dotSpacing = containerWidth < 480 ? 1.9 : 1.5
          for (let lng = minLng; lng <= maxLng; lng += dotSpacing) for (let lat = minLat; lat <= maxLat; lat += dotSpacing) {
            if (pointInFeature([lng, lat], feature)) allDots.push([lng, lat])
          }
        }
        render()
      } catch { setError("Failed to load land map data") }
    }

    const timer = d3.timer(() => { rotation[0] += 0.5; projection.rotate(rotation); render() })
    const onWheel = (event: WheelEvent) => { event.preventDefault(); projection.scale(Math.max(radius * 0.5, Math.min(radius * 2.5, projection.scale() * (event.deltaY > 0 ? 0.9 : 1.1)))); render() }
    canvas.addEventListener("wheel", onWheel, { passive: false })
    load()
    return () => { timer.stop(); canvas.removeEventListener("wheel", onWheel) }
  }, [width, height])

  return <div className={`relative ${className}`} aria-label="Rotating dotted wireframe globe">
    {error ? <p className="p-8 text-center text-sm text-muted-foreground">{error}</p> : <canvas ref={canvasRef} className="h-auto w-full" style={{ maxWidth: "100%" }} />}
  </div>
}
