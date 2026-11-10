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
      chip.textContent = `${g} клас`;
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
    document.getElementById("badge-grade").textContent = `${grade} клас`;

    // Оновлюємо клас на бекенді
    try {
      await apiRequest("/profile/grade", {
        method: "PATCH",
        body: JSON.stringify({ grade }),
      });
    } catch (e) {
      console.warn("Could not sync grade to backend:", e);
    }

    // Завантажуємо теми для цього класу
    loadTopics(grade);
  }

  // ==========================================
  // Завантаження тем
  // ==========================================
  const topicsView = document.getElementById("topics-view");
  const taskView = document.getElementById("task-view");
  const topicsList = document.getElementById("topics-list");

  async function loadTopics(grade) {
    topicsList.innerHTML = '<div class="loading-state">завантаження тем...</div>';
    try {
      const topics = await apiRequest(`/topics/grade/${grade}`);
      if (!topics || topics.length === 0) {
        topicsList.innerHTML = '<div class="loading-state">навчальні матеріали для цього класу незабаром з\'являться</div>';
        return;
      }

      topicsList.innerHTML = "";
      topics.forEach((topic) => {
        const card = document.createElement("div");
        card.className = "topic-card";
        card.innerHTML = `
          <div class="topic-title">${escapeHtml(topic.title)}</div>
          <div class="topic-desc">${escapeHtml(topic.description || "натисни, щоб перейти до завдань")}</div>
        `;
        card.addEventListener("click", () => {
          triggerHaptic("medium");
          openTopic(topic);
        });
        topicsList.appendChild(card);
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
  const taskDifficulty = document.getElementById("task-difficulty");
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
    taskQuestion.innerHTML = "<i>генерація нової задачі за допомогою AI...</i>";
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
    formatAndDisplayMath(taskQuestion, task.question_text);
  }

  function resetTaskUI() {
    userAnswerInput.value = "";
    taskHintBox.classList.add("hidden");
    taskResultBox.classList.add("hidden");
    taskResultBox.className = "result-box hidden";
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
    } catch (e) {
      alert("помилка перевірки відповіді");
    } finally {
      btnSubmitAnswer.disabled = false;
      btnSubmitAnswer.textContent = "перевірити розв'язок";
    }
  });

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
