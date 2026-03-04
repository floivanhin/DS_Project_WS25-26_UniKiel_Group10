const COLORS = {
  red: "#d20515",
  redDark: "#980211",
  redSoft: "rgba(210, 5, 21, 0.2)",
  neutral: "#575757",
  neutralSoft: "rgba(80, 80, 80, 0.25)",
  border: "#d9d9d9",
};

const CSV_FILES = {
  coreTeamAgeSummary: "data/other/bundesliga_team_age_summary.csv",
  coreSeasonAgeSummary: "data/other/bundesliga_season_age_summary.csv",
  rq4Ratings: "data/rq4/rq4_home_away_player_ratings.csv",
  rq4Delta: "data/rq4/rq4_player_home_away_delta.csv",
  rq9TeamAgeEfficiency: "data/rq9/rq9_team_age_vs_efficiency.csv",
  rq9TeamMatchEfficiency: "data/rq9/rq9_team_match_efficiency.csv",
  rq9OptimalAgeSummary: "data/rq9/rq9_optimal_age_summary.csv",
  rq9PlayerAgeProfile: "data/rq9/rq9_player_age_profile.csv",
  rq9PlayerBestAge: "data/rq9/rq9_player_best_age.csv",
};

const csvCache = new Map();

function initMenu() {
  const menuButton = document.querySelector(".menu-toggle");
  const nav = document.querySelector(".top-nav");

  if (!menuButton || !nav) return;

  menuButton.addEventListener("click", () => {
    nav.classList.toggle("open");
    menuButton.setAttribute("aria-expanded", nav.classList.contains("open") ? "true" : "false");
  });
}

function buildAxisGrid() {
  return { color: "#ececec" };
}

function setText(id, value) {
  const node = document.getElementById(id);
  if (node) node.textContent = value;
}

function toNumber(value) {
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : NaN;
}

function toBool(value) {
  return String(value).trim().toLowerCase() === "true";
}

function formatDecimal(value, digits = 2) {
  return Number.isFinite(value) ? value.toFixed(digits) : "n/a";
}

function formatSigned(value, digits = 3) {
  if (!Number.isFinite(value)) return "n/a";
  const prefix = value > 0 ? "+" : "";
  return `${prefix}${value.toFixed(digits)}`;
}

function formatCount(value) {
  return Number.isFinite(value) ? Math.round(value).toLocaleString("en-US") : "n/a";
}

function average(values) {
  const valid = values.filter((value) => Number.isFinite(value));
  if (!valid.length) return NaN;
  return valid.reduce((sum, value) => sum + value, 0) / valid.length;
}

function maxBy(rows, selector) {
  if (!rows.length) return null;
  return rows.reduce((best, row) => (selector(row) > selector(best) ? row : best));
}

function parseCsv(text) {
  const source = text.replace(/^\uFEFF/, "");
  const rows = [];
  let currentRow = [];
  let currentCell = "";
  let inQuotes = false;

  for (let i = 0; i < source.length; i += 1) {
    const char = source[i];

    if (char === '"') {
      if (inQuotes && source[i + 1] === '"') {
        currentCell += '"';
        i += 1;
      } else {
        inQuotes = !inQuotes;
      }
      continue;
    }

    if (char === "," && !inQuotes) {
      currentRow.push(currentCell);
      currentCell = "";
      continue;
    }

    if ((char === "\n" || char === "\r") && !inQuotes) {
      if (char === "\r" && source[i + 1] === "\n") i += 1;
      currentRow.push(currentCell);
      currentCell = "";
      if (currentRow.some((cell) => cell.length > 0)) rows.push(currentRow);
      currentRow = [];
      continue;
    }

    currentCell += char;
  }

  if (currentCell.length > 0 || currentRow.length > 0) {
    currentRow.push(currentCell);
    if (currentRow.some((cell) => cell.length > 0)) rows.push(currentRow);
  }

  if (!rows.length) return [];

  const headers = rows[0].map((cell) => cell.trim());
  return rows.slice(1).map((cells) => {
    const row = {};
    headers.forEach((header, index) => {
      row[header] = (cells[index] ?? "").trim();
    });
    return row;
  });
}

