const SUBJECTS = ["Maths", "Science", "English", "History"];
const REQUIRED_COLUMNS = [
  "Student ID",
  "Name",
  "Gender",
  "Class",
  ...SUBJECTS,
  "Attendance",
  "AssignmentScore",
];
const GRADE_COLORS = {
  A: "#24a36a",
  B: "#5b7ef0",
  C: "#eca936",
  D: "#e87858",
  F: "#d84f4f",
};

let students = [];
let analysis = null;
let installPrompt = null;

const elements = {
  notice: document.querySelector("#notice"),
  studentCount: document.querySelector("#student-count"),
  classCount: document.querySelector("#class-count"),
  classAverage: document.querySelector("#class-average"),
  passRate: document.querySelector("#pass-rate"),
  topPerformer: document.querySelector("#top-performer"),
  topScore: document.querySelector("#top-score"),
  subjectChart: document.querySelector("#subject-chart"),
  gradeChart: document.querySelector("#grade-chart"),
  classFilter: document.querySelector("#class-filter"),
  search: document.querySelector("#student-search"),
  studentRows: document.querySelector("#student-rows"),
  studentResultCount: document.querySelector("#student-result-count"),
  emptyState: document.querySelector("#empty-state"),
  emptyTitle: document.querySelector("#empty-title"),
  emptyCopy: document.querySelector("#empty-copy"),
  dataSource: document.querySelector("#data-source"),
  csvFile: document.querySelector("#csv-file"),
  importButton: document.querySelector("#import-button"),
  addButton: document.querySelector("#add-button"),
  emptyAddButton: document.querySelector("#empty-add-button"),
  templateButton: document.querySelector("#template-button"),
  studentDialog: document.querySelector("#student-dialog"),
  studentForm: document.querySelector("#student-form"),
  cancelStudent: document.querySelector("#cancel-student"),
  exportButton: document.querySelector("#export-button"),
  installButton: document.querySelector("#install-button"),
};

const STORAGE_KEY = "student-performance-data-v1";

function showNotice(message, isError = false) {
  elements.notice.textContent = message;
  elements.notice.classList.add("visible");
  elements.notice.classList.toggle("error", isError);
}

function clearNotice() {
  elements.notice.textContent = "";
  elements.notice.classList.remove("visible", "error");
}

function parseCsv(text) {
  const records = [];
  let record = [];
  let field = "";
  let quoted = false;

  for (let index = 0; index < text.length; index += 1) {
    const character = text[index];
    if (quoted) {
      if (character === '"' && text[index + 1] === '"') {
        field += '"';
        index += 1;
      } else if (character === '"') {
        quoted = false;
      } else {
        field += character;
      }
    } else if (character === '"' && field.length === 0) {
      quoted = true;
    } else if (character === ",") {
      record.push(field);
      field = "";
    } else if (character === "\n" || character === "\r") {
      if (character === "\r" && text[index + 1] === "\n") index += 1;
      record.push(field);
      if (record.some((value) => value.trim() !== "")) records.push(record);
      record = [];
      field = "";
    } else {
      field += character;
    }
  }
  if (quoted) throw new Error("The CSV contains an unclosed quoted value.");
  record.push(field);
  if (record.some((value) => value.trim() !== "")) records.push(record);
  if (records.length < 2) throw new Error("The CSV does not contain any student records.");

  const headers = records[0].map((header) => header.trim().replace(/^\uFEFF/, ""));
  const missing = REQUIRED_COLUMNS.filter((column) => !headers.includes(column));
  if (missing.length) throw new Error(`Missing CSV columns: ${missing.join(", ")}.`);

  const rows = records.slice(1).map((values) => {
    const row = Object.fromEntries(headers.map((header, column) => [header, (values[column] || "").trim()]));
    return row;
  });
  validateStudents(rows);
  return rows;
}

function validateStudents(rows) {
  if (!rows.length) throw new Error("Add at least one student before analyzing data.");
  rows.forEach((row, index) => {
    for (const column of REQUIRED_COLUMNS) {
      if (!String(row[column] || "").trim()) throw new Error(`Row ${index + 2} is missing "${column}".`);
    }
    for (const column of [...SUBJECTS, "Attendance", "AssignmentScore"]) {
      const number = Number(row[column]);
      if (!Number.isFinite(number) || number < 0 || number > 100) {
        throw new Error(`Row ${index + 2}: "${column}" must be a number from 0 to 100.`);
      }
    }
  });
  return rows;
}

function saveStudents(rows) {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(rows));
}

function overallScore(student) {
  return SUBJECTS.reduce((total, subject) => total + Number(student[subject]), 0) / SUBJECTS.length;
}

function gradeFor(score) {
  if (score >= 85) return "A";
  if (score >= 70) return "B";
  if (score >= 55) return "C";
  if (score >= 40) return "D";
  return "F";
}

