# Optional GIS layers

Participants can overlay their own GIS data on the NISAR footprint —
GeoJSON, Shapefile, and GeoPackage all work, and whatever's supplied gets
reprojected to WGS84 for display.

No external boundary dataset is needed for the basic workflow; the
interactive map uses OpenStreetMap as its basemap out of the box.

For offline or reproducible figures, use the static footprint map
functions in `nisar_utils.mapping` instead of the interactive map.