async function loadCsv(path) {
  if (!csvCache.has(path)) {
    const promise = fetch(path)
      .then((response) => {
        if (!response.ok) {
          throw new Error(`Failed to load ${path} via ${response.url} (${response.status})`);
        }
        return response.text();
      })
      .catch((error) => {
        throw new Error(`CSV load error for ${path} on ${window.location.pathname}: ${error.message}`);
      })
      .then(parseCsv);
    csvCache.set(path, promise);
  }
  return csvCache.get(path);
}

function buildTrendLine(points) {
  if (points.length < 2) return [];

  const n = points.length;
  const sumX = points.reduce((sum, point) => sum + point.x, 0);
  const sumY = points.reduce((sum, point) => sum + point.y, 0);
  const sumXY = points.reduce((sum, point) => sum + point.x * point.y, 0);
  const sumXX = points.reduce((sum, point) => sum + point.x * point.x, 0);
  const denominator = n * sumXX - sumX * sumX;
  if (denominator === 0) return [];

  const slope = (n * sumXY - sumX * sumY) / denominator;
  const intercept = (sumY - slope * sumX) / n;
  const xs = points.map((point) => point.x);
  const minX = Math.min(...xs);
  const maxX = Math.max(...xs);

  return [
    { x: minX, y: slope * minX + intercept },
    { x: maxX, y: slope * maxX + intercept },
  ];
}

function formatNamedList(rows, nameKey, valueKey, digits = 3, signed = false) {
  return rows
    .map((row) => {
      const value = toNumber(row[valueKey]);
      const formatted = signed ? formatSigned(value, digits) : formatDecimal(value, digits);
      return `${row[nameKey]} (${formatted})`;
    })
    .join(", ");
}

function buildRq4TopPlayerMetric(topHome, topAway) {
  if (!topHome && !topAway) return "n/a";
  if (topHome && topAway && topHome.player === topAway.player) {
    return `${topHome.player} ${formatDecimal(topHome.avg, 2)}/${formatDecimal(topAway.avg, 2)}`;
  }
  if (topHome && topAway) {
    return `Home ${topHome.player} ${formatDecimal(topHome.avg, 2)} | Away ${topAway.player} ${formatDecimal(topAway.avg, 2)}`;
  }
  if (topHome) return `Home ${topHome.player} ${formatDecimal(topHome.avg, 2)}`;
  return `Away ${topAway.player} ${formatDecimal(topAway.avg, 2)}`;
}

function renderOverviewChart(teamRows) {
  const chartNode = document.getElementById("teamAgeChart");
  if (!chartNode || typeof Chart === "undefined") return;

  new Chart(chartNode, {
    type: "bar",
    data: {
      labels: teamRows.map((row) => row.team),
      datasets: [
        {
          label: "Average age",
          data: teamRows.map((row) => row.avgAge),
          borderColor: COLORS.redDark,
          backgroundColor: COLORS.redSoft,
          borderWidth: 1.5,
          borderRadius: 6,
        },
      ],
    },
    options: {
      maintainAspectRatio: false,
      plugins: {
        legend: { display: false },
        tooltip: {
          callbacks: {
            label(context) {
              return `Age: ${context.raw.toFixed(2)}`;
            },
          },
        },
      },
      scales: {
        x: {
          ticks: {
            maxRotation: 55,
            minRotation: 55,
          },
          grid: { display: false },
        },
        y: {
          title: { display: true, text: "Years" },
          grid: buildAxisGrid(),
        },
      },
    },
  });
}

