const API_BASE = "/api";
const AI_TIMEOUT_MS = 65000;

function parseErrorBody(body, status) {
  if (status === 502) {
    return (
      body?.error ??
      "Serviço de IA indisponível. Aguarde alguns minutos ou use o modo demonstração."
    );
  }
  if (status === 504) {
    return body?.error ?? "Tempo esgotado ao aguardar a IA.";
  }
  if (body?.error) return body.error;
  if (body?.errors?.length) {
    return body.errors.map((e) => e.message).join(" ");
  }
  if (body?.detail) return `${body.error ?? "Erro"}: ${body.detail}`;
  return `Erro ${status}`;
}

async function request(path, options = {}) {
  const controller = new AbortController();
  const timeout = setTimeout(
    () => controller.abort(),
    options.timeout ?? 30000
  );

  try {
    const response = await fetch(`${API_BASE}${path}`, {
      headers: { "Content-Type": "application/json", ...options.headers },
      signal: controller.signal,
      ...options,
    });

    if (!response.ok) {
      const body = await response.json().catch(() => ({}));
      throw new Error(parseErrorBody(body, response.status));
    }

    if (response.status === 204) return null;
    return response.json();
  } catch (err) {
    if (err.name === "AbortError") {
      throw new Error("Tempo esgotado. Verifique sua conexão e tente novamente.");
    }
    throw err;
  } finally {
    clearTimeout(timeout);
  }
}

export const api = {
  health: () => request("/health"),
  listPlans: (params = {}) => {
    const query = new URLSearchParams();
    Object.entries(params).forEach(([key, value]) => {
      if (value === undefined || value === null || value === "") return;
      if (Array.isArray(value)) {
        value.forEach((item) => query.append(key, item));
      } else {
        query.set(key, value);
      }
    });
    const qs = query.toString();
    return request(qs ? `/plans?${qs}` : "/plans");
  },
  getPlan: (id) => request(`/plans/${id}`),
  createPlan: (data) =>
    request("/plans", { method: "POST", body: JSON.stringify(data) }),
  updatePlan: (id, data) =>
    request(`/plans/${id}`, { method: "PUT", body: JSON.stringify(data) }),
  deletePlan: (id) => request(`/plans/${id}`, { method: "DELETE" }),
  getRecommendations: (data) =>
    request("/plans/recommendations", {
      method: "POST",
      body: JSON.stringify(data),
      timeout: AI_TIMEOUT_MS,
    }),
  generatePlan: (data) =>
    request("/plans/generate", {
      method: "POST",
      body: JSON.stringify(data),
      timeout: AI_TIMEOUT_MS,
    }),
};
