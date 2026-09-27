import { PrismaClient } from '@prisma/client';
import fs from 'fs';
import path from 'path';

const prisma = new PrismaClient();

async function main() {
  console.log('--- Starting Database Seeding ---');

  // Clean existing tables in reverse dependency order
  await prisma.citation.deleteMany();
  await prisma.calculation.deleteMany();
  await prisma.policyRule.deleteMany();
  await prisma.hospitalCost.deleteMany();
  await prisma.procedure.deleteMany();
  await prisma.policy.deleteMany();

  // 1. Seed Procedures
  const proceduresPath = path.resolve(process.cwd(), 'data/procedures.json');
  const proceduresRaw = fs.readFileSync(proceduresPath, 'utf-8');
  const proceduresData = JSON.parse(proceduresRaw);

  const procedureMap = new Map<string, string>(); // code -> id

  for (const proc of proceduresData) {
    const created = await prisma.procedure.create({
      data: {
        code: proc.code,
        name: proc.name,
        category: proc.category,
        description: proc.description,
      },
    });
    procedureMap.set(proc.code, created.id);
  }
  console.log(`Seeded ${proceduresData.length} procedures.`);

  // 2. Seed Hospital Costs
  const costsPath = path.resolve(process.cwd(), 'data/hospital-costs.json');
  const costsRaw = fs.readFileSync(costsPath, 'utf-8');
  const costsData = JSON.parse(costsRaw);

  let costsCount = 0;
  for (const cost of costsData) {
    const procId = procedureMap.get(cost.procedureCode);
    if (!procId) continue;

    await prisma.hospitalCost.create({
      data: {
        procedureId: procId,
        city: cost.city || 'National Average',
        roomCategory: cost.roomCategory,
        roomRate: cost.roomRate,
        stayDays: cost.stayDays || 1,
        proportionateCosts: cost.proportionateCosts,
        nonProportionateCosts: cost.nonProportionateCosts,
        otherCosts: cost.otherCosts || 0,
        totalBill: cost.totalBill,
        currency: cost.currency || 'INR',
        source: cost.source || 'Reference Benchmark Schedule',
      },
    });
    costsCount++;
  }
  console.log(`Seeded ${costsCount} hospital cost benchmark scenarios.`);

  // 3. Seed Sample Policy
  const policyJsonPath = path.resolve(process.cwd(), 'data/sample-policy.json');
  const policyJsonRaw = fs.readFileSync(policyJsonPath, 'utf-8');
  const policyData = JSON.parse(policyJsonRaw);

  const markdownPath = path.resolve(process.cwd(), 'data/sample-policy-markdown.md');
  const rawMarkdown = fs.existsSync(markdownPath) ? fs.readFileSync(markdownPath, 'utf-8') : null;

  const policy = await prisma.policy.create({
    data: {
      fileName: 'Star_Health_MediClassic_Sample.pdf',
      filePath: 'policies/sample-policy.pdf',
      status: 'READY',
      insurerName: policyData.policy_metadata?.insurer_name || 'Star Health',
      policyName: policyData.policy_metadata?.policy_name || 'MediClassic Individual Plan',
      rawMarkdown,
      parsedDocumentJson: {
        extractedPolicy: policyData,
      },
      extractionVersion: '1.0.0',
    },
  });
  console.log(`Seeded Policy: ${policy.policyName} (ID: ${policy.id})`);

  // 4. Seed Policy Rules & Citations
  // Rule 1: Sum Insured
  const sumInsuredRule = await prisma.policyRule.create({
    data: {
      policyId: policy.id,
      ruleType: 'SUM_INSURED',
      ruleName: 'Basic Sum Insured',
      value: policyData.sum_insured?.value || 500000,
      unit: 'INR',
      description: 'Maximum aggregate liability across policy period.',
      sourcePage: policyData.sum_insured?.source?.page || 5,
      sourceText: policyData.sum_insured?.source?.text,
      boundingBox: policyData.sum_insured?.source?.bounding_box,
      confidenceLevel: 'HIGH',
    },
  });

  if (policyData.sum_insured?.source) {
    await prisma.citation.create({
      data: {
        policyId: policy.id,
        policyRuleId: sumInsuredRule.id,
        pageNumber: policyData.sum_insured.source.page,
        sourceText: policyData.sum_insured.source.text,
        boundingBox: policyData.sum_insured.source.bounding_box,
      },
    });
  }

  // Rule 2: Room Rent Cap
  const roomRentRule = await prisma.policyRule.create({
    data: {
      policyId: policy.id,
      ruleType: 'ROOM_RENT_CAP',
      ruleName: 'Room Rent Daily Limit',
      value: policyData.room_rent_rule?.percentage || 1.0,
      unit: '%',
      description: policyData.room_rent_rule?.description || '1% of Sum Insured per day',
      sourcePage: policyData.room_rent_rule?.source?.page || 12,
      sourceText: policyData.room_rent_rule?.source?.text,
      boundingBox: policyData.room_rent_rule?.source?.bounding_box,
      confidenceLevel: 'HIGH',
    },
  });

  if (policyData.room_rent_rule?.source) {
    await prisma.citation.create({
      data: {
        policyId: policy.id,
        policyRuleId: roomRentRule.id,
        pageNumber: policyData.room_rent_rule.source.page,
        sourceText: policyData.room_rent_rule.source.text,
        boundingBox: policyData.room_rent_rule.source.bounding_box,
      },
    });
  }

  // Rule 3: Co-Pay
  const copayRule = await prisma.policyRule.create({
    data: {
      policyId: policy.id,
      ruleType: 'COPAY',
      ruleName: 'Mandatory Co-Payment',
      value: policyData.copay?.percentage || 10.0,
      unit: '%',
      description: '10% co-payment applicable on admissible claim amount.',
      sourcePage: policyData.copay?.source?.page || 18,
      sourceText: policyData.copay?.source?.text,
      boundingBox: policyData.copay?.source?.bounding_box,
      confidenceLevel: 'HIGH',
    },
  });

  if (policyData.copay?.source) {
    await prisma.citation.create({
      data: {
        policyId: policy.id,
        policyRuleId: copayRule.id,
        pageNumber: policyData.copay.source.page,
        sourceText: policyData.copay.source.text,
        boundingBox: policyData.copay.source.bounding_box,
      },
    });
  }

  // Sub-limits
  if (Array.isArray(policyData.sub_limits)) {
    for (const sl of policyData.sub_limits) {
      const slRule = await prisma.policyRule.create({
        data: {
          policyId: policy.id,
          ruleType: 'PROCEDURE_SUBLIMIT',
          ruleName: `Sub-limit: ${sl.procedure_name}`,
          value: sl.amount,
          unit: 'INR',
          description: sl.description,
          sourcePage: sl.source?.page || 24,
          sourceText: sl.source?.text,
          boundingBox: sl.source?.bounding_box,
          confidenceLevel: 'HIGH',
        },
      });

      if (sl.source) {
        await prisma.citation.create({
          data: {
            policyId: policy.id,
            policyRuleId: slRule.id,
            pageNumber: sl.source.page,
            sourceText: sl.source.text,
            boundingBox: sl.source.bounding_box,
          },
        });
      }
    }
  }

  console.log('Seeded Policy Rules and Citations.');

  // 5. Seed Demo Calculation Scenario
  const appProcId = procedureMap.get('PROC-APP-LAP');
  if (appProcId) {
    await prisma.calculation.create({
      data: {
        policyId: policy.id,
        procedureId: appProcId,
        scenarioJson: {
          procedureCode: 'PROC-APP-LAP',
          procedureName: 'Laparoscopic Appendectomy',
          roomCategory: 'SINGLE_PRIVATE',
          stayDays: 2,
          city: 'National Average',
        },
        inputJson: {
          policyId: policy.id,
          procedureCode: 'PROC-APP-LAP',
          roomCategory: 'SINGLE_PRIVATE',
          stayDays: 2,
        },
        resultJson: {
          allowedRoomRent: 5000,
          roomFactor: 0.625,
          insurerProportionateShare: 28125,
          coveredRoomRent: 10000,
          baseInsurerLiability: 77125,
          deductible: 0,
          copayPercentage: 10,
          copayAmount: 7713,
          postCopayPay: 69412,
          procedureSubLimit: 40000,
          finalInsurerPay: 40000,
          outOfPocket: 60000,
        },
        calculationTraceJson: [
          {
            step: 'ALLOWED_ROOM_RENT',
            title: 'Step 1: Allowed Room Rent Determination',
            formula: 'SumInsured (500000) × 1% / 100 = ₹5,000/day',
            inputs: { sumInsured: 500000, percentage: 1 },
            result: 5000,
          },
          {
            step: 'ROOM_FACTOR',
            title: 'Step 2: Room Factor Calculation',
            formula: 'min(1, AllowedRoomRent (5000) / ActualRoomRate (8000)) = 0.625',
            inputs: { allowedRoomRent: 5000, actualRoomRate: 8000 },
            result: 0.625,
          },
          {
            step: 'PROPORTIONATE_COSTS',
            title: 'Step 3: Proportionate Costs Adjustment',
            formula: 'Hospital Proportionate (₹45,000) × 0.625 = ₹28,125',
            inputs: { hospitalProportionateCosts: 45000, roomFactor: 0.625 },
            result: 28125,
          },
          {
            step: 'COVERED_ROOM_RENT',
            title: 'Step 4: Covered Room Rent Calculation',
            formula: 'min(5000, 8000) × 2 days = ₹10,000',
            inputs: { allowedRoomRent: 5000, actualRoomRate: 8000, stayDays: 2 },
            result: 10000,
          },
          {
            step: 'BASE_LIABILITY',
            title: 'Step 5: Base Insurer Liability Aggregation',
            formula: '28125 + 35000 + 10000 + 4000 = ₹77,125',
            inputs: { proportionate: 28125, nonProportionate: 35000, room: 10000, other: 4000 },
            result: 77125,
          },
          {
            step: 'COPAY',
            title: 'Step 7: Co-payment Application',
            formula: '77125 × (1 - 0.10) = ₹69,412',
            inputs: { baseInsurerLiability: 77125, copayPercentage: 10 },
            result: 69412,
          },
          {
            step: 'PROCEDURE_SUBLIMIT',
            title: 'Step 8: Procedure Sub-limit Cap',
            formula: 'min(69412, 40000) = ₹40,000',
            inputs: { postCopayPay: 69412, subLimitCap: 40000 },
            result: 40000,
          },
          {
            step: 'FINAL_OOP',
            title: 'Step 9: Final Patient Out-of-Pocket Expense',
            formula: 'TotalBill (100000) - FinalInsurerPay (40000) = ₹60,000',
            inputs: { totalHospitalBill: 100000, finalInsurerPay: 40000 },
            result: 60000,
          }
        ],
        engineVersion: '1.0.0',
      },
    });
    console.log('Seeded Demo Calculation Scenario.');
  }

  console.log('--- Database Seeding Complete ---');
}

main()
  .catch((e) => {
    console.error('Seeding error:', e);
    process.exit(1);
  })
  .finally(async () => {
    await prisma.$disconnect();
  });
