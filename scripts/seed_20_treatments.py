import json
import sqlite3
from pathlib import Path

root_dir = Path(__file__).resolve().parent.parent
benchmarks_file = root_dir / "data" / "treatment_costs" / "benchmarks.json"
db_file = root_dir / "backend" / "fin01.db"

procedures_def = [
    {
        "id": "APPENDECTOMY",
        "name": "Appendectomy",
        "code": "SURG-APP-001",
        "cat": "General Surgery",
        "type": "Surgical",
        "aliases": ["Appendix surgery", "Appendix Removal", "Laparoscopic Appendectomy", "Acute appendicitis surgery"],
        "costs": {"Pune": (75000, 95000), "Mumbai": (110000, 145000), "Nagpur": (55000, 72000)}
    },
    {
        "id": "CATARACT_SURGERY",
        "name": "Cataract Surgery",
        "code": "SURG-OPH-002",
        "cat": "Ophthalmology",
        "type": "Day Care / Surgical",
        "aliases": ["Phacoemulsification", "Cataract Removal", "IOL Implantation", "Eye lens surgery"],
        "costs": {"Pune": (32000, 48000), "Mumbai": (45000, 65000), "Nagpur": (25000, 38000)}
    },
    {
        "id": "KNEE_REPLACEMENT",
        "name": "Knee Replacement",
        "code": "SURG-ORT-003",
        "cat": "Orthopedics",
        "type": "Major Surgical",
        "aliases": ["Total Knee Replacement", "TKR", "Knee Arthroplasty", "Bilateral Knee Replacement"],
        "costs": {"Pune": (180000, 240000), "Mumbai": (260000, 350000), "Nagpur": (140000, 190000)}
    },
    {
        "id": "C_SECTION",
        "name": "C-Section",
        "code": "SURG-OBS-004",
        "cat": "Obstetrics & Gynecology",
        "type": "Surgical",
        "aliases": ["Cesarean Section", "Caesarean Delivery", "LSCS", "Cesarean birth", "Maternity delivery"],
        "costs": {"Pune": (60000, 85000), "Mumbai": (90000, 130000), "Nagpur": (42000, 60000)}
    },
    {
        "id": "ANGIOPLASTY",
        "name": "Angioplasty",
        "code": "SURG-CAR-005",
        "cat": "Cardiology",
        "type": "Interventional Cardiology",
        "aliases": ["Coronary Angioplasty", "PTCA", "Stent placement", "Cardiac Stent", "Percutaneous Coronary Intervention"],
        "costs": {"Pune": (160000, 220000), "Mumbai": (220000, 310000), "Nagpur": (125000, 175000)}
    },
    {
        "id": "HERNIA_REPAIR",
        "name": "Hernia Repair",
        "code": "SURG-GEN-006",
        "cat": "General Surgery",
        "type": "Surgical",
        "aliases": ["Hernioplasty", "Inguinal Hernia Surgery", "Umbilical Hernia", "Laparoscopic Hernia Repair"],
        "costs": {"Pune": (65000, 95000), "Mumbai": (95000, 135000), "Nagpur": (48000, 70000)}
    },
    {
        "id": "CHOLECYSTECTOMY",
        "name": "Cholecystectomy",
        "code": "SURG-GEN-007",
        "cat": "General / GI Surgery",
        "type": "Surgical",
        "aliases": ["Gallbladder Removal", "Laparoscopic Cholecystectomy", "Gall stone surgery", "Lap Chole"],
        "costs": {"Pune": (70000, 105000), "Mumbai": (100000, 150000), "Nagpur": (50000, 78000)}
    },
    {
        "id": "KIDNEY_STONE_REMOVAL",
        "name": "Kidney Stone Removal",
        "code": "SURG-URO-008",
        "cat": "Urology",
        "type": "Endourology / Surgical",
        "aliases": ["PCNL", "URSL", "Lithotripsy", "RIRS", "Renal Calculus Surgery", "Calculus disease"],
        "costs": {"Pune": (55000, 85000), "Mumbai": (80000, 120000), "Nagpur": (40000, 65000)}
    },
    {
        "id": "HYSTERECTOMY",
        "name": "Hysterectomy",
        "code": "SURG-GYN-009",
        "cat": "Gynecology",
        "type": "Major Surgical",
        "aliases": ["Uterus Removal", "Laparoscopic Hysterectomy", "TLH", "Total Abdominal Hysterectomy"],
        "costs": {"Pune": (80000, 120000), "Mumbai": (115000, 170000), "Nagpur": (60000, 90000)}
    },
    {
        "id": "HIP_REPLACEMENT",
        "name": "Hip Replacement",
        "code": "SURG-ORT-010",
        "cat": "Orthopedics",
        "type": "Major Surgical",
        "aliases": ["Total Hip Arthroplasty", "THA", "Hip joint surgery", "Total Hip Replacement"],
        "costs": {"Pune": (190000, 260000), "Mumbai": (275000, 370000), "Nagpur": (150000, 210000)}
    },
    {
        "id": "CABG",
        "name": "CABG",
        "code": "SURG-CTS-011",
        "cat": "Cardiothoracic Surgery",
        "type": "Major Cardiac Surgery",
        "aliases": ["Heart Bypass", "Coronary Artery Bypass", "Open Heart Bypass", "Bypass surgery"],
        "costs": {"Pune": (280000, 390000), "Mumbai": (380000, 520000), "Nagpur": (220000, 310000)}
    },
    {
        "id": "NORMAL_DELIVERY",
        "name": "Normal Delivery",
        "code": "MED-OBS-012",
        "cat": "Obstetrics",
        "type": "Medical / Inpatient",
        "aliases": ["Vaginal Delivery", "Childbirth", "Maternity Normal", "Labor and delivery"],
        "costs": {"Pune": (40000, 60000), "Mumbai": (58000, 88000), "Nagpur": (28000, 45000)}
    },
    {
        "id": "TONSILLECTOMY",
        "name": "Tonsillectomy",
        "code": "SURG-ENT-013",
        "cat": "ENT",
        "type": "Day Care / Surgical",
        "aliases": ["Tonsil surgery", "Adenotonsillectomy", "Tonsil removal"],
        "costs": {"Pune": (35000, 52000), "Mumbai": (50000, 75000), "Nagpur": (25000, 40000)}
    },
    {
        "id": "HEMORRHOIDECTOMY",
        "name": "Hemorrhoidectomy",
        "code": "SURG-GEN-014",
        "cat": "General Surgery / Proctology",
        "type": "Surgical / Day Care",
        "aliases": ["Piles Surgery", "Fissure Surgery", "Fistula in ano", "Laser Piles", "Hemorrhoid surgery"],
        "costs": {"Pune": (45000, 68000), "Mumbai": (65000, 98000), "Nagpur": (32000, 50000)}
    },
    {
        "id": "DIALYSIS",
        "name": "Dialysis",
        "code": "MED-NEP-015",
        "cat": "Nephrology",
        "type": "Medical / Day Care",
        "aliases": ["Hemodialysis", "Kidney dialysis", "Renal dialysis package"],
        "costs": {"Pune": (22000, 35000), "Mumbai": (32000, 48000), "Nagpur": (16000, 26000)}
    },
    {
        "id": "CHEMOTHERAPY",
        "name": "Chemotherapy",
        "code": "MED-ONC-016",
        "cat": "Oncology",
        "type": "Day Care / Medical",
        "aliases": ["Chemo cycle", "Medical oncology", "Cancer infusion"],
        "costs": {"Pune": (40000, 75000), "Mumbai": (60000, 110000), "Nagpur": (30000, 55000)}
    },
    {
        "id": "TYMPANOPLASTY",
        "name": "Tympanoplasty",
        "code": "SURG-ENT-017",
        "cat": "ENT",
        "type": "Day Care / Surgical",
        "aliases": ["Eardrum Repair", "Myringoplasty", "Middle ear reconstruction", "Ear surgery"],
        "costs": {"Pune": (42000, 65000), "Mumbai": (60000, 90000), "Nagpur": (30000, 48000)}
    },
    {
        "id": "SEPTOPLASTY",
        "name": "Septoplasty",
        "code": "SURG-ENT-018",
        "cat": "ENT",
        "type": "Surgical",
        "aliases": ["Deviated Septum Surgery", "DNS surgery", "Turbinoplasty", "Nasal septum surgery"],
        "costs": {"Pune": (38000, 58000), "Mumbai": (55000, 82000), "Nagpur": (28000, 44000)}
    },
    {
        "id": "ARTHROSCOPY",
        "name": "Arthroscopy",
        "code": "SURG-ORT-019",
        "cat": "Orthopedics",
        "type": "Keyhole Surgical",
        "aliases": ["ACL Reconstruction", "Knee Arthroscopy", "Shoulder Arthroscopy", "Ligament repair"],
        "costs": {"Pune": (85000, 130000), "Mumbai": (120000, 180000), "Nagpur": (65000, 100000)}
    },
    {
        "id": "THYROIDECTOMY",
        "name": "Thyroidectomy",
        "code": "SURG-END-020",
        "cat": "Endocrine Surgery",
        "type": "Major Surgical",
        "aliases": ["Thyroid Surgery", "Total Thyroidectomy", "Hemithyroidectomy", "Goitre surgery"],
        "costs": {"Pune": (75000, 115000), "Mumbai": (105000, 160000), "Nagpur": (55000, 85000)}
    }
]