function calculateAnalysis(rows) {
  const scores = rows.map(overallScore);
  const subjectAverages = Object.fromEntries(
    SUBJECTS.map((subject) => [
      subject,
      rows.reduce((total, student) => total + Number(student[subject]), 0) / rows.length,
    ]),
  );
  const gradeDistribution = Object.fromEntries(["A", "B", "C", "D", "F"].map((grade) => [grade, 0]));
  scores.forEach((score) => {
    gradeDistribution[gradeFor(score)] += 1;
  });
  return {
    average: scores.reduce((total, score) => total + score, 0) / rows.length,
    passRate: (scores.filter((score) => score >= 50).length / rows.length) * 100,
    best: rows[scores.indexOf(Math.max(...scores))],
    subjectAverages,
    gradeDistribution,
  };
}

function renderDashboard(source) {
  analysis = calculateAnalysis(students);
  elements.exportButton.disabled = false;
  const bestScore = overallScore(analysis.best);
  const classes = [...new Set(students.map((student) => student.Class))].sort((a, b) =>
    a.localeCompare(b, undefined, { numeric: true }),
  );

  elements.studentCount.textContent = String(students.length);
  elements.classCount.textContent = `${classes.length} ${classes.length === 1 ? "class" : "classes"}`;
  elements.classAverage.textContent = `${analysis.average.toFixed(1)}%`;
  elements.passRate.textContent = `${analysis.passRate.toFixed(0)}%`;
  elements.topPerformer.textContent = analysis.best.Name;
  elements.topScore.textContent = `${bestScore.toFixed(1)}% overall average`;
  elements.dataSource.textContent = `Data source: ${source}`;

  const previousClass = elements.classFilter.value;
  elements.classFilter.innerHTML = [
    '<option value="all">All classes</option>',
    ...classes.map((className) => `<option value="${escapeHtml(className)}">${escapeHtml(`Class ${className}`)}</option>`),
  ].join("");
  elements.classFilter.value = classes.includes(previousClass) ? previousClass : "all";

  elements.subjectChart.innerHTML = SUBJECTS.map((subject) => {
    const average = analysis.subjectAverages[subject];
    return `<div class="subject-row">
      <span>${escapeHtml(subject)}</span>
      <div class="bar-track" aria-label="${escapeHtml(subject)} average ${average.toFixed(1)}%">
        <div class="bar-fill" style="width:${average.toFixed(2)}%"></div>
      </div>
      <span class="subject-value">${average.toFixed(1)}%</span>
    </div>`;
  }).join("");

  const maxGradeCount = Math.max(...Object.values(analysis.gradeDistribution), 1);
  elements.gradeChart.innerHTML = Object.entries(analysis.gradeDistribution)
    .map(([grade, count]) => {
      const height = Math.max((count / maxGradeCount) * 100, 3);
      return `<div class="grade-column" aria-label="Grade ${grade}: ${count} students">
        <span class="grade-count">${count}</span>
        <div class="grade-bar-wrap"><div class="grade-bar" style="height:${height}%;background:${GRADE_COLORS[grade]}"></div></div>
        <span>${grade}</span>
      </div>`;
    })
    .join("");

  renderStudents();
}

function renderStudents() {
  const query = elements.search.value.trim().toLocaleLowerCase();
  const selectedClass = elements.classFilter.value;
  const visibleStudents = students
    .filter((student) => {
      const matchesClass = selectedClass === "all" || student.Class === selectedClass;
      const matchesSearch =
        !query ||
        student.Name.toLocaleLowerCase().includes(query) ||
        student["Student ID"].toLocaleLowerCase().includes(query);
      return matchesClass && matchesSearch;
    })
    .sort((a, b) => a.Name.localeCompare(b.Name));

  elements.studentRows.innerHTML = visibleStudents
    .map((student) => {
      const average = overallScore(student);
      const grade = gradeFor(average);
      return `<tr>
        <td><span class="student-name">${escapeHtml(student.Name)}</span><span class="student-id">${escapeHtml(student["Student ID"])}</span></td>
        <td>${escapeHtml(student.Class)}</td>
        <td>${average.toFixed(1)}%</td>
        <td><span class="grade-pill grade-${grade.toLowerCase()}">${grade}</span></td>
        <td>${Number(student.Attendance).toFixed(0)}%</td>
      </tr>`;
    })
    .join("");
  elements.studentResultCount.textContent = `${visibleStudents.length} of ${students.length} students`;
  elements.emptyState.hidden = visibleStudents.length !== 0;
  if (students.length === 0) {
    elements.emptyTitle.textContent = "Your dashboard starts here";
    elements.emptyCopy.textContent = "Add a student or import a CSV to see class insights. Your data stays in this browser.";
  } else if (visibleStudents.length === 0) {
    elements.emptyTitle.textContent = "No students found";
    elements.emptyCopy.textContent = "Try a different name, ID, or class filter.";
  }
}

