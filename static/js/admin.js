/* ══════════════════════════════════════════════════════════
   LAYOSAM  ·  Admin JS  ·  admin.js
══════════════════════════════════════════════════════════ */

/* ── File drop zone with preview ── */
(function () {
  const dropZone = document.getElementById("file-drop-zone");
  const fileInput = document.getElementById("image-input");
  const preview  = document.getElementById("file-preview");
  const previewImg = document.getElementById("preview-img");
  if (!dropZone || !fileInput) return;

  dropZone.addEventListener("click", function () { fileInput.click(); });

  fileInput.addEventListener("change", function () {
    showPreview(fileInput.files[0]);
  });

  dropZone.addEventListener("dragover", function (e) {
    e.preventDefault();
    dropZone.classList.add("dragover");
  });
  dropZone.addEventListener("dragleave", function () {
    dropZone.classList.remove("dragover");
  });
  dropZone.addEventListener("drop", function (e) {
    e.preventDefault();
    dropZone.classList.remove("dragover");
    const file = e.dataTransfer.files[0];
    if (file) {
      const dt = new DataTransfer();
      dt.items.add(file);
      fileInput.files = dt.files;
      showPreview(file);
    }
  });

  function showPreview(file) {
    if (!file) return;
    const allowed = ["image/jpeg","image/png","image/webp"];
    if (!allowed.includes(file.type)) {
      alert("Only JPG, PNG or WEBP images are allowed.");
      return;
    }
    if (file.size > 8 * 1024 * 1024) {
      alert("Image must be under 8 MB.");
      return;
    }
    const reader = new FileReader();
    reader.onload = function (e) {
      if (previewImg) previewImg.src = e.target.result;
      if (preview) preview.style.display = "block";
      const lbl = dropZone.querySelector(".file-drop-lbl");
      if (lbl) lbl.innerHTML = "<strong>" + file.name + "</strong><br><span style='font-size:11px;color:var(--muted)'>Click to change</span>";
    };
    reader.readAsDataURL(file);
  }
})();

/* ── Confirm delete ── */
document.addEventListener("DOMContentLoaded", function () {
  document.querySelectorAll(".delete-form").forEach(function (form) {
    form.addEventListener("submit", function (e) {
      if (!confirm("Delete this project? This cannot be undone.")) {
        e.preventDefault();
      }
    });
  });
});

/* ── Auto-dismiss flash messages ── */
(function () {
  setTimeout(function () {
    document.querySelectorAll(".flash-msg").forEach(function (el) {
      el.style.transition = "opacity .5s";
      el.style.opacity = "0";
      setTimeout(function () { el.remove(); }, 500);
    });
  }, 4000);
})();
