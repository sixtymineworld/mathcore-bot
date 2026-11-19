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
    loadedTopics: [],
  };

  // Допоміжні функції Haptic Feedback для Telegram
  function triggerHaptic(type = "light") {
    try {
      if (!tg?.HapticFeedback) return;
      if (type === "success" || type === "error" || type === "warning") {
        tg.HapticFeedback.notificationOccurred(type);
      } else if (type === "selection") {
        tg.HapticFeedback.selectionChanged();
      } else {
        tg.HapticFeedback.impactOccurred(type || "light");
      }
    } catch (e) {
      console.warn("Haptic feedback error:", e);
    }
  }

  // Обгортка для API-запитів з автоматичною передачею Telegram initData
  async function apiRequest(endpoint, options = {}) {
    const initData = tg?.initData || "";
    const headers = {
      "Content-Type": "application/json",
      "ngrok-skip-browser-warning": "true",
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
  // Навігація вкладками та перемикання екранів
  // ==========================================
  const navItems = document.querySelectorAll(".nav-item");
  const tabContents = document.querySelectorAll(".tab-content");
  const topicsView = document.getElementById("topics-view");
  const taskView = document.getElementById("task-view");

  function switchTab(targetTabId) {
    triggerHaptic("selection");

    // Оновлення кнопок нижньої панелі
    navItems.forEach((btn) => {
      if (btn.getAttribute("data-tab") === targetTabId) {
        btn.classList.add("active");
      } else {
        btn.classList.remove("active");
      }
    });

    // Оновлення відображення секцій вкладок
    tabContents.forEach((tab) => {
      if (tab.id === targetTabId) {
        tab.classList.remove("hidden");
        tab.classList.add("active");
      } else {
        tab.classList.add("hidden");
        tab.classList.remove("active");
      }
    });

    // Якщо повертаємось на теми
    if (targetTabId === "tab-topics") {
      if (taskView && topicsView) {
        taskView.classList.add("hidden");
        topicsView.classList.remove("hidden");
      }
    }

    // Якщо відкриваємо профіль
    if (targetTabId === "tab-profile") {
      loadProfile(false);
    }

    window.scrollTo({ top: 0, behavior: "smooth" });
  }

  // Кліки по нижній панелі навігації
  navItems.forEach((btn) => {
    btn.addEventListener("click", (e) => {
      e.preventDefault();
      const targetTabId = btn.getAttribute("data-tab");
      if (targetTabId) {
        switchTab(targetTabId);
      }
    });
  });

  // Клік по бейджу користувача в хедері -> відкриття профілю
  const headerUserBadge = document.getElementById("header-user-badge");
  if (headerUserBadge) {
    headerUserBadge.addEventListener("click", () => {
      switchTab("tab-profile");
    });
  }

  // Клік по імені в hero welcome card -> відкриття профілю
  const heroPill = document.querySelector(".hero-pill");
  if (heroPill) {
    heroPill.addEventListener("click", () => {
      switchTab("tab-profile");
    });
  }

  // Кнопка "назад до тем" з профілю
  const btnBackFromProfile = document.getElementById("btn-back-from-profile");
  if (btnBackFromProfile) {
    btnBackFromProfile.addEventListener("click", () => {
      switchTab("tab-topics");
    });
  }

  // ==========================================
  // Вибір класу (grade chips)
  // ==========================================
  const gradeChipsList = document.getElementById("grade-chips-list");

  if (gradeChipsList) {
    // Горизонтальний скрол коліщатком миші для десктопу
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
  }

  function renderGradeChips() {
    if (!gradeChipsList) return;
    gradeChipsList.innerHTML = "";
    for (let g = 1; g <= 11; g++) {
      const chip = document.createElement("button");
      chip.type = "button";
      chip.className = `grade-chip ${g === state.currentGrade ? "active" : ""}`;
      chip.textContent = g === 11 ? "11 клас (нмт)" : `${g} клас`;

      chip.addEventListener("click", () => {
        triggerHaptic("light");
        setGrade(g);
      });

      gradeChipsList.appendChild(chip);
    }

    setTimeout(() => {
      const activeChip = gradeChipsList.querySelector(".grade-chip.active");
      if (activeChip) {
        activeChip.scrollIntoView({ behavior: "smooth", inline: "center", block: "nearest" });
      }
    }, 50);
  }

  function setGrade(grade) {
    // Якщо відкрите завдання, повертаємось до списку тем
    if (taskView && !taskView.classList.contains("hidden")) {
      taskView.classList.add("hidden");
      if (topicsView) topicsView.classList.remove("hidden");
    }

    state.currentGrade = grade;
    renderGradeChips();

    const gradeText = grade === 11 ? "11 клас (нмт)" : `${grade} клас`;
    const badgeGrade = document.getElementById("badge-grade");
    if (badgeGrade) badgeGrade.textContent = gradeText;
    const profileGrade = document.getElementById("profile-grade");
    if (profileGrade) profileGrade.textContent = gradeText;

    // Фонова синхронізація класу на бекенді
    apiRequest("/profile/grade", {
      method: "PATCH",
      body: JSON.stringify({ grade }),
    }).catch((e) => console.warn("Could not sync grade to backend:", e));

    // Миттєве завантаження тем для нового класу
    const subject = grade >= 7 ? (state.currentSubject || "алгебра") : null;
    loadTopics(grade, subject);
  }

  // ==========================================
  // Вибір предмету (алгебра / геометрія для 7-11 класів)
  // ==========================================
  const topicsList = document.getElementById("topics-list");
  const subjectSelectorContainer = document.getElementById("subject-selector-container");
  const subjectBtnAlgebra = document.getElementById("subject-btn-algebra");
  const subjectBtnGeometry = document.getElementById("subject-btn-geometry");
  const topicsSectionLabel = document.getElementById("topics-section-label");

  if (subjectBtnAlgebra && subjectBtnGeometry) {
    subjectBtnAlgebra.addEventListener("click", (e) => {
      e.preventDefault();
      setSubject("алгебра");
    });
    subjectBtnGeometry.addEventListener("click", (e) => {
      e.preventDefault();
      setSubject("геометрія");
    });
  }

  function setSubject(subject) {
    triggerHaptic("selection");
    state.currentSubject = subject;

    if (subject === "алгебра") {
      subjectBtnAlgebra?.classList.add("active");
      subjectBtnGeometry?.classList.remove("active");
    } else {
      subjectBtnGeometry?.classList.add("active");
      subjectBtnAlgebra?.classList.remove("active");
    }

    if (topicsSectionLabel) {
      topicsSectionLabel.textContent = `розділи (${subject}):`;
    }

    loadTopics(state.currentGrade, subject);
  }

  function getTopicsWord(count) {
    if (count % 10 === 1 && count % 100 !== 11) return "тема";
    if ([2, 3, 4].includes(count % 10) && ![12, 13, 14].includes(count % 100)) return "теми";
    return "тем";
  }

  // ==========================================
  // Завантаження тем та розділів
  // ==========================================
  async function loadTopics(grade, subject = null) {
    if (!topicsList) return;
    topicsList.innerHTML = '<div class="loading-state">завантаження тем...</div>';

    // Для 7-11 класів завжди активуємо вибір предмету
    let activeSubject = null;
    if (grade >= 7) {
      subjectSelectorContainer?.classList.remove("hidden");
      activeSubject = subject || state.currentSubject || "алгебра";
      state.currentSubject = activeSubject;

      if (activeSubject === "алгебра") {
        subjectBtnAlgebra?.classList.add("active");
        subjectBtnGeometry?.classList.remove("active");
      } else {
        subjectBtnGeometry?.classList.add("active");
        subjectBtnAlgebra?.classList.remove("active");
      }

      if (topicsSectionLabel) {
        topicsSectionLabel.textContent = `розділи (${activeSubject}):`;
      }
    } else {
      subjectSelectorContainer?.classList.add("hidden");
      if (topicsSectionLabel) {
        topicsSectionLabel.textContent = "навчальні розділи:";
      }
    }

    try {
      let endpoint = `/topics/grade/${grade}`;
      if (grade >= 7 && activeSubject) {
        endpoint += `?subject=${encodeURIComponent(activeSubject)}`;
      }

      const topics = await apiRequest(endpoint);
      renderTopics(topics);
    } catch (e) {
      topicsList.innerHTML = '<div class="loading-state">не вдалося завантажити теми</div>';
    }
  }

  function renderTopics(topics) {
    state.loadedTopics = topics || [];
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

  if (btnBackToTopics) {
    btnBackToTopics.addEventListener("click", () => {
      triggerHaptic("light");
      taskView.classList.add("hidden");
      topicsView.classList.remove("hidden");
      window.scrollTo({ top: 0, behavior: "smooth" });
    });
  }

  async function openTopic(topic) {
    state.currentTopic = topic;
    if (currentTopicTitle) currentTopicTitle.textContent = topic.title;
    topicsView.classList.add("hidden");
    taskView.classList.remove("hidden");
    window.scrollTo({ top: 0, behavior: "smooth" });

    // Завантажуємо першу задачу або генеруємо
    await loadOrGenerateTask(topic.id);
  }

  async function loadOrGenerateTask(topicId) {
    resetTaskUI();
    // Кожного разу генеруємо нове завдання за обраною темою
    await generateNewTask(topicId);
  }

  async function generateNewTask(topicId) {
    resetTaskUI();
    if (taskQuestion) taskQuestion.innerHTML = "<i>генерація завдання за підручником о. істера...</i>";
    try {
      const res = await apiRequest(`/topics/${topicId}/generate`, {
        method: "POST",
      });
      displayTask(res.task);
    } catch (e) {
      if (taskQuestion) taskQuestion.textContent = "не вдалося згенерувати задачу";
    }
  }

  function displayTask(task) {
    state.currentTask = task;
    if (taskTitle) taskTitle.textContent = task.title || "завдання";
    if (taskDifficulty) taskDifficulty.textContent = `${task.difficulty || 1}/3`;

    // Відображення бейджа формату НМТ тільки для відповідних завдань
    if (taskNmtBadge) {
      if (task.is_nmt) {
        taskNmtBadge.classList.remove("hidden");
      } else {
        taskNmtBadge.classList.add("hidden");
      }
    }

    // Відображення векторного малюнка / креслення
    if (taskDiagram) {
      if (task.diagram_svg && task.diagram_svg.trim().startsWith("<svg")) {
        taskDiagram.innerHTML = task.diagram_svg;
        taskDiagram.classList.remove("hidden");
      } else {
        taskDiagram.innerHTML = "";
        taskDiagram.classList.add("hidden");
      }
    }

    if (taskQuestion) {
      formatAndDisplayMath(taskQuestion, task.question_text);
    }
  }

  function resetTaskUI() {
    if (userAnswerInput) userAnswerInput.value = "";
    if (taskHintBox) taskHintBox.classList.add("hidden");
    if (taskResultBox) {
      taskResultBox.classList.add("hidden");
      taskResultBox.className = "result-box hidden";
    }
    if (taskDiagram) {
      taskDiagram.classList.add("hidden");
      taskDiagram.innerHTML = "";
    }
    if (taskNmtBadge) taskNmtBadge.classList.add("hidden");
    if (btnToggleSolution) btnToggleSolution.classList.add("hidden");
    if (taskSolutionBox) taskSolutionBox.classList.add("hidden");
    if (taskSolutionText) taskSolutionText.textContent = "";
  }

  // Кнопка перевірки відповіді
  if (btnSubmitAnswer) {
    btnSubmitAnswer.addEventListener("click", async () => {
      const answer = userAnswerInput?.value?.trim();
      if (!answer) {
        userAnswerInput?.focus();
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
          resultStatus.innerHTML = `<span class="material-symbols-outlined status-icon">check_circle</span> відповідь правильна!`;
        } else {
          triggerHaptic("error");
          taskResultBox.className = "result-box incorrect";
          resultStatus.innerHTML = `<span class="material-symbols-outlined status-icon">refresh</span> спробуй ще раз`;
        }

        resultExplanation.textContent = "";
        formatAndDisplayMath(resultExplanation, result.explanation);

        // Відображаємо кнопку покрокового розв'язку
        const solution = result.detailed_solution || state.currentTask.detailed_solution;
        if (solution && btnToggleSolution && taskSolutionBox) {
          formatAndDisplayMath(taskSolutionText, solution);
          btnToggleSolution.classList.remove("hidden");
          btnToggleSolution.innerHTML = `<span class="material-symbols-outlined" style="font-size: 15px;">menu_book</span><span>покроковий розв'язок</span><span>↓</span>`;
          taskSolutionBox.classList.add("hidden");
        } else if (btnToggleSolution) {
          btnToggleSolution.classList.add("hidden");
        }
      } catch (e) {
        alert("помилка перевірки відповіді");
      } finally {
        btnSubmitAnswer.disabled = false;
        btnSubmitAnswer.textContent = "перевірити розв'язок";
      }
    });
  }

  // Кнопка перемикання покрокового розв'язку
  if (btnToggleSolution) {
    btnToggleSolution.addEventListener("click", () => {
      triggerHaptic("light");
      const isHidden = taskSolutionBox.classList.contains("hidden");
      if (isHidden) {
        taskSolutionBox.classList.remove("hidden");
        btnToggleSolution.innerHTML = `<span class="material-symbols-outlined" style="font-size: 15px;">menu_book</span><span>приховати розв'язок</span><span>↑</span>`;
      } else {
        taskSolutionBox.classList.add("hidden");
        btnToggleSolution.innerHTML = `<span class="material-symbols-outlined" style="font-size: 15px;">menu_book</span><span>покроковий розв'язок</span><span>↓</span>`;
      }
    });
  }

  // Кнопка підказки
  if (btnGetHint) {
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
  }

  // Кнопка нової задачі
  if (btnGenerateAnother) {
    btnGenerateAnother.addEventListener("click", async () => {
      if (!state.currentTopic) return;
      triggerHaptic("medium");
      await generateNewTask(state.currentTopic.id);
    });
  }

  // ==========================================
  // Профіль та аналітика
  // ==========================================
  async function loadProfile(initial = false) {
    try {
      const profile = await apiRequest("/profile");
      state.profile = profile;

      const name = profile.first_name || "учень";
      const nameLower = name.toLowerCase();

      const profileName = document.getElementById("profile-name");
      if (profileName) profileName.textContent = nameLower;

      const badgeName = document.getElementById("badge-name");
      if (badgeName) badgeName.textContent = nameLower;

      const heroUserName = document.getElementById("hero-user-name");
      if (heroUserName) heroUserName.textContent = nameLower;

      const profileAvatar = document.getElementById("profile-avatar");
      if (profileAvatar) profileAvatar.textContent = nameLower.charAt(0);

      // Використовуємо вибраний клас зі стану, або з профілю при першому завантаженні
      const displayGrade = initial ? (profile.grade || state.currentGrade || 7) : state.currentGrade;
      const gradeText = displayGrade === 11 ? "11 клас (нмт)" : `${displayGrade} клас`;

      const profileGrade = document.getElementById("profile-grade");
      if (profileGrade) profileGrade.textContent = gradeText;

      const badgeGrade = document.getElementById("badge-grade");
      if (badgeGrade) badgeGrade.textContent = gradeText;

      const profileRank = document.getElementById("profile-rank");
      if (profileRank) profileRank.textContent = profile.rank || "дослідник";

      const statSolved = document.getElementById("stat-solved");
      if (statSolved) statSolved.textContent = profile.solved_unique ?? 0;

      const statAccuracy = document.getElementById("stat-accuracy");
      if (statAccuracy) statAccuracy.textContent = `${profile.accuracy ?? 0}%`;

      const statAttempts = document.getElementById("stat-attempts");
      if (statAttempts) statAttempts.textContent = profile.total_attempts ?? 0;

      const statToday = document.getElementById("stat-today");
      if (statToday) statToday.textContent = profile.today_solved ?? 0;

      const statStreak = document.getElementById("stat-streak");
      if (statStreak) statStreak.textContent = profile.streak ?? 0;

      const statDays = document.getElementById("stat-days");
      if (statDays) statDays.textContent = `${profile.days_registered ?? 1} дн.`;

      const progressPercent = document.getElementById("progress-percent");
      if (progressPercent) progressPercent.textContent = `${profile.accuracy ?? 0}%`;

      const progressBarFill = document.getElementById("progress-bar-fill");
      if (progressBarFill) {
        progressBarFill.style.width = `${Math.min(profile.accuracy ?? 0, 100)}%`;
      }

      // Тільки при першому завантаженні застосунку виставляємо збережений клас
      if (initial && profile.grade && profile.grade !== state.currentGrade) {
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

  function updateHeroGreeting() {
    const hour = new Date().getHours();
    let greeting = "привіт";
    if (hour >= 5 && hour < 12) greeting = "доброго ранку";
    else if (hour >= 12 && hour < 18) greeting = "гарного дня";
    else if (hour >= 18 && hour < 23) greeting = "затишного вечора";

    const greetingEl = document.getElementById("hero-greeting-time");
    if (greetingEl) {
      greetingEl.textContent = greeting;
    }

    const tgUser = tg?.initDataUnsafe?.user;
    if (tgUser?.first_name) {
      const heroUserName = document.getElementById("hero-user-name");
      if (heroUserName) {
        heroUserName.textContent = tgUser.first_name.toLowerCase();
      }
    }
  }

  // Кнопка швидкого старту в Hero Section
  const btnHeroQuickStart = document.getElementById("btn-hero-quick-start");
  if (btnHeroQuickStart) {
    btnHeroQuickStart.addEventListener("click", async () => {
      triggerHaptic("medium");
      if (state.loadedTopics && state.loadedTopics.length > 0) {
        const randomTopic = state.loadedTopics[Math.floor(Math.random() * state.loadedTopics.length)];
        await openTopic(randomTopic);
      } else {
        document.getElementById("grade-chips-list")?.scrollIntoView({ behavior: "smooth" });
      }
    });
  }

  // ==========================================
  // Старт застосунку
  // ==========================================
  updateHeroGreeting();
  renderGradeChips();
  loadProfile(true).then(() => {
    loadTopics(state.currentGrade, state.currentGrade >= 7 ? state.currentSubject : null);
  });
});