function renderRq4Charts(data) {
  if (typeof Chart === "undefined") return;

  const compareNode = document.getElementById("rq4CompareChart");
  if (compareNode) {
    new Chart(compareNode, {
      type: "bar",
      data: {
        labels: data.compareRows.map((row) => row.player),
        datasets: [
          {
            label: "Home avg rating",
            data: data.compareRows.map((row) => row.homeAvg),
            backgroundColor: "rgba(210, 5, 21, 0.72)",
            borderColor: COLORS.redDark,
            borderWidth: 1,
            borderRadius: 6,
          },
          {
            label: "Away avg rating",
            data: data.compareRows.map((row) => row.awayAvg),
            backgroundColor: "rgba(73, 73, 73, 0.62)",
            borderColor: "#333",
            borderWidth: 1,
            borderRadius: 6,
          },
        ],
      },
      options: {
        maintainAspectRatio: false,
        plugins: {
          legend: { position: "top" },
        },
        scales: {
          x: {
            ticks: {
              maxRotation: 55,
              minRotation: 55,
            },
            grid: { display: false },
          },
          y: {
            title: { display: true, text: "Rating" },
            grid: buildAxisGrid(),
          },
        },
      },
    });
  }

  const meanNode = document.getElementById("rq4MeanChart");
  if (meanNode) {
    const values = [data.meanHome, data.meanAway];
    const minValue = Math.min(...values);
    const maxValue = Math.max(...values);
    const padding = Math.max((maxValue - minValue) * 0.85, 0.02);

    new Chart(meanNode, {
      type: "bar",
      data: {
        labels: ["Home", "Away"],
        datasets: [
          {
            data: values,
            backgroundColor: ["rgba(210, 5, 21, 0.76)", "rgba(80, 80, 80, 0.62)"],
            borderColor: [COLORS.redDark, "#353535"],
            borderWidth: 1,
            borderRadius: 8,
          },
        ],
      },
      options: {
        maintainAspectRatio: false,
        plugins: {
          legend: { display: false },
          tooltip: {
            callbacks: {
              label(context) {
                return `Mean: ${context.raw.toFixed(3)}`;
              },
            },
          },
        },
        scales: {
          y: {
            min: Number((minValue - padding).toFixed(3)),
            max: Number((maxValue + padding).toFixed(3)),
            grid: buildAxisGrid(),
          },
          x: {
            grid: { display: false },
          },
        },
      },
    });
  }

  const deltaNode = document.getElementById("rq4DeltaChart");
  if (deltaNode) {
    const deltaValues = data.deltaRows.map((row) => row.delta);
    new Chart(deltaNode, {
      type: "bar",
      data: {
        labels: data.deltaRows.map((row) => row.player),
        datasets: [
          {
            label: "Delta (home minus away)",
            data: deltaValues,
            borderWidth: 1,
            borderColor: deltaValues.map((value) => (value >= 0 ? COLORS.redDark : "#3f3f3f")),
            backgroundColor: deltaValues.map((value) => (value >= 0 ? "rgba(210, 5, 21, 0.68)" : "rgba(66, 66, 66, 0.68)")),
            borderRadius: 6,
          },
        ],
      },
      options: {
        maintainAspectRatio: false,
        indexAxis: "y",
        plugins: {
          legend: { display: false },
          tooltip: {
            callbacks: {
              label(context) {
                return `Delta: ${context.raw.toFixed(3)}`;
              },
            },
          },
        },
        scales: {
          x: {
            title: { display: true, text: "Home minus Away" },
            grid: buildAxisGrid(),
          },
          y: {
            grid: { display: false },
          },
        },
      },
    });
  }
}

