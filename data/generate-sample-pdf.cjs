// Minimal pure Node.js valid 30-page PDF generator without third-party dependencies
const fs = require('fs');
const path = require('path');

function createSamplePdf(outputPath) {
  const pages = 30;
  let objects = [];
  let currentObjId = 1;

  // Catalog
  const catalogId = currentObjId++;
  // Pages
  const pagesId = currentObjId++;
  // Font
  const fontId = currentObjId++;

  const pageIds = [];
  const contentIds = [];

  for (let i = 1; i <= pages; i++) {
    pageIds.push(currentObjId++);
    contentIds.push(currentObjId++);
  }

  let body = '';
  const offsets = [];

  function addObj(id, content) {
    offsets[id] = Buffer.byteLength(body, 'latin1') + 9; // +9 for %PDF-1.4\n
    body += `${id} 0 obj\n${content}\nendobj\n`;
  }

  // 1: Catalog
  addObj(catalogId, `<< /Type /Catalog /Pages ${pagesId} 0 R >>`);

  // 2: Pages
  const kidsStr = pageIds.map(id => `${id} 0 R`).join(' ');
  addObj(pagesId, `<< /Type /Pages /Kids [${kidsStr}] /Count ${pages} >>`);

  // 3: Font
  addObj(fontId, `<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>`);

  // Page specific content
  const pageContents = {
    1: 'STAR HEALTH & ALLIED INSURANCE\\nMediClassic Individual Policy Document\\nPolicy No: POL-STAR-2024-8849102',
    5: 'SECTION 1.1 - BASIC SUM INSURED\\nSum Insured: INR 5,00,000 (Five Lakhs Only)\\nMaximum aggregate liability across policy period.',
    7: 'SECTION 2.3 - VOLUNTARY DEDUCTIBLE\\nVoluntary Deductible: NIL. No deductible opted under this schedule.',
    12: 'SECTION 3.2 - ROOM, BOARDING AND NURSING EXPENSES\\nRoom rent capped up to 1% of Sum Insured per day (INR 5,000/day).\\nProportionate deductions apply to associated medical charges if room rent exceeds limit.',
    15: 'SECTION 4.1 - WAITING PERIODS\\n24 Months waiting period for Pre-Existing Diseases (PED) and joint replacements.',
    18: 'SECTION 4.7 - CO-PAYMENT CLAUSE\\nA compulsory co-payment of 10% shall apply on every admissible claim amount.',
    24: 'SECTION 6.1 - SPECIFIED PROCEDURE SUB-LIMITS\\nAppendectomy (Laparoscopic/Open) capped at INR 40,000 per hospitalization.\\nCataract capped at INR 35,000 per eye. Hernia capped at INR 50,000.',
    28: 'SECTION 7.1 - PERMANENT EXCLUSIONS\\nCosmetic surgery, aesthetic treatments, and unproven therapies are excluded.',
    30: 'SECTION 8 - CLAIMS PROCESS\\nSubmit itemized bills and discharge summary within 15 days.'
  };

  for (let i = 1; i <= pages; i++) {
    const textLines = (pageContents[i] || `Star Health MediClassic Policy Document - Page ${i}\\nGeneral Terms & Conditions`).split('\\n');
    let streamContent = `BT /F1 14 Tf 50 720 Td (Page ${i} of ${pages}) Tj ET\n`;
    let yPos = 680;
    for (const line of textLines) {
      // Escape parentheses in line
      const safeLine = line.replace(/\\/g, '\\\\').replace(/\(/g, '\\(').replace(/\)/g, '\\)');
      streamContent += `BT /F1 12 Tf 50 ${yPos} Td (${safeLine}) Tj ET\n`;
      yPos -= 25;
    }

    const streamLen = Buffer.byteLength(streamContent, 'latin1');
    addObj(contentIds[i - 1], `<< /Length ${streamLen} >>\nstream\n${streamContent}\nendstream`);
    addObj(pageIds[i - 1], `<< /Type /Page /Parent ${pagesId} 0 R /MediaBox [0 0 595 842] /Contents ${contentIds[i - 1]} 0 R /Resources << /Font << /F1 ${fontId} 0 R >> >> >>`);
  }

  const startXref = Buffer.byteLength(body, 'latin1') + 9;
  let xref = `xref\n0 ${currentObjId}\n0000000000 65535 f \n`;
  for (let i = 1; i < currentObjId; i++) {
    const offset = String(offsets[i]).padStart(10, '0');
    xref += `${offset} 00000 n \n`;
  }

  const trailer = `trailer\n<< /Size ${currentObjId} /Root ${catalogId} 0 R >>\nstartxref\n${startXref}\n%%EOF\n`;
  const pdfData = `%PDF-1.4\n${body}${xref}${trailer}`;

  fs.writeFileSync(outputPath, Buffer.from(pdfData, 'latin1'));
  console.log(`Generated sample PDF at ${outputPath} (${pdfData.length} bytes, ${pages} pages)`);
}

const targetPath = path.resolve('f:/FIN-01/storage/policies/sample-policy.pdf');
createSamplePdf(targetPath);
