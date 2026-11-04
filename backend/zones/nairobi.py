"""
The 17 Nairobi sub-counties monitored by AFEWS.

IMPORTANT: elevation, drainage and the demo rainfall/water-level values are
working approximations for demonstration, not surveyed data. Elevation is a
rough average in metres above sea level and the coordinates are approximate
centres of each sub-county. Drainage quality is an assumption (higher for
areas with large informal settlements along the rivers). Edit any zone on the
Zones page to correct it.

Each row: name, wards, elevation_m, drainage, latitude, longitude,
          demo_rainfall_mm, demo_water_level_cm
"""
from .models import Zone

P, M, G = Zone.DrainageQuality.POOR, Zone.DrainageQuality.MODERATE, Zone.DrainageQuality.GOOD

NAIROBI_SUBCOUNTIES = [
    ("Westlands Sub-County", "Kitisuru, Parklands/Highridge, Karura, Kangemi, Mountain View", 1700, G, -1.2650, 36.8050, 20, 10),
    ("Dagoretti North Sub-County", "Kilimani, Kawangware, Gatina, Kileleshwa, Kabiro", 1750, M, -1.2830, 36.7600, 40, 25),
    ("Dagoretti South Sub-County", "Mutu-ini, Ngando, Riruta, Uthiru/Ruthimitu, Waithaka", 1780, M, -1.3020, 36.7350, 25, 15),
    ("Lang'ata Sub-County", "Karen, Nairobi West, Mugumo-ini, South C, Nyayo Highrise", 1690, G, -1.3350, 36.7600, 30, 15),
    ("Kibra Sub-County", "Laini Saba, Lindi, Makina, Woodley/Kenyatta Golf Course, Sarang'ombe", 1650, P, -1.3133, 36.7876, 140, 95),
    ("Roysambu Sub-County", "Githurai, Kahawa West, Zimmerman, Roysambu, Kahawa", 1600, M, -1.2100, 36.8900, 35, 20),
    ("Kasarani Sub-County", "Clay City, Mwiki, Kasarani, Njiru, Ruai", 1590, M, -1.2200, 36.9100, 45, 30),
    ("Ruaraka Sub-County", "Babadogo, Utalii, Mathare North, Lucky Summer, Korogocho", 1620, P, -1.2400, 36.8700, 100, 70),
    ("Embakasi South Sub-County", "Imara Daima, Kwa Njenga, Kwa Reuben, Pipeline, Kware", 1600, P, -1.3300, 36.8900, 90, 60),
    ("Embakasi North Sub-County", "Kariobangi North, Dandora Area I, II, III and IV", 1600, P, -1.2500, 36.8900, 60, 40),
    ("Embakasi Central Sub-County", "Kayole North, Kayole Central, Kayole South, Komarock, Matopeni", 1590, M, -1.2800, 36.9100, 30, 15),
    ("Embakasi East Sub-County", "Upper Savannah, Lower Savannah, Embakasi, Utawala, Mihango", 1580, M, -1.3000, 36.9500, 25, 10),
    ("Embakasi West Sub-County", "Umoja I, Umoja II, Mowlem, Kariobangi South", 1630, M, -1.2850, 36.8800, 35, 20),
    ("Makadara Sub-County", "Maringo/Hamza, Viwandani, Harambee, Makongeni", 1650, P, -1.3000, 36.8650, 70, 45),
    ("Kamukunji Sub-County", "Pumwani, Eastleigh North, Eastleigh South, Airbase, California", 1660, M, -1.2750, 36.8450, 30, 15),
    ("Starehe Sub-County", "Nairobi Central, Ngara, Pangani, Ziwani/Kariokor, Landimawe, Nairobi South", 1670, M, -1.2800, 36.8350, 25, 10),
    ("Mathare Sub-County", "Hospital, Mabatini, Huruma, Ngei, Mlango Kubwa, Kiamaiko", 1640, P, -1.2600, 36.8590, 120, 80),
]

# The four zones that the earlier demo data created. Replaced by the list above.
OLD_DEMO_ZONE_NAMES = ["Kibera - Gatwekera", "Mathare 4A", "Mukuru Kwa Njenga", "Kawangware"]
