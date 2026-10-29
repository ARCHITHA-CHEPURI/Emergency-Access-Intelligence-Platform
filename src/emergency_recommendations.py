import pandas as pd

INPUT = "data/processed/emergency_junction_hotspots.csv"
OUTPUT = "data/processed/emergency_recommendations.csv"

print("=" * 50)
print("       EMERGENCY RESPONSE RECOMMENDATION")
print("=" * 50)

df = pd.read_csv(INPUT)

def generate_recommendation(row):

    risk = row["risk_category"]
    distance = row["nearest_hospital_distance_km"]
    hospitals = row["hospitals_within_5km"]
    hospital_risk = row["hospital_access_risk"]

    if risk == "CRITICAL" and distance > 4:
        return (
            "Immediate attention; "
            "consider emergency medical staging "
            "and alternate hospital routing."
        )

    if risk == "CRITICAL":
        return (
            "Immediate attention; "
            "prioritize emergency response readiness."
        )

    if risk == "HIGH" and distance > 3:
        return (
            "High attention; "
            "review emergency hospital access "
            "and alternate routes."
        )

    if hospitals <= 2:
        return (
            "Limited nearby hospital coverage; "
            "consider additional emergency support."
        )

    if hospital_risk > 0.5:
        return (
            "Elevated hospital accessibility risk; "
            "monitor emergency response access."
        )

    if risk == "MEDIUM":
        return (
            "Monitor junction conditions "
            "and maintain emergency preparedness."
        )

    return "Routine monitoring."

df["response_recommendation"] = df.apply(
    generate_recommendation,
    axis=1
)

df.to_csv(
    OUTPUT,
    index=False
)

print("\nRecommendations generated:", len(df))

print("\nSample recommendations:")

print(
    df[
        [
            "final_risk_rank",
            "junction_id",
            "risk_category",
            "hospital_access_risk",
            "nearest_hospital_distance_km",
            "response_recommendation"
        ]
    ].head(10).to_string(index=False)
)

print("\nSaved:")
print(OUTPUT)

print("\nDONE.")