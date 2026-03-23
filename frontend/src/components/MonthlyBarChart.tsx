import { Bar } from 'react-chartjs-2'
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip,
  Legend,
} from 'chart.js'
import { categoryColor, formatCLP } from '../utils/categoryColors'
import { useChartTheme } from '../hooks/useChartTheme'

ChartJS.register(CategoryScale, LinearScale, BarElement, Title, Tooltip, Legend)

interface CatTotal {
  category_name: string
  total: string
  net_total: string
}

interface Props {
  data: CatTotal[]
  selectedCategories: Set<string>
}

export default function CategoryBarChart({ data, selectedCategories }: Props) {
  const filtered = data.filter((d) => selectedCategories.has(d.category_name))
  const ct = useChartTheme()

  const chartData = {
    labels: filtered.map((d) => d.category_name),
    datasets: [
      {
        label: 'Total',
        data: filtered.map((d) => parseFloat(d.net_total)),
        backgroundColor: filtered.map((d) => categoryColor(d.category_name)),
        borderRadius: 4,
      },
    ],
  }

  return (
    <Bar
      data={chartData}
      options={{
        responsive: true,
        plugins: {
          legend: { display: false },
          tooltip: {
            backgroundColor: ct.tooltipBg,
            titleColor: ct.tooltipText,
            bodyColor: ct.tooltipText,
            borderColor: ct.tooltipBorder,
            borderWidth: 1,
            callbacks: {
              label: (ctx) => formatCLP(ctx.parsed.y ?? 0),
            },
          },
        },
        scales: {
          y: {
            beginAtZero: true,
            grid: { color: ct.gridColor },
            ticks: { color: ct.tickColor },
          },
          x: {
            grid: { display: false },
            ticks: { color: ct.tickColor },
          },
        },
      }}
    />
  )
}
