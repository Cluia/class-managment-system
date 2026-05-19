import { api } from "./api.js";

const state = {
  page: 1,
  perPage: 10,
  pagination: { total_pages: 1, total: 0 },
  editingId: null,
};

const listView = document.getElementById("list-view");
const formView = document.getElementById("form-view");
const plansList = document.getElementById("plans-list");
const listLoading = document.getElementById("list-loading");
const paginationInfo = document.getElementById("pagination-info");
const btnPrev = document.getElementById("btn-prev");
const btnNext = document.getElementById("btn-next");
const planForm = document.getElementById("plan-form");
const formTitle = document.getElementById("form-title");
const btnSave = document.getElementById("btn-save");
const btnCancelEdit = document.getElementById("btn-cancel-edit");
const btnAi = document.getElementById("btn-ai-recommendations");
const aiLoadingMsg = document.getElementById("ai-loading-msg");
const aiSpinner = btnAi.querySelector(".btn-ai__spinner");
const alertBox = document.getElementById("alert");
const toast = document.getElementById("toast");

function showToast(message, isError = false) {
  toast.textContent = message;
  toast.classList.toggle("toast--error", isError);
  toast.classList.remove("toast--hidden");
  setTimeout(() => toast.classList.add("toast--hidden"), 4000);
}

function showAlert(message) {
  alertBox.textContent = message;
  alertBox.classList.remove("alert--hidden");
}

function hideAlert() {
  alertBox.classList.add("alert--hidden");
}

function parseList(value) {
  if (!value) return [];
  return value.split(",").map((s) => s.trim()).filter(Boolean);
}

function joinList(arr) {
  return (arr ?? []).join(", ");
}

function mergeListField(current, additions) {
  const merged = [...parseList(current), ...(additions ?? [])];
  return [...new Set(merged)].join(", ");
}

function switchView(view) {
  document.querySelectorAll(".nav__btn").forEach((btn) => {
    btn.classList.toggle("nav__btn--active", btn.dataset.view === view);
  });
  listView.classList.toggle("view--hidden", view !== "list");
  formView.classList.toggle("view--hidden", view !== "form");
}

function getListParams() {
  const params = {
    page: state.page,
    per_page: state.perPage,
    sort_by: document.getElementById("filter-sort-by").value,
    sort_order: document.getElementById("filter-sort-order").value,
  };

  const subject = document.getElementById("filter-subject").value.trim();
  const tags = document.getElementById("filter-tags").value.trim();
  const scheduled = document.getElementById("filter-date").value;
  const search = document.getElementById("filter-search").value.trim();

  if (subject) params.subject = subject;
  if (tags) params.tags = tags;
  if (scheduled) params.scheduled_date = scheduled;
  if (search) params.search = search;

  return params;
}

function updatePaginationControls() {
  const { page, total_pages, total } = state.pagination;
  paginationInfo.textContent = `Página ${page} de ${total_pages || 1} (${total} plano(s))`;
  btnPrev.disabled = page <= 1;
  btnNext.disabled = page >= (total_pages || 1);
}

async function loadPlans() {
  listLoading.classList.remove("loading--hidden");
  plansList.innerHTML = "";
  hideAlert();

  try {
    const result = await api.listPlans(getListParams());
    const plans = result.data ?? [];
    state.pagination = result.pagination ?? state.pagination;

    if (!plans.length) {
      plansList.innerHTML = `
        <li class="plans-list__empty">
          <span class="plans-list__empty-icon" aria-hidden="true">📋</span>
          Nenhum plano encontrado. Ajuste os filtros ou cadastre um novo plano.
        </li>`;
    } else {
      plansList.innerHTML = plans
        .map(
          (p) => `
        <li class="plans-list__item" data-id="${p.id}" tabindex="0" role="button">
          <span class="plans-list__title">${escapeHtml(p.title)}</span>
          <div class="plans-list__meta">
            <span class="plans-list__meta-item">
              <span class="plans-list__meta-icon" aria-hidden="true">📖</span>
              ${escapeHtml(p.subject)}
            </span>
            <span class="plans-list__meta-item">
              <span class="plans-list__meta-icon" aria-hidden="true">📅</span>
              ${escapeHtml(p.scheduled_date ?? "—")}
            </span>
          </div>
          <div class="plans-list__tags">${(p.tags ?? []).map((t) => `<span class="tag">${escapeHtml(t)}</span>`).join("")}</div>
        </li>`
        )
        .join("");

      plansList.querySelectorAll(".plans-list__item").forEach((li) => {
        const open = () => openEditPlan(li.dataset.id);
        li.addEventListener("click", open);
        li.addEventListener("keydown", (e) => {
          if (e.key === "Enter" || e.key === " ") {
            e.preventDefault();
            open();
          }
        });
      });
    }

    updatePaginationControls();
  } catch (err) {
    showAlert(err.message ?? "Erro ao carregar planos.");
    plansList.innerHTML = "";
  } finally {
    listLoading.classList.add("loading--hidden");
  }
}

function escapeHtml(text) {
  const el = document.createElement("span");
  el.textContent = text ?? "";
  return el.innerHTML;
}

