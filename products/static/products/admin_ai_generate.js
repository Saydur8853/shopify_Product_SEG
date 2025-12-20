(() => {
  const fieldMap = {
    id_description: "description",
    id_seo_title: "seo_title",
    id_seo_description: "seo_description",
  };

  const fieldIds = Object.keys(fieldMap);

  function getCookie(name) {
    const value = `; ${document.cookie}`;
    const parts = value.split(`; ${name}=`);
    if (parts.length === 2) {
      return parts.pop().split(";").shift();
    }
    return "";
  }

  function getCsrfToken() {
    const tokenInput = document.querySelector('input[name="csrfmiddlewaretoken"]');
    if (tokenInput && tokenInput.value) {
      return tokenInput.value;
    }
    return getCookie("csrftoken");
  }

  function getAiUrl() {
    const path = window.location.pathname;
    const match = path.match(/^(.*\/productuploadrow\/)(?:\d+\/)?(?:change|add)\/$/);
    if (match && match[1]) {
      return `${match[1]}ai-generate/`;
    }
    return "/admin/products/productuploadrow/ai-generate/";
  }

  function getMessageBox() {
    let box = document.getElementById("ai-generate-message");
    if (box) {
      return box;
    }

    const container = document.createElement("div");
    container.id = "ai-generate-message";
    container.style.margin = "10px 0";
    container.style.padding = "10px 12px";
    container.style.border = "1px solid #c6c6c6";
    container.style.borderRadius = "4px";
    container.style.display = "none";
    container.style.whiteSpace = "pre-wrap";

    const form = document.querySelector("form");
    if (form && form.parentNode) {
      form.parentNode.insertBefore(container, form);
    } else {
      document.body.insertBefore(container, document.body.firstChild);
    }

    return container;
  }

  function showMessage(type, text) {
    const box = getMessageBox();
    const color = type === "error" ? "#b20000" : "#0b6e2d";
    const bg = type === "error" ? "#fff3f3" : "#f0fff4";
    box.style.borderColor = color;
    box.style.background = bg;
    box.style.color = color;
    box.textContent = text;
    box.style.display = "block";
  }

  function clearMessage() {
    const box = document.getElementById("ai-generate-message");
    if (!box) {
      return;
    }
    box.textContent = "";
    box.style.display = "none";
  }

  function insertButton(fieldId) {
    const field = document.getElementById(fieldId);
    if (!field) {
      return;
    }
    if (field.parentElement && field.parentElement.classList.contains("ai-generate-wrapper")) {
      return;
    }

    const button = document.createElement("button");
    button.type = "button";
    button.className = "button";
    button.textContent = "AI GENERATE";
    button.dataset.aiTarget = fieldId;

    const wrapper = document.createElement("div");
    wrapper.className = "ai-generate-wrapper";
    wrapper.style.display = "flex";
    wrapper.style.alignItems = "center";
    wrapper.style.gap = "8px";

    field.style.flex = "1 1 auto";
    field.parentNode.insertBefore(wrapper, field);
    wrapper.appendChild(field);
    wrapper.appendChild(button);

    button.addEventListener("click", async () => {
      const titleInput = document.getElementById("id_title");
      const title = titleInput ? titleInput.value.trim() : "";
      if (!title) {
        showMessage("error", "Please enter a title first.");
        return;
      }

      const aiUrl = getAiUrl();
      const csrfToken = getCsrfToken();
      const targetField = document.getElementById(fieldId);
      const targetKey = fieldMap[fieldId];

      if (!targetField || !targetKey) {
        showMessage("error", "Target field not found.");
        return;
      }

      button.disabled = true;
      const originalText = button.textContent;
      button.textContent = "GENERATING...";
      clearMessage();

      try {
        const response = await fetch(aiUrl, {
          method: "POST",
          headers: {
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
            "X-CSRFToken": csrfToken,
            "X-Requested-With": "XMLHttpRequest",
          },
          body: new URLSearchParams({ title }),
        });

        const payload = await response.json();
        if (!response.ok) {
          throw new Error(payload.error || "AI generation failed.");
        }

        const value = payload.data && payload.data[targetKey];
        if (!value) {
          throw new Error("AI did not return a value for this field.");
        }

        targetField.value = value;
        showMessage("success", "AI generation completed.");
      } catch (err) {
        const message = err && err.message ? err.message : "AI generation failed.";
        showMessage("error", message);
      } finally {
        button.disabled = false;
        button.textContent = originalText;
      }
    });
  }

  document.addEventListener("DOMContentLoaded", () => {
    fieldIds.forEach(insertButton);
  });
})();
