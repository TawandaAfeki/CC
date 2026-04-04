
function openModal() {
  const overlay = document.getElementById('modal-overlay');
  overlay.classList.add('visible');
  document.body.style.overflow = 'hidden';
  document.getElementById('modal-form-fields').classList.remove('hide');
  document.getElementById('modal-success').classList.remove('show');
  const btn = document.getElementById('modal-submit-btn');
  if (btn) { btn.textContent = 'Send Message'; btn.disabled = false; }
}

function closeModal() {
  const overlay = document.getElementById('modal-overlay');
  overlay.classList.remove('visible');
  document.body.style.overflow = '';
  window.location.href = 'index.html';
}

function handleModalSubmit(e) {
  e.preventDefault();
  const btn = document.getElementById('modal-submit-btn');
  btn.textContent = 'Sending…';
  btn.disabled = true;
  setTimeout(() => {
    document.getElementById('modal-form-fields').classList.add('hide');
    document.getElementById('modal-success').classList.add('show');
  }, 1000);
}

document.getElementById('modal-overlay').addEventListener('click', function(e) {
  if (e.target === this) closeModal();
});

document.addEventListener('keydown', function(e) {
  if (e.key === 'Escape') closeModal();
});

// Auto-open on page load — remove this line if embedding in main site
window.addEventListener('DOMContentLoaded', () => setTimeout(openModal, 300));

// =======================
// Supabase Init
// =======================
  const { createClient } = supabase;

const supabaseClient = supabase.createClient(
  "https://krmhgcbmonocngjjpjgw.supabase.co",
  "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImtybWhnY2Jtb25vY25nampwamd3Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzA1ODIyODcsImV4cCI6MjA4NjE1ODI4N30.-7dNxyrISyouzAgx_s8tlR8B0PvD8LiaGLC0jzIz2FY"
);


// =======================
// EmailJS Init
// =======================
(function () {
  emailjs.init("1PhbXKtOHcwy3kEo8");
})();

// =======================
// Contact Form Submission
// =======================
const contactForm = document.getElementById("contact-form");
const formStatus = document.getElementById("form-status");

if (contactForm) {
  contactForm.addEventListener("submit", async function (e) {
    e.preventDefault();

    formStatus.textContent = "Sending...";
    formStatus.style.color = "#94a3b8";

    const fileInput = document.getElementById("data_file");
    let fileLink = "No file uploaded";

    if (fileInput && fileInput.files.length > 0) {
      const file = fileInput.files[0];

      const allowedTypes = [
        "text/csv",
        "application/vnd.ms-excel",
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
      ];

      if (!allowedTypes.includes(file.type)) {
        formStatus.textContent =
          "Invalid file type. Please upload a CSV or Excel file.";
        formStatus.style.color = "#ef4444";
        return;
      }

      const filePath = `uploads/${Date.now()}_${file.name}`;

      const { error } = await supabaseClient.storage
        .from("contact-uploads")
        .upload(filePath, file);

      if (error) {
        console.error("Supabase upload error:", error);
        formStatus.textContent =
          "File upload failed. Please try again.";
        formStatus.style.color = "#ef4444";
        return;
      }

      const { data } = supabaseClient.storage
        .from("contact-uploads")
        .getPublicUrl(filePath);

      fileLink = data.publicUrl;
    }

    const templateParams = {
      user_name: contactForm.user_name.value,
      user_email: contactForm.user_email.value,
      message: contactForm.message.value,
      file_link: fileLink,
    };

    Promise.all([
      emailjs.send(
        "service_lsyfdad",
        "template_20x0lee",
        templateParams
      ),
      emailjs.send(
        "service_lsyfdad",
        "template_bicxoer",
        templateParams
      )
    ])
      .then(() => {
        formStatus.textContent = "Message sent successfully";
        formStatus.style.color = "#22c55e";
        contactForm.reset();
      })
      .catch((error) => {
        console.error("EmailJS error:", error);
        formStatus.textContent =
          error.text || "Something went wrong. Please try again.";
        formStatus.style.color = "#ef4444";
      });
  });
}

