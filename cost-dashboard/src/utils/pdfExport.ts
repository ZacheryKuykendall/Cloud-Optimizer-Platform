import jsPDF from 'jspdf';
import autoTable from 'jspdf-autotable';
import { format } from 'date-fns';

interface ExportData {
  costs: any[];
  breakdown: {
    byService: { [key: string]: number };
    byRegion: { [key: string]: number };
    byTag: { [key: string]: { [key: string]: number } };
    byTime: { [key: string]: number };
  };
  trends?: any[];
  period: {
    start: Date;
    end: Date;
  };
  filters?: {
    view?: string;
    tag?: string;
    metric?: string;
  };
}

const formatCurrency = (value: number): string => {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
  }).format(value);
};

const formatDate = (date: Date): string => {
  return format(date, 'yyyy-MM-dd');
};

export const generatePDF = (data: ExportData, title: string): void => {
  const doc = new jsPDF();
  const pageWidth = doc.internal.pageSize.width;
  const margin = 20;

  // Title
  doc.setFontSize(20);
  doc.text(title, margin, margin);

  // Period and Filters
  doc.setFontSize(12);
  doc.text(
    `Period: ${formatDate(data.period.start)} to ${formatDate(data.period.end)}`,
    margin,
    margin + 10
  );

  if (data.filters) {
    const filterText = Object.entries(data.filters)
      .filter(([_, value]) => value && value !== 'all')
      .map(([key, value]) => `${key}: ${value}`)
      .join(', ');
    if (filterText) {
      doc.text(`Filters: ${filterText}`, margin, margin + 20);
    }
  }

  let yOffset = margin + 30;

  // Cost by Service
  if (Object.keys(data.breakdown.byService).length > 0) {
    doc.setFontSize(14);
    doc.text('Cost by Service', margin, yOffset);
    yOffset += 10;

    const serviceData = Object.entries(data.breakdown.byService).map(([service, cost]) => [
      service,
      formatCurrency(cost),
    ]);

    autoTable(doc, {
      startY: yOffset,
      head: [['Service', 'Cost']],
      body: serviceData,
      margin: { left: margin },
    });

    yOffset = (doc as any).lastAutoTable.finalY + 20;
  }

  // Cost by Region
  if (Object.keys(data.breakdown.byRegion).length > 0) {
    if (yOffset > doc.internal.pageSize.height - 60) {
      doc.addPage();
      yOffset = margin;
    }

    doc.setFontSize(14);
    doc.text('Cost by Region', margin, yOffset);
    yOffset += 10;

    const regionData = Object.entries(data.breakdown.byRegion).map(([region, cost]) => [
      region,
      formatCurrency(cost),
    ]);

    autoTable(doc, {
      startY: yOffset,
      head: [['Region', 'Cost']],
      body: regionData,
      margin: { left: margin },
    });

    yOffset = (doc as any).lastAutoTable.finalY + 20;
  }

  // Cost by Tag
  if (Object.keys(data.breakdown.byTag).length > 0) {
    if (yOffset > doc.internal.pageSize.height - 60) {
      doc.addPage();
      yOffset = margin;
    }

    doc.setFontSize(14);
    doc.text('Cost by Tag', margin, yOffset);
    yOffset += 10;

    const tagData = Object.entries(data.breakdown.byTag).flatMap(([tag, values]) =>
      Object.entries(values).map(([key, cost]) => [tag, key, formatCurrency(cost)])
    );

    autoTable(doc, {
      startY: yOffset,
      head: [['Tag', 'Value', 'Cost']],
      body: tagData,
      margin: { left: margin },
    });

    yOffset = (doc as any).lastAutoTable.finalY + 20;
  }

  // Daily Costs
  if (data.costs.length > 0) {
    if (yOffset > doc.internal.pageSize.height - 60) {
      doc.addPage();
      yOffset = margin;
    }

    doc.setFontSize(14);
    doc.text('Daily Costs', margin, yOffset);
    yOffset += 10;

    const dailyData = data.costs.map((cost) => [
      cost.date,
      formatCurrency(cost.amount),
      cost.service,
      cost.category,
    ]);

    autoTable(doc, {
      startY: yOffset,
      head: [['Date', 'Amount', 'Service', 'Category']],
      body: dailyData,
      margin: { left: margin },
    });
  }

  // Footer
  const totalPages = doc.internal.getNumberOfPages();
  for (let i = 1; i <= totalPages; i++) {
    doc.setPage(i);
    doc.setFontSize(10);
    doc.text(
      `Page ${i} of ${totalPages}`,
      pageWidth / 2,
      doc.internal.pageSize.height - 10,
      { align: 'center' }
    );
    doc.text(
      `Generated on ${format(new Date(), 'yyyy-MM-dd HH:mm:ss')}`,
      pageWidth - margin,
      doc.internal.pageSize.height - 10,
      { align: 'right' }
    );
  }

  // Save the PDF
  doc.save(`${title.toLowerCase().replace(/\s+/g, '-')}-${format(new Date(), 'yyyyMMdd')}.pdf`);
};
