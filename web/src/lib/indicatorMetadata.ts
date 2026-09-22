export type IndicatorFormat = "percent" | "usd" | "constant-usd";

export type IndicatorMetadata = {
  id: string;
  name: string;
  unit: string;
  frequency: string;
  description: string;
  whatItMeans: string;
  source: string;
  format: IndicatorFormat;
  chartTitle: string;
  chartSubtitle: string;
};

export const INDICATOR_METADATA: Record<string, IndicatorMetadata> = {
  "FP.CPI.TOTL.ZG": {
    id: "FP.CPI.TOTL.ZG",
    name: "Inflation",
    unit: "%",
    frequency: "Annual",
    description: "Annual percentage change in consumer prices.",
    whatItMeans: "Inflation describes how quickly the general price level changed compared with the previous year.",
    source: "World Bank",
    format: "percent",
    chartTitle: "How has inflation changed across selected Asian economies?",
    chartSubtitle: "Annual change in consumer prices, compared with the previous year.",
  },
  "NY.GDP.MKTP.CD": {
    id: "NY.GDP.MKTP.CD",
    name: "GDP",
    unit: "current US$",
    frequency: "Annual",
    description: "Total value of goods and services produced in the economy.",
    whatItMeans: "GDP measures the total value of goods and services produced within an economy during a given year.",
    source: "World Bank",
    format: "usd",
    chartTitle: "How large are the economies in comparison?",
    chartSubtitle: "Total economic output in current US dollars.",
  },
  "NY.GDP.MKTP.KD.ZG": {
    id: "NY.GDP.MKTP.KD.ZG",
    name: "GDP growth",
    unit: "%",
    frequency: "Annual",
    description: "Annual percentage change in real GDP.",
    whatItMeans: "GDP growth shows how much economic output changed compared with the previous year.",
    source: "World Bank",
    format: "percent",
    chartTitle: "How quickly are these economies growing?",
    chartSubtitle: "Annual percentage change in real GDP, compared with the previous year.",
  },
  "NY.GDP.PCAP.KD": {
    id: "NY.GDP.PCAP.KD",
    name: "GDP per person",
    unit: "constant US$",
    frequency: "Annual",
    description: "Economic output per person in constant US dollars.",
    whatItMeans: "GDP per person is GDP divided by population. It is a rough measure of economic output per person, not individual income.",
    source: "World Bank",
    format: "constant-usd",
    chartTitle: "How does economic output per person compare?",
    chartSubtitle: "GDP per person in constant US dollars.",
  },
  "SL.UEM.TOTL.ZS": {
    id: "SL.UEM.TOTL.ZS",
    name: "Unemployment",
    unit: "% of labor force",
    frequency: "Annual",
    description: "Share of the labor force without work but available for and seeking employment.",
    whatItMeans: "The unemployment rate is the percentage of the labor force that is unemployed and actively seeking work.",
    source: "World Bank",
    format: "percent",
    chartTitle: "How does unemployment compare across countries?",
    chartSubtitle: "Share of the labor force without work, measured annually.",
  },
};

export function getIndicatorMetadata(indicatorId: string): IndicatorMetadata {
  return INDICATOR_METADATA[indicatorId] ?? {
    id: indicatorId,
    name: indicatorId,
    unit: "",
    frequency: "Annual",
    description: "World Bank indicator.",
    whatItMeans: "This measure comes from the World Bank and is reported annually.",
    source: "World Bank",
    format: "percent",
    chartTitle: `How does ${indicatorId} compare across countries?`,
    chartSubtitle: "Annual World Bank observation.",
  };
}