function renderRq9Charts(data) {
  if (typeof Chart === "undefined") return;

  const scatterNode = document.getElementById("rq9ScatterChart");
  if (scatterNode) {
    new Chart(scatterNode, {
      type: "scatter",
      data: {
        datasets: [
          {
            label: "Teams",
            data: data.scatterRows,
            backgroundColor: "rgba(210, 5, 21, 0.82)",
            borderColor: COLORS.redDark,
            pointRadius: 5.5,
            pointHoverRadius: 7,
          },
          {
            type: "line",
            label: "Trend line",
            data: data.trendLine,
            borderColor: "#444",
            borderWidth: 2,
            borderDash: [6, 5],
            pointRadius: 0,
            tension: 0,
          },
        ],
      },
      options: {
        maintainAspectRatio: false,
        parsing: false,
        plugins: {
          tooltip: {
            callbacks: {
              label(context) {
                const point = context.raw;
                const team = point.team ? `${point.team}: ` : "";
                return `${team}Age ${point.x.toFixed(2)}, Efficiency ${point.y.toFixed(3)}`;
              },
            },
          },
        },
        scales: {
          x: {
            title: { display: true, text: "Average team age" },
            grid: buildAxisGrid(),
          },
          y: {
            title: { display: true, text: "goals_per_shot" },
            grid: buildAxisGrid(),
          },
        },
      },
    });
  }

  const rankingNode = document.getElementById("rq9RankingChart");
  if (rankingNode) {
    const rankingValues = data.rankingRows.map((row) => row.goalsPerShot);
    new Chart(rankingNode, {
      type: "bar",
      data: {
        labels: data.rankingRows.map((row) => row.team),
        datasets: [
          {
            label: "goals_per_shot",
            data: rankingValues,
            backgroundColor: rankingValues.map((_, index) =>
              index < 5 ? "rgba(210, 5, 21, 0.85)" : "rgba(85, 85, 85, 0.65)"
            ),
            borderColor: rankingValues.map((_, index) => (index < 5 ? COLORS.redDark : "#3e3e3e")),
            borderWidth: 1,
            borderRadius: 6,
          },
        ],
      },
      options: {
        maintainAspectRatio: false,
        indexAxis: "y",
        plugins: {
          legend: { display: false },
        },
        scales: {
          x: {
            title: { display: true, text: "goals_per_shot" },
            grid: buildAxisGrid(),
          },
          y: {
            ticks: {
              font: { size: 10 },
            },
            grid: { display: false },
          },
        },
      },
    });
  }

  const ageProfileNode = document.getElementById("rq9AgeProfileChart");
  if (ageProfileNode) {
    new Chart(ageProfileNode, {
      data: {
        labels: data.ageProfileRows.map((row) => row.ageInt),
        datasets: [
          {
            type: "bar",
            label: "Total shots",
            data: data.ageProfileRows.map((row) => row.totalShots),
            yAxisID: "yShots",
            backgroundColor: "rgba(110, 110, 110, 0.45)",
            borderColor: "#5f5f5f",
            borderWidth: 1,
            borderRadius: 5,
          },
          {
            type: "line",
            label: "goals_per_shot",
            data: data.ageProfileRows.map((row) => row.goalsPerShot),
            yAxisID: "yEff",
            borderColor: COLORS.redDark,
            backgroundColor: "rgba(210, 5, 21, 0.2)",
            pointBackgroundColor: COLORS.red,
            pointBorderColor: COLORS.redDark,
            pointRadius: 4,
            tension: 0.25,
          },
        ],
      },
      options: {
        maintainAspectRatio: false,
        plugins: {
          legend: {
            position: "top",
          },
        },
        scales: {
          x: {
            title: { display: true, text: "Age band" },
            grid: { display: false },
          },
          yEff: {
            type: "linear",
            position: "left",
            min: 0,
            title: { display: true, text: "goals_per_shot" },
            grid: buildAxisGrid(),
          },
          yShots: {
            type: "linear",
            position: "right",
            title: { display: true, text: "total_shots" },
            grid: { drawOnChartArea: false },
          },
        },
      },
    });
  }
}

async function renderOverviewPage() {
  const [teamSummaryRaw, seasonSummaryRaw, rq9MatchRaw] = await Promise.all([
    loadCsv(CSV_FILES.coreTeamAgeSummary),
    loadCsv(CSV_FILES.coreSeasonAgeSummary),
    loadCsv(CSV_FILES.rq9TeamMatchEfficiency),
  ]);

  const seasonRow = seasonSummaryRaw[0] ?? {};
  const teamRows = teamSummaryRaw
    .map((row) => ({
      team: row.team,
      avgAge: toNumber(row.avg_age),
    }))
    .filter((row) => Number.isFinite(row.avgAge))
    .sort((a, b) => a.avgAge - b.avgAge);

  const uniquePlayers = toNumber(seasonRow.unique_players);
  const avgAge = toNumber(seasonRow.avg_age);
  const minAge = toNumber(seasonRow.min_age);
  const maxAge = toNumber(seasonRow.max_age);
  const seasonLabel = seasonRow.season_label || "n/a";

  setText("ov-chip-season", seasonLabel);
  setText("ov-chip-players", `${formatCount(uniquePlayers)} players`);
  setText("ov-chip-teams", `${formatCount(teamRows.length)} teams`);
  setText("ov-metric-players", formatCount(uniquePlayers));
  setText("ov-metric-avg-age", formatDecimal(avgAge, 2));
  setText("ov-metric-age-range", `${formatDecimal(minAge, 2)}-${formatDecimal(maxAge, 2)}`);
  setText("ov-metric-team-match-rows", formatCount(rq9MatchRaw.length));

  if (teamRows.length) {
    const youngest = teamRows[0];
    const oldest = teamRows[teamRows.length - 1];
    setText("ov-youngest-team", `${youngest.team} (${formatDecimal(youngest.avgAge, 2)})`);
    setText("ov-oldest-team", `${oldest.team} (${formatDecimal(oldest.avgAge, 2)})`);
  }

  renderOverviewChart(teamRows);
}

