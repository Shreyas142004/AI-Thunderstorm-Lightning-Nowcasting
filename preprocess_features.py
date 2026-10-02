"""
Convective Meteorological Feature Engineering & Preprocessing Pipeline
=======================================================================
Project: AI-Based Thunderstorm & Convective Weather Nowcasting System
Location: Karnataka (Bangalore HAL Observatory, WMO 43295)
Author: ML Engineer / Data Scientist

Description:
    Transforms raw daily weather observations into physical atmospheric features
    for machine learning modeling:
    - Cleans artifacts and handles temporal gaps (e.g., Year 2004 gap).
    - Computes thermodynamic instability proxies (Dew Point Depression,
      Vapor Pressure Deficit, Diurnal Temperature Range).
    - Computes kinematic features (Wind vector decomposition u/v, pressure tendencies).
    - Generates multi-day lags and rolling antecedent moisture metrics.
    - Encodes seasonal/monsoonal cyclical patterns (sin/cos of day of year).
    - Formulates ground-truth convective event classification targets.
    - Exports clean dataset and generates chronological train/test splits.
"""

import os
import argparse
import numpy as np
import pandas as pd
from pathlib import Path

# Import central project configuration
from config import DATASET_DIR, PROCESSED_DIR


def parse_arguments() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Preprocess and engineer convective atmospheric features."
    )
    parser.add_argument(
        "--input",
        "-i",
        type=str,
        default=str(DATASET_DIR / "karnataka_dataset.xlsx"),
        help="Path to input weather dataset (.xlsx or .csv)",
    )
    parser.add_argument(
        "--output",
        "-o",
        type=str,
        default=str(PROCESSED_DIR / "karnataka_convective_features.csv"),
        help="Path for exported feature-engineered CSV",
    )
    return parser.parse_args()


def load_raw_dataset(file_path: str) -> pd.DataFrame:
    """Load raw dataset from Excel or CSV format."""
    print(f"[1/6] Loading raw dataset from: '{file_path}'...")
    if file_path.lower().endswith((".xlsx", ".xls")):
        df = pd.read_excel(file_path)
    else:
        df = pd.read_csv(file_path, low_memory=False)
    print(f"      Initial shape: {df.shape[0]:,} rows x {df.shape[1]} columns")
    return df


def clean_and_harmonize(df: pd.DataFrame) -> pd.DataFrame:
    """
    Perform initial sanitation:
    - Deduplicate timestamps
    - Parse datetime and sort chronologically
    - Drop 100% null and constant columns
    - Identify temporal segments (handles Year 2004 gap)
    """
    print("[2/6] Cleaning raw data & harmonizing temporal continuity...")
    df = df.copy()

    # Standardize column names to lower case
    df.columns = [c.strip().lower() for c in df.columns]

    # Convert datetime
    df["datetime"] = pd.to_datetime(df["datetime"])
    
    # Deduplicate timestamps
    initial_count = len(df)
    df = df.drop_duplicates(subset=["datetime"]).sort_values(by="datetime").reset_index(drop=True)
    dropped_dups = initial_count - len(df)
    if dropped_dups > 0:
        print(f"      Removed {dropped_dups} duplicate timestamp record(s).")

    # Drop 100% null columns identified during EDA
    cols_to_drop = ["solarradiation", "solarenergy", "uvindex", "severerisk", "snow", "snowdepth"]
    existing_drops = [c for c in cols_to_drop if c in df.columns]
    df = df.drop(columns=existing_drops)
    print(f"      Dropped unpopulated/constant columns: {existing_drops}")

    # Detect temporal discontinuity (e.g., Year 2004 gap)
    # If gap between records > 2 days, assign a new segment_id to prevent rolling leakage
    time_diff = df["datetime"].diff()
    is_break = time_diff > pd.Timedelta(days=2)
    df["segment_id"] = is_break.cumsum()
    n_segments = df["segment_id"].nunique()
    print(f"      Identified {n_segments} continuous temporal segment(s). (Gaps handled cleanly)")

    return df


