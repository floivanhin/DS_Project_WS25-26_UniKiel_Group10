<template>
  <div>
    <h3>Research Question 2: How does the matchday affect the amount of goals?</h3>
    <hr />
    <div>
      <label v-for="opt in options" :key="opt" style="margin-right:12px;">
        <input type="radio" name="chartType" :value="opt" v-model="chartType" />
        {{ opt }}
      </label>
    </div>

    <div ref="plot" style="width:100%;height:600px;margin-top:12px;"></div>
  </div>
</template>

<script>
import Plotly from "plotly.js-dist-min";

export default {
  name: "GoalsByMatchday",
  data() {
    return {
      options: ["bar", "histogram", "line"],
      chartType: "bar",
      df: null,
      yColumns: [
        "total_goals_2020-2021",
        "total_goals_2021-2022",
        "total_goals_2022-2023",
        "total_goals_2023-2024",
        "total_goals_2024-2025",
      ],
    };
  },
  watch: {
    chartType() {
      this.drawPlot();
    },
  },
  mounted() {
    this.loadData();
  },
  methods: {
    async loadData() {
      const res = await fetch("/data/data_goals.csv");
      const text = await res.text();
      this.df = this.parseCSV(text);
      this.drawPlot();
    },
    parseCSV(text) {
      const lines = text.trim().split(/\r?\n/);
      if (!lines.length) return [];
      const headers = lines[0].split(",").map(h => h.trim());
      return lines.slice(1).map(line => {
        const cols = line.split(",").map(c => c.trim());
        const obj = {};
        headers.forEach((h, i) => {
          const val = cols[i] === undefined ? "" : cols[i];
          // try to convert numeric values
          const num = Number(val);
          obj[h] = val !== "" && !Number.isNaN(num) ? num : val;
        });
        return obj;
      });
    },
    drawPlot() {
      if (!this.df || !this.df.length) return;
      const x = this.df.map(r => r.matchday);

      const traces = this.yColumns
        .filter(col => col in this.df[0])
        .map(col => {
          const y = this.df.map(r => r[col]);
          const name = col;
          if (this.chartType === "bar") {
            return {
              x,
              y,
              name,
              type: "bar",
            };
          }
          if (this.chartType === "histogram") {
            return {
              x,
              y,
              name,
              type: "histogram",
            };
          }
          // line
          return {
            x,
            y,
            name,
            type: "scatter",
            mode: "lines+markers",
          };
        });

      const layout = {
        xaxis: { title: "Matchday" },
        yaxis: { title: "goals" },
        barmode: this.chartType === 'bar' ? 'group' : 'overlay',
        margin: { t: 30, r: 20, l: 50, b: 50 },
        legend: { orientation: "h", y: -0.15 },
      };

      Plotly.react(this.$refs.plot, traces, layout, { responsive: true });
    },
  },
};
</script>

<style scoped>
@media (max-width: 600px) {
  div[ref="plot"] {
    height: 400px;
  }
}
</style>