async function renderRq4Page() {
  const [ratingsRaw, deltaRaw] = await Promise.all([loadCsv(CSV_FILES.rq4Ratings), loadCsv(CSV_FILES.rq4Delta)]);

  const ratingRows = ratingsRaw.map((row) => ({
    player: row.player,
    homeAway: row.home_away,
    avg: toNumber(row.avg_overall_rating),
    eligibleForLeaderboard: toBool(row.eligible_for_leaderboard),
  }));

  const deltaRows = deltaRaw.map((row) => ({
    player: row.player,
    homeAvg: toNumber(row.home_avg_overall_rating),
    awayAvg: toNumber(row.away_avg_overall_rating),
    delta: toNumber(row.avg_rating_delta_home_minus_away),
    absDelta: toNumber(row.abs_avg_rating_delta),
    eligibleBothSides: toBool(row.eligible_both_sides),
  }));

  const leaderboardRows = ratingRows.filter(
    (row) => row.eligibleForLeaderboard && Number.isFinite(row.avg) && (row.homeAway === "home" || row.homeAway === "away")
  );
  const homeRows = leaderboardRows.filter((row) => row.homeAway === "home");
  const awayRows = leaderboardRows.filter((row) => row.homeAway === "away");

  const meanHome = average(homeRows.map((row) => row.avg));
  const meanAway = average(awayRows.map((row) => row.avg));
  const meanDelta = meanHome - meanAway;

  const topHome = maxBy(homeRows, (row) => row.avg);
  const topAway = maxBy(awayRows, (row) => row.avg);

  const eligibleDeltaRows = deltaRows.filter(
    (row) =>
      row.eligibleBothSides &&
      Number.isFinite(row.homeAvg) &&
      Number.isFinite(row.awayAvg) &&
      Number.isFinite(row.delta) &&
      Number.isFinite(row.absDelta)
  );

  const compareRows = [...eligibleDeltaRows].sort((a, b) => b.absDelta - a.absDelta).slice(0, 10);
  const topPositive = [...eligibleDeltaRows]
    .filter((row) => row.delta > 0)
    .sort((a, b) => b.delta - a.delta);
  const topNegative = [...eligibleDeltaRows]
    .filter((row) => row.delta < 0)
    .sort((a, b) => a.delta - b.delta);
  const deltaChartRows = [...topPositive.slice(0, 6), ...topNegative.slice(0, 6)];

  setText("rq4-chip-ratings-rows", formatCount(ratingRows.length));
  setText("rq4-chip-player-comparisons", formatCount(deltaRows.length));
  setText("rq4-chip-eligible-both", formatCount(eligibleDeltaRows.length));

  setText("rq4-metric-home-mean", formatDecimal(meanHome, 3));
  setText("rq4-metric-away-mean", formatDecimal(meanAway, 3));
  setText("rq4-metric-home-away-delta", formatSigned(meanDelta, 3));
  setText("rq4-metric-top-player", buildRq4TopPlayerMetric(topHome, topAway));

  if (topPositive.length) {
    setText("rq4-key-positive", `Strongest positive deltas: ${formatNamedList(topPositive.slice(0, 3), "player", "delta", 3, true)}.`);
  }
  if (topNegative.length) {
    setText("rq4-key-negative", `Strongest negative deltas: ${formatNamedList(topNegative.slice(0, 3), "player", "delta", 3, true)}.`);
  }
  if (topHome && topAway) {
    const topText =
      topHome.player === topAway.player
        ? `The top home and away average rating is ${topHome.player}.`
        : `Top home average rating: ${topHome.player}; top away average rating: ${topAway.player}.`;
    setText("rq4-key-top-player", topText);
  }

  renderRq4Charts({
    compareRows,
    meanHome,
    meanAway,
    deltaRows: deltaChartRows,
  });
}

