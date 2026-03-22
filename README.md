# DS_Project_WS25-26_UniKiel_Group10

Group 10 data science project for the University of Kiel, winter semester 2025/2026.

This project focuses on **Bundesliga 2024/2025** football data and combines a **Python backend** for data collection and analysis with a **Vue 3 frontend dashboard** for interactive visualization.

---

## Project Overview

The repository is divided into two main parts:

- **Backend**  
  Python-based data processing and analysis pipelines for multiple research questions.

- **Bundesliga Statistics Page**  
  A Vue 3 dashboard for visualizing football statistics and weather-related match insights.

Some research questions are organized in separate folders, depending on their implementation and data sources.

---

## Project Structure

```text
.
├── backend/
│   ├── RQ1/
│   ├── RQ2/
│   ├── RQ3_RQ8/
│   ├── RQ4_RQ8/
│   ├── RQ5/
│   └── RQ7/
│
├── bundesliga-statistics-page/
│   └── (Vue 3 frontend application)
│
└── info/
    └── (topics and presentations)
```

---

# Backend

The `backend/` folder contains the Python-based analysis workflows and data pipelines.

## Main folders

- `RQ1/`
- `RQ2/`
- `RQ3_RQ8/`
- `RQ4_RQ8/`
- `RQ5/`
- `RQ7/`

---

### Files in `RQ4_RQ8`

- `main.py`  
  Runs the complete workflow

- `espn_data_download_pipeline.py`  
  Builds the raw ESPN table for RQ8

- `whoscored_data_download_pipeline.py`  
  Builds the raw WhoScored table for RQ4

- `rq4_analysis.py`  
  Generates the RQ4 result tables

- `rq8_analysis.py`  
  Generates the RQ8 result tables

---

# Frontend – Bundesliga Statistics Page

The `bundesliga statistics page/` folder contains a small **Vue 3 dashboard** for interactive analysis and visualization of Bundesliga statistics.

In particular, it is used to explore how factors such as **weather conditions during matches** may influence **goal scoring**, alongside other football-related visual insights.

---

## Technologies Used

- Vue 3
- TypeScript
- Vite
- Vue Router
- Plotly.js

---

## Prerequisites

Before running the frontend, make sure the following are installed:

- **Node.js**
- **npm**

You can check this with:

```bash
node -v
npm -v
```

---

## Installing dependencies

Inside the frontend folder, run:

```bash
npm install
npm install plotly.js-dist-min
npm install vue-router
```

---

## Running the frontend

Start the development server with:

```bash
npm run dev
```

After that, Vite will provide a local development URL in the terminal.

---

# Suggested Workflow

A typical workflow for the project looks like this:

1. Run the **backend** scripts to collect and analyze Bundesliga data
2. Generate the necessary CSV and JSON output files
3. Use the **frontend dashboard** to visualize and explore the results interactively

---

# Notes

- The backend and frontend are stored in **separate large folders**
- The backend is responsible for **data collection, preprocessing, and analysis**
- The frontend is responsible for **interactive presentation and visualization**
- Some research questions are implemented in dedicated folders, while others share combined pipelines

---

## Authors

University of Kiel – Data Science Project  
Winter Semester 2025/2026 – Group 10

- Tino Hinrichs
- Florian Hinrichsen
- Kirill Norinskiy
- Cat Lam Tang