function escapeHtml(value) {
  return String(value).replace(/[&<>"']/g, (character) => {
    const replacements = { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" };
    return replacements[character];
  });
}

function buildReport() {
  const lines = [
    "Student Performance Analyser",
    "============================",
    "",
    `Total Students: ${students.length}`,
    `Average Overall Score: ${analysis.average.toFixed(2)}%`,
    `Pass Rate: ${analysis.passRate.toFixed(2)}%`,
    "",
    `Top Performer: ${analysis.best.Name} (${analysis.best.Class}) - ${overallScore(analysis.best).toFixed(2)}%`,
    "",
    "Subject-wise Average Scores:",
    ...SUBJECTS.map((subject) => `- ${subject}: ${analysis.subjectAverages[subject].toFixed(2)}%`),
    "",
    "Grade Distribution:",
    ...Object.entries(analysis.gradeDistribution).map(([grade, count]) => `- Grade ${grade}: ${count} students`),
  ];
  return `${lines.join("\n")}\n`;
}

function loadSavedData() {
  try {
    const saved = localStorage.getItem(STORAGE_KEY);
    if (saved !== null) {
      students = validateStudents(JSON.parse(saved));
      renderDashboard("Saved in this browser");
      clearNotice();
      return;
    }
  } catch (error) {
    showNotice(`Could not load saved data: ${error.message}. Import a CSV or add a student to continue.`, true);
    return;
  }

  elements.studentResultCount.textContent = "0 students";
  renderStudents();
  elements.exportButton.disabled = true;
  clearNotice();
}

elements.importButton.addEventListener("click", () => elements.csvFile.click());
elements.csvFile.addEventListener("change", async () => {
  const [file] = elements.csvFile.files;
  if (!file) return;
  try {
    const imported = parseCsv(await file.text());
    saveStudents(imported);
    students = imported;
    renderDashboard(file.name);
    clearNotice();
  } catch (error) {
    showNotice(error.message, true);
  } finally {
    elements.csvFile.value = "";
  }
});

elements.addButton.addEventListener("click", () => elements.studentDialog.showModal());
elements.emptyAddButton.addEventListener("click", () => elements.studentDialog.showModal());
elements.cancelStudent.addEventListener("click", () => elements.studentDialog.close());
elements.studentForm.addEventListener("submit", (event) => {
  event.preventDefault();
  const row = Object.fromEntries(new FormData(elements.studentForm).entries());
  const updated = [...students, row];
  try {
    validateStudents(updated);
    saveStudents(updated);
    students = updated;
    renderDashboard("Saved in this browser");
    elements.studentForm.reset();
    elements.studentDialog.close();
    clearNotice();
  } catch (error) {
    showNotice(`Could not add student: ${error.message}`, true);
  }
});

elements.templateButton.addEventListener("click", () => {
  const csv = `${REQUIRED_COLUMNS.join(",")}\r\n`;
  const file = new Blob([csv], { type: "text/csv;charset=utf-8" });
  const url = URL.createObjectURL(file);
  const link = document.createElement("a");
  link.href = url;
  link.download = "student_data_template.csv";
  link.click();
  URL.revokeObjectURL(url);
});

elements.classFilter.addEventListener("change", renderStudents);
elements.search.addEventListener("input", renderStudents);
elements.exportButton.addEventListener("click", () => {
  if (!analysis) return;
  const file = new Blob([buildReport()], { type: "text/plain;charset=utf-8" });
  const link = document.createElement("a");
  link.href = URL.createObjectURL(file);
  link.download = "analysis_report.txt";
  link.click();
  URL.revokeObjectURL(link.href);
});

elements.installButton.addEventListener("click", async () => {
  if (installPrompt) {
    await installPrompt.prompt();
    installPrompt = null;
    return;
  }
  const isAppleMobile = /iPhone|iPad|iPod/i.test(navigator.userAgent);
  showNotice(
    isAppleMobile
      ? "To install: tap Share in Safari, then choose Add to Home Screen."
      : "Use your browser menu and choose Install app or Add to Home screen.",
  );
});

window.addEventListener("beforeinstallprompt", (event) => {
  event.preventDefault();
  installPrompt = event;
});

window.addEventListener("appinstalled", () => {
  installPrompt = null;
  showNotice("Student Performance Analyser has been installed.");
});

if ("serviceWorker" in navigator && location.protocol !== "file:") {
  navigator.serviceWorker.register("./service-worker.js").catch((error) => {
    showNotice(`Offline support could not start: ${error.message}`, true);
  });
}

loadSavedData();