async function renderRq9Page() {
  const [teamRaw, matchRaw, optimalRaw, ageProfileRaw, bestAgeRaw] = await Promise.all([
    loadCsv(CSV_FILES.rq9TeamAgeEfficiency),
    loadCsv(CSV_FILES.rq9TeamMatchEfficiency),
    loadCsv(CSV_FILES.rq9OptimalAgeSummary),
    loadCsv(CSV_FILES.rq9PlayerAgeProfile),
    loadCsv(CSV_FILES.rq9PlayerBestAge),
  ]);

  const teamRows = teamRaw
    .map((row) => ({
      team: row.team,
      seasonLabel: row.season_label,
      avgAge: toNumber(row.avg_age),
      goalsPerShot: toNumber(row.goals_per_shot),
    }))
    .filter((row) => Number.isFinite(row.avgAge) && Number.isFinite(row.goalsPerShot));

  const rankingRows = [...teamRows].sort((a, b) => b.goalsPerShot - a.goalsPerShot);
  const lowRows = [...teamRows].sort((a, b) => a.goalsPerShot - b.goalsPerShot).slice(0, 3);
  const scatterRows = teamRows.map((row) => ({
    x: row.avgAge,
    y: row.goalsPerShot,
    team: row.team,
  }));
  const trendLine = buildTrendLine(scatterRows);

  const ageProfileRows = ageProfileRaw
    .map((row) => ({
      ageInt: toNumber(row.age_int),
      goalsPerShot: toNumber(row.goals_per_shot),
      totalShots: toNumber(row.total_shots),
    }))
    .filter((row) => Number.isFinite(row.ageInt) && Number.isFinite(row.goalsPerShot) && Number.isFinite(row.totalShots))
    .sort((a, b) => a.ageInt - b.ageInt);

  const optimalRow = optimalRaw.find((row) => row.scope === "single_season") || optimalRaw[0] || {};
  const bestAgeRow = bestAgeRaw.find((row) => row.season !== "all") || bestAgeRaw[0] || {};

  const pearson = toNumber(optimalRow.pearson_r_age_efficiency);
  const minAvgAge = Math.min(...teamRows.map((row) => row.avgAge));
  const maxAvgAge = Math.max(...teamRows.map((row) => row.avgAge));
  const bestAgeInt = toNumber(bestAgeRow.best_age_int);
  const bestBandEfficiency = toNumber(bestAgeRow.goals_per_shot);
  const bestBandGoals = toNumber(bestAgeRow.total_goals);
  const bestBandShots = toNumber(bestAgeRow.total_shots);
  const seasonLabel = teamRows[0]?.seasonLabel || "n/a";

  setText("rq9-chip-teams", formatCount(teamRows.length));
  setText("rq9-chip-team-match-rows", formatCount(matchRaw.length));
  setText("rq9-chip-pearson", formatDecimal(pearson, 3));
  setText("rq9-chip-season", seasonLabel);

  setText("rq9-metric-pearson", formatDecimal(pearson, 3));
  setText("rq9-metric-age-range", `${formatDecimal(minAvgAge, 2)}-${formatDecimal(maxAvgAge, 2)}`);
  setText("rq9-metric-best-age", `${formatCount(bestAgeInt)} years`);
  setText(
    "rq9-metric-band-efficiency",
    `${formatDecimal(bestBandEfficiency, 3)} (${formatCount(bestBandGoals)}/${formatCount(bestBandShots)})`
  );

  if (rankingRows.length) {
    setText("rq9-key-top", `Top efficiency: ${formatNamedList(rankingRows.slice(0, 3), "team", "goalsPerShot", 3)}.`);
  }
  if (lowRows.length) {
    setText("rq9-key-low", `Low efficiency: ${formatNamedList(lowRows, "team", "goalsPerShot", 3)}.`);
  }
  if (optimalRow.model_note) {
    setText("rq9-key-model-note", `Model note: ${optimalRow.model_note}`);
  }

  renderRq9Charts({
    scatterRows,
    trendLine,
    rankingRows,
    ageProfileRows,
  });
}

async function renderCurrentPage() {
  const page = document.body.dataset.page;
  if (page === "overview") await renderOverviewPage();
  if (page === "rq4") await renderRq4Page();
  if (page === "rq9") await renderRq9Page();
}

document.addEventListener("DOMContentLoaded", () => {
  initMenu();
  renderCurrentPage().catch((error) => {
    console.error("Failed to load web-statistics data from CSV outputs.", error);
  });
});
