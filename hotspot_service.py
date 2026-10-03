"""
GIS Hotspot Prioritisation Service

Performs reproducible geographic hotspot prioritisation on the Laurent Lebreton et al. (2018)
oceanographic historical dataset extracted from Master_Project_Tableau.twbx.

Dataset Details:
    Source: Laurent Lebreton et al., Scientific Reports (2018)
    Coordinate System: WGS 84 (EPSG:4326) Decimal Degrees
    Coverage: Global oceans with primary density in the North Pacific Subtropical Gyre (GPGP)
    Temporal Range: 1972 to 2015
    Total Sample Records: 3,532 manta-trawl net survey tows
"""

import csv
import math
import os
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any

DATA_FILE_PATH = Path(__file__).parent / "data" / "lebreton2018_historical_dataset.csv"


class HotspotService:
    """
    Service for GIS Hotspot detection, prioritisation calculation, and spatial clustering.
    """

    def __init__(self, data_path: Optional[Path] = None):
        self.data_path = data_path or DATA_FILE_PATH
        self.observations: List[Dict[str, Any]] = []
        self._load_dataset()

    def _load_dataset(self) -> None:
        """Loads and parses raw CSV data into typed observations with priority scores."""
        if not self.data_path.exists():
            raise FileNotFoundError(f"Dataset not found at: {self.data_path}")

        records = []
        with open(self.data_path, "r", encoding="utf-8", errors="ignore") as f:
            reader = csv.DictReader(f)
            for row in reader:
                try:
                    lat_str = row.get("Latitude (degrees)", 0)
                    lon_str = row.get("Longitude (degrees)", 0)
                    if not lat_str or not lon_str:
                        continue
                    lat = float(lat_str)
                    lon = float(lon_str)

                    def to_int(v, default=0):
                        try:
                            return int(float(v or default))
                        except (ValueError, TypeError):
                            return default

                    def to_float(v, default=0.0):
                        try:
                            return float(v or default)
                        except (ValueError, TypeError):
                            return default

                    year = to_int(row.get("Sampling Year"))
                    month = to_int(row.get("Sampling Month"))
                    mass = to_float(row.get("Microplastic Mass Concentration (g/km)"))
                    num = to_float(row.get("Microplastic Numerical Concentration (#/km)"))
                    gpgp_str = str(row.get("Inside GPGP?", "0")).strip()
                    inside_gpgp = 1 if gpgp_str == "1" else 0
                    origin = str(row.get("Data Origin", "Unknown")).strip()
                    ref = str(row.get("Data Reference", "Unknown")).strip()
                    sample_id = str(row.get("#", "")).strip()

                    # Calculate deterministic Hotspot Priority Index (HPI)
                    hpi, tier = self._calculate_hpi(mass, num, inside_gpgp)

                    records.append({
                        "id": sample_id,
                        "latitude": round(lat, 4),
                        "longitude": round(lon, 4),
                        "year": year,
                        "month": month,
                        "mass_concentration_g_km2": round(mass, 2),
                        "numerical_concentration_km2": round(num, 2),
                        "inside_gpgp": inside_gpgp,
                        "origin": origin,
                        "reference": ref,
                        "priority_score": hpi,
                        "priority_tier": tier
                    })
                except (ValueError, TypeError):
                    continue

        self.observations = records

    @staticmethod
    def _calculate_hpi(mass: float, numerical: float, inside_gpgp: int) -> Tuple[float, str]:
        """
        Calculates the Hotspot Priority Index (HPI in [0, 100]).
        
        Formula:
            HPI = 0.55 * S_mass + 0.30 * S_gpgp + 0.15 * S_num
            
            S_mass: Log10 scaled mass concentration normalized against reference ceiling (5000 g/km²)
            S_gpgp: 100 if inside Great Pacific Garbage Patch, else 0
            S_num:  Log10 scaled numerical concentration normalized against reference ceiling (10^6 #/km²)
        
        Tier Assignment:
            HPI >= 70.0: 'Critical (High)'
            40.0 <= HPI < 70.0: 'Moderate (Medium)'
            HPI < 40.0: 'Baseline (Low)'
        """
        # Mass sub-score (0 - 100)
        mass_ceiling = 5000.0
        if mass > 0:
            s_mass = min(100.0, (math.log10(1.0 + mass) / math.log10(1.0 + mass_ceiling)) * 100.0)
        else:
            s_mass = 0.0

        # Gyre zone sub-score (0 or 100)
        s_gpgp = 100.0 if inside_gpgp == 1 else 0.0

        # Numerical concentration sub-score (0 - 100)
        num_ceiling = 1_000_000.0
        if numerical > 0:
            s_num = min(100.0, (math.log10(1.0 + numerical) / math.log10(1.0 + num_ceiling)) * 100.0)
        else:
            s_num = 0.0

        hpi = round(0.55 * s_mass + 0.30 * s_gpgp + 0.15 * s_num, 2)

        if hpi >= 70.0:
            tier = "Critical (High)"
        elif hpi >= 40.0:
            tier = "Moderate (Medium)"
        else:
            tier = "Baseline (Low)"

        return hpi, tier

    def get_summary_stats(self) -> Dict[str, Any]:
        """Returns statistical overview of the dataset."""
        if not self.observations:
            return {}

        masses = [o["mass_concentration_g_km2"] for o in self.observations]
        scores = [o["priority_score"] for o in self.observations]
        gpgp_count = sum(1 for o in self.observations if o["inside_gpgp"] == 1)

        critical_count = sum(1 for o in self.observations if o["priority_tier"] == "Critical (High)")
        moderate_count = sum(1 for o in self.observations if o["priority_tier"] == "Moderate (Medium)")
        baseline_count = sum(1 for o in self.observations if o["priority_tier"] == "Baseline (Low)")

        return {
            "total_observations": len(self.observations),
            "inside_gpgp_count": gpgp_count,
            "outside_gpgp_count": len(self.observations) - gpgp_count,
            "max_mass_concentration": max(masses),
            "median_mass_concentration": sorted(masses)[len(masses) // 2],
            "critical_hotspots": critical_count,
            "moderate_hotspots": moderate_count,
            "baseline_locations": baseline_count,
            "year_min": min(o["year"] for o in self.observations if o["year"] > 0),
            "year_max": max(o["year"] for o in self.observations if o["year"] > 0),
            "spatial_bounds": {
                "min_lat": min(o["latitude"] for o in self.observations),
                "max_lat": max(o["latitude"] for o in self.observations),
                "min_lon": min(o["longitude"] for o in self.observations),
                "max_lon": max(o["longitude"] for o in self.observations),
            }
        }

    def get_hotspots(
        self,
        tier: Optional[str] = None,
        inside_gpgp: Optional[int] = None,
        limit: int = 250
    ) -> List[Dict[str, Any]]:
        """Returns ranked observations matching optional filter criteria."""
        results = self.observations
        if tier:
            results = [r for r in results if tier.lower() in r["priority_tier"].lower()]
        if inside_gpgp is not None:
            results = [r for r in results if r["inside_gpgp"] == inside_gpgp]

        # Sort descending by priority score
        sorted_results = sorted(results, key=lambda x: x["priority_score"], reverse=True)
        return sorted_results[:limit]

    def get_spatial_clusters(self, grid_size: float = 5.0) -> List[Dict[str, Any]]:
        """
        Aggregates observations into geographic grid cells (grid_size degrees x grid_size degrees)
        to identify macro-scale accumulation hotspots.
        """
        cells: Dict[Tuple[float, float], List[Dict[str, Any]]] = {}

        for obs in self.observations:
            grid_lat = round(math.floor(obs["latitude"] / grid_size) * grid_size + (grid_size / 2.0), 2)
            grid_lon = round(math.floor(obs["longitude"] / grid_size) * grid_size + (grid_size / 2.0), 2)
            key = (grid_lat, grid_lon)
            if key not in cells:
                cells[key] = []
            cells[key].append(obs)

        clusters = []
        for (lat, lon), group in cells.items():
            count = len(group)
            avg_mass = sum(g["mass_concentration_g_km2"] for g in group) / count
            max_mass = max(g["mass_concentration_g_km2"] for g in group)
            avg_score = sum(g["priority_score"] for g in group) / count
            gpgp_in = sum(1 for g in group if g["inside_gpgp"] == 1)

            if avg_score >= 70.0:
                tier = "Critical (High)"
            elif avg_score >= 40.0:
                tier = "Moderate (Medium)"
            else:
                tier = "Baseline (Low)"

            clusters.append({
                "cluster_latitude": lat,
                "cluster_longitude": lon,
                "observation_count": count,
                "mean_mass_concentration": round(avg_mass, 2),
                "max_mass_concentration": round(max_mass, 2),
                "mean_priority_score": round(avg_score, 2),
                "cluster_tier": tier,
                "inside_gpgp_percentage": round((gpgp_in / count) * 100, 1)
            })

        return sorted(clusters, key=lambda c: c["mean_priority_score"], reverse=True)


# Module-level singleton
hotspot_service = HotspotService()