function resetForm() {
  planForm.reset();
  state.editingId = null;
  formTitle.textContent = "Novo plano de aula";
  btnSave.textContent = "Salvar plano";
  btnCancelEdit.classList.add("loading--hidden");
  const dateInput = planForm.querySelector('[name="scheduled_date"]');
  if (dateInput) dateInput.value = new Date().toISOString().slice(0, 10);
}

async function openEditPlan(id) {
  try {
    const plan = await api.getPlan(id);
    state.editingId = id;
    formTitle.textContent = "Editar plano de aula";
    btnSave.textContent = "Atualizar plano";
    btnCancelEdit.classList.remove("loading--hidden");

    planForm.title.value = plan.title;
    planForm.subject.value = plan.subject;
    planForm.syllabus_summary.value = plan.syllabus_summary;
    planForm.objective.value = plan.objective;
    planForm.scheduled_date.value = plan.scheduled_date;
    planForm.contents.value = joinList(plan.contents);
    planForm.support_resources.value = joinList(plan.support_resources);
    planForm.tags.value = joinList(plan.tags);

    switchView("form");
  } catch (err) {
    showToast(err.message ?? "Erro ao carregar plano.", true);
  }
}

function formToPayload() {
  return {
    title: planForm.title.value.trim(),
    subject: planForm.subject.value.trim(),
    syllabus_summary: planForm.syllabus_summary.value.trim(),
    objective: planForm.objective.value.trim(),
    scheduled_date: planForm.scheduled_date.value,
    contents: parseList(planForm.contents.value),
    support_resources: parseList(planForm.support_resources.value),
    tags: parseList(planForm.tags.value),
  };
}

function setAiLoading(loading) {
  btnAi.disabled = loading;
  aiSpinner.classList.toggle("loading--hidden", !loading);
  btnAi.querySelector(".btn-ai__label").classList.toggle("loading--hidden", loading);
  aiLoadingMsg.classList.toggle("loading--hidden", !loading);
}

async function handleAiRecommendations() {
  const title = planForm.title.value.trim();
  const subject = planForm.subject.value.trim();
  const syllabus_summary = planForm.syllabus_summary.value.trim();

  if (!title || !subject || !syllabus_summary) {
    showToast("Preencha Título, Disciplina e Ementa antes de gerar recomendações.", true);
    return;
  }

  hideAlert();
  setAiLoading(true);

  try {
    const data = await api.getRecommendations({ title, subject, syllabus_summary });

    planForm.contents.value = mergeListField(
      planForm.contents.value,
      data.conteudos_complementares ?? []
    );
    planForm.support_resources.value = mergeListField(
      planForm.support_resources.value,
      data.topicos_relacionados ?? []
    );
    planForm.tags.value = mergeListField(planForm.tags.value, data.tags ?? []);

    if (data.fallback_mock) {
      showToast(
        "IA temporariamente indisponível — sugestões de demonstração aplicadas."
      );
    } else {
      showToast("Recomendações da IA aplicadas ao formulário!");
    }
  } catch (err) {
    const msg = err.message ?? "";
    const isAiDown = msg.includes("IA") || msg.includes("502") || msg.includes("504");
    showAlert(
      isAiDown
        ? "Serviço de IA indisponível no momento. O restante do app continua funcionando — você pode preencher o formulário manualmente ou tentar de novo mais tarde."
        : msg || "Não foi possível obter recomendações. Tente novamente."
    );
  } finally {
    setAiLoading(false);
  }
}

planForm.addEventListener("submit", async (e) => {
  e.preventDefault();
  hideAlert();

  const payload = formToPayload();
  btnSave.disabled = true;

  try {
    if (state.editingId) {
      await api.updatePlan(state.editingId, payload);
      showToast("Plano atualizado com sucesso!");
    } else {
      await api.createPlan(payload);
      showToast("Plano cadastrado com sucesso!");
    }
    resetForm();
    switchView("list");
    await loadPlans();
  } catch (err) {
    showAlert(err.message ?? "Erro ao salvar plano.");
  } finally {
    btnSave.disabled = false;
  }
});

document.querySelectorAll(".nav__btn").forEach((btn) => {
  btn.addEventListener("click", () => switchView(btn.dataset.view));
});

document.getElementById("btn-apply-filters").addEventListener("click", () => {
  state.page = 1;
  loadPlans();
});

document.getElementById("filter-search").addEventListener("keydown", (e) => {
  if (e.key === "Enter") {
    e.preventDefault();
    state.page = 1;
    loadPlans();
  }
});

btnPrev.addEventListener("click", () => {
  if (state.page > 1) {
    state.page -= 1;
    loadPlans();
  }
});

btnNext.addEventListener("click", () => {
  if (state.page < state.pagination.total_pages) {
    state.page += 1;
    loadPlans();
  }
});

btnAi.addEventListener("click", handleAiRecommendations);
document.getElementById("btn-new-plan").addEventListener("click", resetForm);
btnCancelEdit.addEventListener("click", () => {
  resetForm();
  switchView("list");
});

resetForm();
loadPlans();
