// mathcore Telegram Mini App Client Logic
document.addEventListener("DOMContentLoaded", () => {
  const tg = window.Telegram?.WebApp;
  if (tg) {
    tg.ready();
    tg.expand();
  }

  // Стан застосунку
  const state = {
    currentGrade: 7,
    currentSubject: "алгебра",
    currentTopic: null,
    currentTask: null,
    profile: null,
  };

  // Допоміжні функції Haptic Feedback для Telegram
  function triggerHaptic(type = "light") {
    if (!tg?.HapticFeedback) return;
    if (type === "success" || type === "error" || type === "warning") {
      tg.HapticFeedback.notificationOccurred(type);
    } else {
      tg.HapticFeedback.impactOccurred(type);
    }
  }

  // Обгортка для API-запитів з автоматичною передачею Telegram initData
  async function apiRequest(endpoint, options = {}) {
    const initData = tg?.initData || "";
    const headers = {
      "Content-Type": "application/json",
      Authorization: `tma ${initData}`,
      ...(options.headers || {}),
    };

    try {
      const response = await fetch(`/api/v1${endpoint}`, {
        ...options,
        headers,
      });

      if (!response.ok) {
        throw new Error(`HTTP error ${response.status}`);
      }
      return await response.json();
    } catch (err) {
      console.error(`API Error on ${endpoint}:`, err);
      throw err;
    }
  }

  // Перетворення та рендеринг тексту з формулами та HTML
  function formatMathText(rawText) {
    if (!rawText) return "";
    let res = String(rawText);

    // Заміна переносів рядків на <br>
    res = res.replace(/\r\n/g, "\n").replace(/\n/g, "<br>");

    // Якщо текст вже містить розмітку LaTeX ($...$ або \(...\)), повертаємо
    if (res.includes("$") || res.includes("\\(")) {
      return res;
    }

    // Перетворення квадратних коренів: √(16) -> \(\sqrt{16}\), √25 -> \(\sqrt{25}\)
    res = res.replace(/√\((\w+)\)/g, "\\(\\sqrt{$1}\\)");
    res = res.replace(/√([0-9a-zA-Z]+)/g, "\\(\\sqrt{$1}\\)");

    // Перетворення дробів: 2/7 або x / 6 -> \(\frac{2}{7}\)
    res = res.replace(/\b([a-zA-Z0-9]+)\s*\/\s*([0-9]+)\b/g, "\\(\\frac{$1}{$2}\\)");

    // Перетворення степенів: c² -> \(c^2\), x² -> \(x^2\), D = b² -> \(b^2\)
    res = res.replace(/([a-zA-Z0-9]+)²/g, "\\($1^2\\)");
    res = res.replace(/([a-zA-Z0-9]+)³/g, "\\($1^3\\)");

    return res;
  }

  // Рендер математичних формул через KaTeX
  function renderLatex(element) {
    if (!element) return;
    if (window.renderMathInElement) {
      try {
        window.renderMathInElement(element, {
          delimiters: [
            { left: "$$", right: "$$", display: true },
            { left: "$", right: "$", display: false },
            { left: "\\(", right: "\\)", display: false },
            { left: "\\[", right: "\\]", display: true },
          ],
          throwOnError: false,
        });
      } catch (err) {
        console.warn("KaTeX render error:", err);
      }
    } else {
      setTimeout(() => renderLatex(element), 100);
    }
  }

  function formatAndDisplayMath(element, rawText) {
    if (!element) return;
    element.innerHTML = formatMathText(rawText);
    renderLatex(element);
  }

  // ==========================================
  // Навігація вкладками
  // ==========================================
  const navItems = document.querySelectorAll(".nav-item");
  const tabContents = document.querySelectorAll(".tab-content");

  navItems.forEach((btn) => {
    btn.addEventListener("click", () => {
      triggerHaptic("selection");
      const targetTabId = btn.getAttribute("data-tab");

      navItems.forEach((b) => b.classList.remove("active"));
      tabContents.forEach((t) => t.classList.add("hidden"));

      btn.classList.add("active");
      const targetContent = document.getElementById(targetTabId);
      if (targetContent) {
        targetContent.classList.remove("hidden");
      }

      if (targetTabId === "tab-profile") {
        loadProfile();
      }
    });
  });

  // ==========================================
  // Вибір класу (grade chips)
  // ==========================================
  const gradeChipsList = document.getElementById("grade-chips-list");

  // Налаштування плавного горизонтального скролу для класу
  if (gradeChipsList) {
    // Скрол звичайним коліщатком миші
    gradeChipsList.addEventListener(
      "wheel",
      (evt) => {
        if (evt.deltaY !== 0) {
          evt.preventDefault();
          gradeChipsList.scrollLeft += evt.deltaY;
        }
      },
      { passive: false }
    );

    // Перетягування мишкою (drag-to-scroll)
    let isDown = false;
    let startX = 0;
    let scrollStart = 0;

    gradeChipsList.addEventListener("mousedown", (e) => {
      isDown = true;
      gradeChipsList.classList.add("dragging");
      startX = e.pageX - gradeChipsList.offsetLeft;
      scrollStart = gradeChipsList.scrollLeft;
    });

    window.addEventListener("mouseup", () => {
      if (isDown) {
        isDown = false;
        gradeChipsList.classList.remove("dragging");
      }
    });

    gradeChipsList.addEventListener("mousemove", (e) => {
      if (!isDown) return;
      e.preventDefault();
      const x = e.pageX - gradeChipsList.offsetLeft;
      const walk = (x - startX) * 1.5;
      gradeChipsList.scrollLeft = scrollStart - walk;
    });
  }

  function renderGradeChips() {
    gradeChipsList.innerHTML = "";
    for (let g = 1; g <= 11; g++) {
      const chip = document.createElement("button");
      chip.className = `grade-chip ${g === state.currentGrade ? "active" : ""}`;
      chip.textContent = g === 11 ? "11 клас (нмт)" : `${g} клас`;
      chip.addEventListener("click", () => {
        triggerHaptic("light");
        setGrade(g);
      });
      gradeChipsList.appendChild(chip);
    }

    // Автоматично прокручуємо до активного класу, щоб він був у полі зору
    setTimeout(() => {
      const activeChip = gradeChipsList.querySelector(".grade-chip.active");
      if (activeChip) {
        activeChip.scrollIntoView({ behavior: "smooth", inline: "center", block: "nearest" });
      }
    }, 50);
  }

  async function setGrade(grade) {
    // Не дозволяємо змінювати клас, якщо користувач перебуває у режимі перегляду завдання
    if (!taskView.classList.contains("hidden")) {
      return;
    }

    state.currentGrade = grade;
    renderGradeChips();
    document.getElementById("badge-grade").textContent = grade === 11 ? "11 клас (нмт)" : `${grade} клас`;

    // Оновлюємо клас на бекенді
    try {
      await apiRequest("/profile/grade", {
        method: "PATCH",
        body: JSON.stringify({ grade }),
      });
    } catch (e) {
      console.warn("Could not sync grade to backend:", e);
    }

    // Завантажуємо теми для цього класу з урахуванням предмету
    loadTopics(grade, grade >= 7 ? state.currentSubject : null);
  }

  // ==========================================
  // Завантаження тем та розділів
  // ==========================================
  const topicsView = document.getElementById("topics-view");
  const taskView = document.getElementById("task-view");
  const topicsList = document.getElementById("topics-list");
  const subjectSelectorContainer = document.getElementById("subject-selector-container");
  const subjectBtnAlgebra = document.getElementById("subject-btn-algebra");
  const subjectBtnGeometry = document.getElementById("subject-btn-geometry");
  const topicsSectionLabel = document.getElementById("topics-section-label");

  if (subjectBtnAlgebra && subjectBtnGeometry) {
    subjectBtnAlgebra.addEventListener("click", () => {
      triggerHaptic("selection");
      setSubject("алгебра");
    });
    subjectBtnGeometry.addEventListener("click", () => {
      triggerHaptic("selection");
      setSubject("геометрія");
    });
  }

  function setSubject(subject) {
    state.currentSubject = subject;
    if (subject === "алгебра") {
      subjectBtnAlgebra.classList.add("active");
      subjectBtnGeometry.classList.remove("active");
    } else {
      subjectBtnGeometry.classList.add("active");
      subjectBtnAlgebra.classList.remove("active");
    }
    loadTopics(state.currentGrade, state.currentSubject);
  }

  function getTopicsWord(count) {
    if (count % 10 === 1 && count % 100 !== 11) return "тема";
    if ([2, 3, 4].includes(count % 10) && ![12, 13, 14].includes(count % 100)) return "теми";
    return "тем";
  }

  async function loadTopics(grade, subject = null) {
    topicsList.innerHTML = '<div class="loading-state">завантаження тем...</div>';

    // Для 7-11 класів відображаємо вибір предмету: алгебра чи геометрія
    if (grade >= 7) {
      subjectSelectorContainer.classList.remove("hidden");
      const activeSubject = subject || state.currentSubject || "алгебра";
      if (activeSubject === "алгебра") {
        subjectBtnAlgebra.classList.add("active");
        subjectBtnGeometry.classList.remove("active");
      } else {
        subjectBtnGeometry.classList.add("active");
        subjectBtnAlgebra.classList.remove("active");
      }
      if (topicsSectionLabel) {
        topicsSectionLabel.textContent = `розділи (${activeSubject}):`;
      }
    } else {
      subjectSelectorContainer.classList.add("hidden");
      if (topicsSectionLabel) {
        topicsSectionLabel.textContent = "навчальні розділи:";
      }
    }

    try {
      let endpoint = `/topics/grade/${grade}`;
      if (grade >= 7 && subject) {
        endpoint += `?subject=${encodeURIComponent(subject)}`;
      }

      const topics = await apiRequest(endpoint);
      if (!topics || topics.length === 0) {
        topicsList.innerHTML = '<div class="loading-state">навчальні матеріали для цього розділу незабаром з\'являться</div>';
        return;
      }

      // Групуємо теми за розділами (папками)
      const sectionsMap = new Map();
      topics.forEach((topic) => {
        const sec = topic.section || "загальний розділ";
        if (!sectionsMap.has(sec)) {
          sectionsMap.set(sec, []);
        }
        sectionsMap.get(sec).push(topic);
      });

      topicsList.innerHTML = "";

      sectionsMap.forEach((secTopics, secTitle) => {
        const folder = document.createElement("div");
        folder.className = "folder-section";

        const header = document.createElement("div");
        header.className = "folder-header";
        header.innerHTML = `
          <div class="folder-title-wrap">
            <span class="material-symbols-outlined folder-icon">folder_open</span>
            <span class="folder-title">${escapeHtml(secTitle)}</span>
          </div>
          <span class="folder-count">${secTopics.length} ${getTopicsWord(secTopics.length)}</span>
        `;

        const topicsContainer = document.createElement("div");
        topicsContainer.className = "folder-topics-list";

        secTopics.forEach((topic) => {
          const card = document.createElement("div");
          card.className = "topic-card";
          card.innerHTML = `
            <div class="topic-card-header">
              <div class="topic-title">${escapeHtml(topic.title)}</div>
              <span class="material-symbols-outlined topic-arrow">arrow_forward</span>
            </div>
            <div class="topic-desc">${escapeHtml(topic.description || "натисніть, щоб розв'язувати завдання")}</div>
          `;
          card.addEventListener("click", () => {
            triggerHaptic("medium");
            openTopic(topic);
          });
          topicsContainer.appendChild(card);
        });

        folder.appendChild(header);
        folder.appendChild(topicsContainer);
        topicsList.appendChild(folder);
      });
    } catch (e) {
      topicsList.innerHTML = '<div class="loading-state">не вдалося завантажити теми</div>';
    }
  }

  // ==========================================
  // Завдання та тренажер
  // ==========================================
  const btnBackToTopics = document.getElementById("btn-back-to-topics");
  const currentTopicTitle = document.getElementById("current-topic-title");
  const taskTitle = document.getElementById("task-title");
  const taskNmtBadge = document.getElementById("task-nmt-badge");
  const taskDifficulty = document.getElementById("task-difficulty");
  const taskDiagram = document.getElementById("task-diagram");
  const taskQuestion = document.getElementById("task-question");
  const taskHintBox = document.getElementById("task-hint-box");
  const taskHintText = document.getElementById("task-hint-text");
  const userAnswerInput = document.getElementById("user-answer-input");
  const btnSubmitAnswer = document.getElementById("btn-submit-answer");
  const btnGetHint = document.getElementById("btn-get-hint");
  const btnGenerateAnother = document.getElementById("btn-generate-another");
  const taskResultBox = document.getElementById("task-result-box");
  const resultStatus = document.getElementById("result-status");
  const resultExplanation = document.getElementById("result-explanation");
  const btnToggleSolution = document.getElementById("btn-toggle-solution");
  const taskSolutionBox = document.getElementById("task-solution-box");
  const taskSolutionText = document.getElementById("task-solution-text");

  btnBackToTopics.addEventListener("click", () => {
    triggerHaptic("light");
    taskView.classList.add("hidden");
    topicsView.classList.remove("hidden");
  });

  async function openTopic(topic) {
    state.currentTopic = topic;
    currentTopicTitle.textContent = topic.title;
    topicsView.classList.add("hidden");
    taskView.classList.remove("hidden");

    // Завантажуємо першу задачу або генеруємо
    await loadOrGenerateTask(topic.id);
  }

  async function loadOrGenerateTask(topicId) {
    resetTaskUI();
    taskQuestion.innerHTML = "<i>завантажую завдання...</i>";

    try {
      const tasks = await apiRequest(`/topics/${topicId}/tasks`);
      if (tasks && tasks.length > 0) {
        displayTask(tasks[0]);
      } else {
        // Якщо завдань немає, генеруємо штучним інтелектом
        await generateNewTask(topicId);
      }
    } catch (e) {
      taskQuestion.textContent = "помилка завантаження завдання";
    }
  }

  async function generateNewTask(topicId) {
    resetTaskUI();
    taskQuestion.innerHTML = "<i>генерація завдання у форматі нмт за допомогою AI...</i>";
    try {
      const res = await apiRequest(`/topics/${topicId}/generate`, {
        method: "POST",
      });
      displayTask(res.task);
    } catch (e) {
      taskQuestion.textContent = "не вдалося згенерувати задачу";
    }
  }

  function displayTask(task) {
    state.currentTask = task;
    taskTitle.textContent = task.title || "завдання";
    taskDifficulty.textContent = `${task.difficulty || 1}/3`;

    // Відображення бейджа формату НМТ
    if (task.is_nmt || (task.title && task.title.toLowerCase().includes("нмт"))) {
      taskNmtBadge.classList.remove("hidden");
    } else {
      taskNmtBadge.classList.add("hidden");
    }

    // Відображення векторного малюнка / креслення
    if (task.diagram_svg && task.diagram_svg.trim().startsWith("<svg")) {
      taskDiagram.innerHTML = task.diagram_svg;
      taskDiagram.classList.remove("hidden");
    } else {
      taskDiagram.innerHTML = "";
      taskDiagram.classList.add("hidden");
    }

    formatAndDisplayMath(taskQuestion, task.question_text);
  }

  function resetTaskUI() {
    userAnswerInput.value = "";
    taskHintBox.classList.add("hidden");
    taskResultBox.classList.add("hidden");
    taskResultBox.className = "result-box hidden";
    taskDiagram.classList.add("hidden");
    taskDiagram.innerHTML = "";
    if (taskNmtBadge) taskNmtBadge.classList.add("hidden");
    if (btnToggleSolution) btnToggleSolution.classList.add("hidden");
    if (taskSolutionBox) taskSolutionBox.classList.add("hidden");
    if (taskSolutionText) taskSolutionText.textContent = "";
  }

  // Кнопка перевірки відповіді
  btnSubmitAnswer.addEventListener("click", async () => {
    const answer = userAnswerInput.value.trim();
    if (!answer) {
      userAnswerInput.focus();
      return;
    }

    if (!state.currentTask) return;

    btnSubmitAnswer.disabled = true;
    btnSubmitAnswer.textContent = "перевірка...";

    try {
      const result = await apiRequest(`/tasks/${state.currentTask.id}/check`, {
        method: "POST",
        body: JSON.stringify({ answer }),
      });

      taskResultBox.classList.remove("hidden");
      if (result.is_correct) {
        triggerHaptic("success");
        taskResultBox.className = "result-box correct";
        resultStatus.textContent = "відповідь правильна!";
      } else {
        triggerHaptic("error");
        taskResultBox.className = "result-box incorrect";
        resultStatus.textContent = "спробуй ще раз";
      }

      resultExplanation.textContent = "";
      formatAndDisplayMath(resultExplanation, result.explanation);

      // Відображаємо кнопку покрокового розв'язку
      const solution = result.detailed_solution || state.currentTask.detailed_solution;
      if (solution) {
        formatAndDisplayMath(taskSolutionText, solution);
        btnToggleSolution.classList.remove("hidden");
        btnToggleSolution.innerHTML = `
          <span class="material-symbols-outlined" style="font-size: 15px; vertical-align: middle;">menu_book</span>
          показати покроковий розв'язок ↓
        `;
        taskSolutionBox.classList.add("hidden");
      } else {
        btnToggleSolution.classList.add("hidden");
      }
    } catch (e) {
      alert("помилка перевірки відповіді");
    } finally {
      btnSubmitAnswer.disabled = false;
      btnSubmitAnswer.textContent = "перевірити розв'язок";
    }
  });

  // Кнопка перемикання покрокового розв'язку
  if (btnToggleSolution) {
    btnToggleSolution.addEventListener("click", () => {
      triggerHaptic("light");
      const isHidden = taskSolutionBox.classList.contains("hidden");
      if (isHidden) {
        taskSolutionBox.classList.remove("hidden");
        btnToggleSolution.innerHTML = `
          <span class="material-symbols-outlined" style="font-size: 15px; vertical-align: middle;">menu_book</span>
          приховати розв'язок ↑
        `;
      } else {
        taskSolutionBox.classList.add("hidden");
        btnToggleSolution.innerHTML = `
          <span class="material-symbols-outlined" style="font-size: 15px; vertical-align: middle;">menu_book</span>
          показати покроковий розв'язок ↓
        `;
      }
    });
  }

  // Кнопка підказки
  btnGetHint.addEventListener("click", async () => {
    if (!state.currentTask) return;
    triggerHaptic("light");

    if (!taskHintBox.classList.contains("hidden")) {
      taskHintBox.classList.add("hidden");
      return;
    }

    try {
      const hintRes = await apiRequest(`/tasks/${state.currentTask.id}/hint`);
      taskHintText.textContent = "";
      formatAndDisplayMath(taskHintText, hintRes.hint);
      taskHintBox.classList.remove("hidden");
    } catch (e) {
      console.error(e);
    }
  });

  // Кнопка нової задачі
  btnGenerateAnother.addEventListener("click", async () => {
    if (!state.currentTopic) return;
    triggerHaptic("medium");
    await generateNewTask(state.currentTopic.id);
  });

  // ==========================================
  // Профіль та аналітика
  // ==========================================
  async function loadProfile() {
    try {
      const profile = await apiRequest("/profile");
      state.profile = profile;

      const name = profile.first_name || "учень";
      document.getElementById("profile-name").textContent = name;
      document.getElementById("badge-name").textContent = name;
      document.getElementById("profile-avatar").textContent = name.charAt(0).toLowerCase();

      const grade = profile.grade || 7;
      document.getElementById("profile-grade").textContent = `${grade} клас`;
      document.getElementById("badge-grade").textContent = `${grade} клас`;

      document.getElementById("profile-rank").textContent = profile.rank;
      document.getElementById("stat-solved").textContent = profile.solved_unique;
      document.getElementById("stat-accuracy").textContent = `${profile.accuracy}%`;
      document.getElementById("stat-attempts").textContent = profile.total_attempts;
      document.getElementById("stat-today").textContent = profile.today_solved;
      document.getElementById("stat-streak").textContent = profile.streak;
      document.getElementById("stat-days").textContent = `${profile.days_registered} дн.`;

      document.getElementById("progress-percent").textContent = `${profile.accuracy}%`;
      document.getElementById("progress-bar-fill").style.width = `${Math.min(profile.accuracy, 100)}%`;

      if (profile.grade && profile.grade !== state.currentGrade) {
        state.currentGrade = profile.grade;
        renderGradeChips();
      }
    } catch (e) {
      console.warn("Could not load profile:", e);
    }
  }

  function escapeHtml(str) {
    if (!str) return "";
    return str
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#039;");
  }

  // ==========================================
  // Старт застосунку
  // ==========================================
  renderGradeChips();
  loadProfile().then(() => {
    loadTopics(state.currentGrade);
  });
});
