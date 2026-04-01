function getCookie(name) {
  const cookieValue = document.cookie
    .split(";")
    .map((c) => c.trim())
    .find((c) => c.startsWith(name + "="));
  if (!cookieValue) return null;
  return decodeURIComponent(cookieValue.split("=")[1]);
}

function renderProgressChart(completedCount, pendingCount) {
  const canvas = document.getElementById("progressChart");
  if (!canvas) return null;

  const data = {
    labels: ["Completed", "Pending"],
    datasets: [
      {
        data: [completedCount, pendingCount],
        backgroundColor: ["#198754", "#ffc107"],
        borderWidth: 0,
      },
    ],
  };

  return new Chart(canvas, {
    type: "doughnut",
    data,
    options: {
      responsive: true,
      plugins: {
        legend: { position: "bottom" },
      },
    },
  });
}

function setCounts(completedCount, pendingCount) {
  const completedEl = document.getElementById("completedCount");
  const pendingEl = document.getElementById("pendingCount");
  if (completedEl) completedEl.textContent = String(completedCount);
  if (pendingEl) pendingEl.textContent = String(pendingCount);
}

document.addEventListener("DOMContentLoaded", () => {
  const initial = window.DASHBOARD || { completedCount: 0, pendingCount: 0 };
  let chart = renderProgressChart(initial.completedCount, initial.pendingCount);

  document.querySelectorAll(".task-toggle").forEach((checkbox) => {
    checkbox.addEventListener("change", async (e) => {
      const input = e.currentTarget;
      const taskId = input.dataset.taskId;
      const desired = Boolean(input.checked);

      const csrfToken = getCookie("csrftoken");

      try {
        const res = await fetch(`/tasks/${taskId}/toggle/`, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            "X-CSRFToken": csrfToken,
          },
          body: JSON.stringify({ is_completed: desired }),
        });

        const data = await res.json();
        if (!res.ok || !data.ok) throw new Error(data.error || "Request failed");

        setCounts(data.completed_count, data.pending_count);
        if (chart) {
          chart.data.datasets[0].data = [data.completed_count, data.pending_count];
          chart.update();
        }
      } catch (err) {
        input.checked = !desired;
        alert("Could not update task. Please refresh and try again.");
      }
    });
  });
});

