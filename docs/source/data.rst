🌐 Data Sources
===============

List of Sources
----------------

The underlying data sources are a mix of:

- `3DEP <http://nationalmap.gov/elevation.html>`__ : Formerly NED and NED Topobathy in the United States, 10 meters outside of Alaska, 3 meters in select land and territorial water areas.
- `ArcticDEM <http://nga.maps.arcgis.com/apps/MapSeries/index.html?appid=cf2fba21df7540fb981f8836f2a97e25>`__ : Strips of 5 meter mosaics across all of the land north of 60° latitude, including Alaska, Canada, Greenland, Iceland, Norway, Russia, and Sweden.
- `CDEM <http://geogratis.gc.ca/api/en/nrcan-rncan/ess-sst/c40acfba-c722-4be1-862e-146b80be738e.html>`__ : Canadian Digital Elevation Model in Canada, with variable spatial resolution (from 20-400 meters) depending on the latitude.
- `data.gov.uk <http://environment.data.gov.uk/ds/survey/index.jsp#/survey>`__ : 2 meters over most of the United Kingdom.
- `data.gv.at <https://www.data.gv.at/katalog/dataset/b5de6975-417b-4320-afdb-eb2a9e2a1dbf>`__ : 10 meters over Austria.
- `ETOPO1 <https://www.ngdc.noaa.gov/mgg/global/global.html>`__ : For ocean bathymetry, 1 arc-minute resolution globally.
- `EUDEM <https://www.eea.europa.eu/data-and-maps/data/eu-dem#tab-original-data>`__ : In most of Europe at 30 meter resolution, including Albania, Austria, Belgium, Bosnia and Herzegovina, Bulgaria, Croatia, Cyprus, Czechia, Denmark, Estonia, Finland, France, Germany, Greece, Hungary, Iceland, Ireland, Italy, Kosovo, Latvia, Liechtenstein, Lithuania, Luxembourg, Macedonia, Malta, Montenegro, Netherlands, Norway, Poland, Portugal, Romania, Serbia, Slovakia, Slovenia, Spain, Sweden, Switzerland, and United Kingdom.
- `Geoscience Australia's DEM of Australia <https://ecat.ga.gov.au/geonetwork/srv/eng/search#!22be4b55-2465-4320-e053-10a3070a5236>`__ : 5 meters around coastal regions in South Australia, Victoria, and Northern Territory.
- `GMTED <http://topotools.cr.usgs.gov/gmted_viewer/>`__ : Globally, coarser resolutions at 7.5", 15", and 30" in land areas.
- `INEGI <http://en.www.inegi.org.mx/temas/mapas/relieve/continental/>`__ : Continental relief in Mexico.
- `Kartverket <http://data.kartverket.no/download/content/digital-terrengmodell-10-m-utm-33>`__ : Digital Terrain Model, 10 meters over Norway.
- `LINZ <https://data.linz.govt.nz/layer/1768-nz-8m-digital-elevation-model-2012/>`__ : 8 meters over New Zealand.
- `SRTM <https://lta.cr.usgs.gov/SRTM>`__: Globally except high latitudes, 30 meters (90 meters nominal quality) in land areas.

Data Sources per Zoom Level
----------------------------

+--------+---------------------+--------------------------------------------------+
| Zoom   | Ocean               | Land                                             |
+========+=====================+==================================================+
| **0**  | ETOPO1              | ETOPO1                                           |
+--------+---------------------+--------------------------------------------------+
| **1**  | ETOPO1              | ETOPO1                                           |
+--------+---------------------+--------------------------------------------------+
| **2**  | ETOPO1              | ETOPO1                                           |
+--------+---------------------+--------------------------------------------------+
| **3**  | ETOPO1              | ETOPO1                                           |
+--------+---------------------+--------------------------------------------------+
| **4**  | ETOPO1              | GMTED                                            |
+--------+---------------------+--------------------------------------------------+
| **5**  | ETOPO1              | GMTED                                            |
+--------+---------------------+--------------------------------------------------+
| **6**  | ETOPO1              | GMTED                                            |
+--------+---------------------+--------------------------------------------------+
| **7**  | ETOPO1              | SRTM, NRCAN in Canada, with GMTED above 60°      |
+--------+---------------------+--------------------------------------------------+
| **8**  | ETOPO1              | SRTM, NRCAN in Canada, with GMTED above 60°      |
+--------+---------------------+--------------------------------------------------+
| **9**  | ETOPO1              | SRTM, NRCAN in Canada, EUDEM in Europe,          |
|        |                     | with GMTED above 60°                             |
+--------+---------------------+--------------------------------------------------+
| **10** | ETOPO1, NED         | SRTM, data.gov.at in Austria, NRCAN in Canada,   |
|        | Topobathy in CA     | SRTM, NED/3DEP, data.gov.uk, ArcticDEM, LINZ,    |
|        |                     | Kartverket                                       |
+--------+---------------------+--------------------------------------------------+

.. note::

   Information about data sources is provided `here <https://github.com/tilezen/joerd/blob/master/docs/data-sources.md>`__.