city_tiers = {
    "Pune": "Tier-1",
    "Mumbai": "Tier-1 Metro",
    "Nagpur": "Tier-2"
}

benchmarks_data = []
for p in procedures_def:
    for city, (c_min, c_max) in p["costs"].items():
        ref_cost = round((c_min + c_max) / 2)
        benchmarks_data.append({
            "treatment_id": p["id"],
            "canonical_name": p["name"],
            "procedure": p["name"],
            "procedure_code": p["code"],
            "category": p["cat"],
            "procedure_type": p["type"],
            "aliases": p["aliases"],
            "city": city,
            "city_tier": city_tiers.get(city, "Tier-1"),
            "reference_cost": ref_cost,
            "cost_min": c_min,
            "cost_max": c_max,
            "min_cost": c_min,
            "max_cost": c_max,
            "currency": "INR",
            "cost_unit": "per_procedure",
            "source": "State Healthcare Package Benchmark 2025",
            "source_date": "2025-01-15",
            "data_status": "REFERENCE",
            "data_type": "synthetic",
            "notes": f"NABH hospital benchmark estimation for {p['name']} in {city}."
        })

# Write benchmarks.json
with open(benchmarks_file, "w", encoding="utf-8") as f:
    json.dump(benchmarks_data, f, indent=2)

print(f"Successfully generated benchmarks.json with {len(benchmarks_data)} items across {len(procedures_def)} procedures.")

# Update SQLite database treatment_costs table if db exists
if db_file.exists():
    conn = sqlite3.connect(db_file)
    cur = conn.cursor()
    # Check if treatment_costs table exists
    cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='treatment_costs';")
    if cur.fetchone():
        cur.execute("DELETE FROM treatment_costs;")
        for b in benchmarks_data:
            cur.execute("""
                INSERT INTO treatment_costs 
                (procedure_name, procedure_code, city, city_tier, min_cost, max_cost, source, source_date, notes, data_type)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
            """, (
                b["procedure"], b["procedure_code"], b["city"], b["city_tier"],
                b["min_cost"], b["max_cost"], b["source"], b["source_date"],
                b["notes"], b["data_type"]
            ))
        conn.commit()
        print(f"Successfully synced {len(benchmarks_data)} records to treatment_costs table in fin01.db.")
    conn.close()
