// GitHub Pages (or a local static server) serves these files. Python runs at API.
const API = "https://sd5913-week04-tides.venetanji.workers.dev";
const monthPicker = document.querySelector("#month");
const dayPicker = document.querySelector("#day");
const status = document.querySelector("#status");
const chart = document.querySelector("#chart");
let rows = [];
let currentRequest = 0;

for (let month = 1; month <= 12; month++) {
  const name = new Date(2026, month - 1, 1).toLocaleString("en", { month: "long" });
  monthPicker.add(new Option(name, month));
}
monthPicker.value = "9";

async function loadMonth() {
  // A slower old reply must not replace a newer selection.
  const request = ++currentRequest;
  const month = monthPicker.value;
  const url = API + "/tides?month=" + month;
  document.querySelector("#request-link").href = url;
  dayPicker.disabled = true;
  dayPicker.replaceChildren();
  chart.setAttribute("hidden", "");
  document.querySelector("#caption").textContent = "";
  status.textContent = "Loading tide records…";
  try {
    const response = await fetch(url);
    if (!response.ok) throw new Error("HTTP " + response.status);
    const received = await response.json();
    if (request !== currentRequest) return;
    if (!Array.isArray(received) || received.length === 0) {
      throw new Error("No daily records returned");
    }
    rows = received;
    for (const row of rows) dayPicker.add(new Option(row.day, row.day));
    dayPicker.disabled = false;
    status.textContent = rows.length + " daily records received. Choose a day.";
    showDay();
  } catch (error) {
    if (request !== currentRequest) return;
    dayPicker.disabled = true;
    status.textContent = "Could not load the records: " + error.message + ". Check your connection, then choose a month to retry.";
  }
}

function showDay() {
  const record = rows.find(row => row.day === Number(dayPicker.value));
  if (!record) return;
  drawChart(record.heights);
  const date = `2026-${String(record.month).padStart(2, "0")}-${String(record.day).padStart(2, "0")}`;
  document.querySelector("#caption").textContent = date + " · 24 hourly heights";
  document.querySelector("#chart-title").textContent = "Tide heights for " + date;
}

function drawChart(heights) {
  // Fixed 0–3 m scale so changing the day does not change the meaning of height.
  const x = index => 70 + index / 23 * 790;
  const y = height => 290 - height / 3 * 240;
  const axes = document.querySelector("#axes");
  axes.replaceChildren();
  function element(tag, attributes, text = "") {
    const node = document.createElementNS("http://www.w3.org/2000/svg", tag);
    for (const [name, value] of Object.entries(attributes)) node.setAttribute(name, value);
    node.textContent = text;
    axes.append(node);
  }
  for (let metres = 0; metres <= 3; metres++) {
    element("line", { x1: 70, x2: 860, y1: y(metres), y2: y(metres), stroke: "#ddd" });
    element("text", { x: 58, y: y(metres) + 6, "text-anchor": "end", "font-size": 18 }, metres + " m");
  }
  for (const hour of [1, 6, 12, 18, 24]) {
    element("text", { x: x(hour - 1), y: 319, "text-anchor": "middle", "font-size": 18 }, String(hour));
  }
  element("text", { x: 465, y: 348, "text-anchor": "middle", "font-size": 18 }, "Hour (Hong Kong time)");
  document.querySelector("#line").setAttribute("points", heights.map((height, i) => `${x(i)},${y(height)}`).join(" "));
  chart.removeAttribute("hidden");
}

// Event callbacks: month changes request data; day changes only redraw the chart.
monthPicker.addEventListener("change", loadMonth);
dayPicker.addEventListener("change", showDay);
loadMonth();