def convert_units_to_metric(df: pd.DataFrame) -> pd.DataFrame:
    """
    Convert US Customary units (°F, inches, mph) to International Meteorological Standard (°C, mm, km/h):
    - Temperature: °C = (°F - 32) * 5/9
    - Precipitation: mm = inches * 25.4
    - Wind speed: km/h = mph * 1.60934
    """
    print("[3/6] Converting meteorological units to metric standard (deg C, mm, km/h)...")
    df = df.copy()

    # Temperature conversions
    temp_cols = ["temp", "tempmax", "tempmin", "feelslike", "feelslikemax", "feelslikemin", "dew"]
    for col in temp_cols:
        if col in df.columns:
            df[f"{col}_c"] = ((df[col] - 32.0) * (5.0 / 9.0)).round(2)

    # Precipitation conversion
    if "precip" in df.columns:
        df["precip_mm"] = (df["precip"] * 25.4).round(2)

    # Wind speed conversion
    if "windspeed" in df.columns:
        df["windspeed_kmh"] = (df["windspeed"] * 1.60934).round(2)
        df["windspeed_ms"] = (df["windspeed_kmh"] / 3.6).round(2)

    if "windgust" in df.columns:
        # Wind gust is sparse (only reported when gust > threshold); fillna with windspeed
        df["windgust_kmh"] = (df["windgust"] * 1.60934).round(2)
        df["has_recorded_gust"] = df["windgust"].notnull().astype(int)
        df["windgust_kmh"] = df["windgust_kmh"].fillna(df["windspeed_kmh"])

    return df


