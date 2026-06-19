import { Doughnut } from 'react-chartjs-2'
import { Chart as ChartJS, ArcElement, Tooltip, Legend } from 'chart.js'
import { categoryColor, formatCLP } from '../utils/categoryColors'
import { useChartTheme } from '../hooks/useChartTheme'

ChartJS.register(ArcElement, Tooltip, Legend)

interface CatTotal {
  category_name: string
  total: string
  net_total: string
}

interface Props {
  data: CatTotal[]
  selectedCategories: Set<string>
}

export default function CategoryDoughnut({ data, selectedCategories }: Props) {
  const filtered = data.filter((d) => selectedCategories.has(d.category_name)).slice(0, 10)
  const ct = useChartTheme()

  const chartData = {
    labels: filtered.map((d) => d.category_name),
    datasets: [
      {
        data: filtered.map((d) => parseFloat(d.net_total)),
        backgroundColor: filtered.map((d) => categoryColor(d.category_name)),
        borderWidth: 2,
        borderColor: ct.doughnutBorderColor,
      },
    ],
  }

  return (
    <Doughnut
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
              label: (ctx) => {
                const value = ctx.parsed
                const dataset = ctx.dataset.data as number[]
                const sum = dataset.reduce((acc, v) => acc + (v || 0), 0)
                const pct = sum > 0 ? (value / sum) * 100 : 0
                return `${formatCLP(value)} (${pct.toFixed(1)}%)`
              },
            },
          },
        },
      }}
    />
  )
}