def engineer_atmospheric_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Compute domain-specific thermodynamic and kinematic convective features:
    1. Dew Point Depression (DPD = T - Td)
    2. Diurnal Temperature Range (DTR = Tmax - Tmin)
    3. Vapor Pressure & Vapor Pressure Deficit (VPD via Magnus-Tetens formula)
    4. Apparent Temperature Difference (FeelsLike - Temp)
    5. Wind Vector Components (u: zonal east-west, v: meridional north-south)
    6. Cyclical Seasonal Encodings (sine/cosine of Day of Year and Month)
    7. Multi-day Temporal Lags (t-1, t-2, t-3)
    8. Multi-day Rolling Aggregations (3-day and 7-day cumulative precip and moisture)
    """
    print("[4/6] Engineering domain-specific convective meteorological features...")
    df = df.copy()

    # 1. Dew Point Depression (DPD): Indicator of atmospheric boundary-layer saturation
    # Low DPD (< 3°C) signifies near-saturated surface air -> high convective potential
    df["dew_point_depression_c"] = (df["temp_c"] - df["dew_c"]).round(2)

    # 2. Diurnal Temperature Range (DTR): Daytime radiative heating proxy
    # High DTR indicates intense solar insolation capable of triggering thermal updrafts
    df["diurnal_temp_range_c"] = (df["tempmax_c"] - df["tempmin_c"]).round(2)

    # 3. Apparent Temperature Differential (thermal discomfort / high humidity factor)
    df["thermal_discomfort_delta_c"] = (df["feelslike_c"] - df["temp_c"]).round(2)

    # 4. Vapor Pressure & Saturation Vapor Pressure (Magnus-Tetens Formula in hPa)
    # e(T) = 6.112 * exp((17.67 * T) / (T + 243.5))
    df["vapor_pressure_hpa"] = (
        6.112 * np.exp((17.67 * df["dew_c"]) / (df["dew_c"] + 243.5))
    ).round(2)
    df["sat_vapor_pressure_hpa"] = (
        6.112 * np.exp((17.67 * df["temp_c"]) / (df["temp_c"] + 243.5))
    ).round(2)
    # Vapor Pressure Deficit (VPD): High VPD inhibits cloud development; Low VPD promotes condensation
    df["vapor_pressure_deficit_hpa"] = (
        df["sat_vapor_pressure_hpa"] - df["vapor_pressure_hpa"]
    ).round(2)

    # 5. Wind Vector Decomposition
    # Visual Crossing winddir is meteorological degrees (direction wind is blowing from)
    if "winddir" in df.columns:
        wind_rad = np.radians(df["winddir"].fillna(0))
        # u = zonal component (positive towards East), v = meridional (positive towards North)
        df["wind_u_kmh"] = (-df["windspeed_kmh"] * np.sin(wind_rad)).round(2)
        df["wind_v_kmh"] = (-df["windspeed_kmh"] * np.cos(wind_rad)).round(2)

    # 6. Cyclical Seasonal Encodings (Day of Year & Month)
    # Captures Pre-Monsoon convective thunderstorm season (April-May) and SW Monsoon (June-Sept)
    doy = df["datetime"].dt.dayofyear
    df["sin_day_of_year"] = np.sin(2 * np.pi * doy / 365.25).round(4)
    df["cos_day_of_year"] = np.cos(2 * np.pi * doy / 365.25).round(4)

    month = df["datetime"].dt.month
    df["sin_month"] = np.sin(2 * np.pi * month / 12.0).round(4)
    df["cos_month"] = np.cos(2 * np.pi * month / 12.0).round(4)
    df["day_of_year"] = doy
    df["month"] = month
    df["year"] = df["datetime"].dt.year

    # 7. Temporal Lag Features (within continuous segments to prevent gap leakage)
    lag_cols = ["temp_c", "dew_c", "humidity", "precip_mm", "cloudcover"]
    if "sealevelpressure" in df.columns:
        # Interpolate pressure linearly within segment for missing values
        df["pressure_interpolated"] = df.groupby("segment_id")["sealevelpressure"].transform(
            lambda g: g.interpolate(method="linear", limit=3).bfill().ffill()
        )
        lag_cols.append("pressure_interpolated")
        # Pressure tendency (1-day pressure drop): barometric drops indicate incoming convective trough
        df["pressure_drop_1d"] = df.groupby("segment_id")["pressure_interpolated"].diff().round(2)

    for col in lag_cols:
        for lag in [1, 2, 3]:
            df[f"{col}_lag{lag}"] = df.groupby("segment_id")[col].shift(lag)

    # 8. Multi-day Rolling Antecedent Features (Moisture & Precipitation Accumulation)
    df["precip_accum_3d"] = (
        df.groupby("segment_id")["precip_mm"]
        .transform(lambda s: s.rolling(window=3, min_periods=1).sum())
        .round(2)
    )
    df["precip_accum_7d"] = (
        df.groupby("segment_id")["precip_mm"]
        .transform(lambda s: s.rolling(window=7, min_periods=1).sum())
        .round(2)
    )
    df["humidity_mean_3d"] = (
        df.groupby("segment_id")["humidity"]
        .transform(lambda s: s.rolling(window=3, min_periods=1).mean())
        .round(2)
    )
    df["temp_max_3d"] = (
        df.groupby("segment_id")["tempmax_c"]
        .transform(lambda s: s.rolling(window=3, min_periods=1).max())
        .round(2)
    )

    return df


def formulate_target_labels(df: pd.DataFrame) -> pd.DataFrame:
    """
    Formulate Convective Event ground-truth classification targets:
    
    1. Primary Target: `target_convective_rain` (Binary: 0 or 1)
       - 1: Convective rain day (conditions contains 'Rain' OR precipitation > 0.5 mm).
       - 0: Fair weather / dry day.
       
    2. Secondary Target: `target_severe_convective` (Binary: 0 or 1)
       - 1: High-impact convective storm day (Convective rain AND (precip_mm >= 75th percentile
            or strong wind gust > 30 km/h)).
       - 0: Moderate or non-severe day.
    """
    print("[5/6] Formulating Convective Weather Target Labels (Option 1)...")
    df = df.copy()

    # Normalize conditions string
    cond_str = df["conditions"].astype(str).str.lower()
    
    # Primary Target: Convective Rain Day
    is_rain_condition = cond_str.str.contains("rain", na=False)
    is_rain_measured = df["precip_mm"] > 0.5
    df["target_convective_rain"] = (is_rain_condition | is_rain_measured).astype(int)

    # Secondary Target: Severe Convective Event
    # High rainfall (> 10 mm ~ 75th percentile of rainy days) or high wind gust
    p75_rain = df.loc[df["target_convective_rain"] == 1, "precip_mm"].quantile(0.75)
    df["target_severe_convective"] = (
        (df["target_convective_rain"] == 1) & 
        ((df["precip_mm"] >= p75_rain) | (df["windgust_kmh"] >= 35.0))
    ).astype(int)

    # Target stats
    n_total = len(df)
    pos_primary = df["target_convective_rain"].sum()
    pos_severe = df["target_severe_convective"].sum()

    print(f"      -> Target 1 ('target_convective_rain'):  {pos_primary:,} / {n_total:,} ({pos_primary/n_total*100:.2f}%)")
    print(f"      -> Target 2 ('target_severe_convective'): {pos_severe:,} / {n_total:,} ({pos_severe/n_total*100:.2f}%)")

    return df


def export_and_summarize(df: pd.DataFrame, output_path: str):
    """
    Save the feature-engineered dataset and print correlation insights.
    """
    print(f"[6/6] Exporting processed dataset to: '{output_path}'...")
    
    # Drop initial lag burn-in rows (first 3 rows of each segment contain NaN in lag3)
    clean_df = df.dropna(subset=["temp_c_lag3", "precip_mm_lag3"]).reset_index(drop=True)
    
    # Ensure output directory exists
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    clean_df.to_csv(output_path, index=False)
    
    file_size_mb = os.path.getsize(output_path) / (1024 * 1024)
    print(f"      Saved {clean_df.shape[0]:,} records x {clean_df.shape[1]} features ({file_size_mb:.2f} MB).")

    # Display Top Feature Correlations with target_convective_rain
    numeric_cols = clean_df.select_dtypes(include=[np.number]).columns
    corrs = clean_df[numeric_cols].corr()["target_convective_rain"].drop(["target_convective_rain", "target_severe_convective"])
    sorted_corrs = corrs.abs().sort_values(ascending=False).head(15)

    print("\n" + "=" * 65)
    print(" TOP 15 PREDICTIVE CONVECTIVE FEATURES BY CORRELATION (|r|)")
    print("=" * 65)
    for feat in sorted_corrs.index:
        r_val = corrs[feat]
        direction = "+" if r_val > 0 else "-"
        print(f"  {feat:<32} : {direction}{abs(r_val):.4f}")
    print("=" * 65 + "\n")

    # Chronological Split Summary for Modeling (70% Train / 30% Test)
    min_year = int(clean_df["year"].min())
    max_year = int(clean_df["year"].max())
    split_year = int(min_year + 0.70 * (max_year - min_year))

    train_df = clean_df[clean_df["year"] <= split_year]
    test_df = clean_df[clean_df["year"] > split_year]
    print(f"Chronological Split for Model Training (70% Train / 30% Test):")
    print(f"  -> Train Set (70% | Years {min_year}-{split_year}): {len(train_df):,} samples ({len(train_df)/len(clean_df)*100:.1f}%)")
    print(f"  -> Test Set  (30% | Years {split_year+1}-{max_year}): {len(test_df):,} samples ({len(test_df)/len(clean_df)*100:.1f}%)")
    print("  => Ready for Model Training & Validation!\n")


def run_pipeline(input_path: str, output_path: str):
    """Execute complete end-to-end preprocessing."""
    raw_df = load_raw_dataset(input_path)
    clean_df = clean_and_harmonize(raw_df)
    metric_df = convert_units_to_metric(clean_df)
    feat_df = engineer_atmospheric_features(metric_df)
    target_df = formulate_target_labels(feat_df)
    export_and_summarize(target_df, output_path)


if __name__ == "__main__":
    args = parse_arguments()
    run_pipeline(args.input, args.output)
