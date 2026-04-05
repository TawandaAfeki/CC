// Scroll reveal
  const reveals = document.querySelectorAll('.reveal');
  const io = new IntersectionObserver((entries) => {
    entries.forEach(e => { if (e.isIntersecting) { e.target.classList.add('in'); io.unobserve(e.target); } });
  }, { threshold: 0.12 });
  reveals.forEach(el => io.observe(el));

  // FAQ accordion
  document.querySelectorAll('.faq-q').forEach(btn => {
    btn.addEventListener('click', () => {
      const item = btn.closest('.faq-item');
      const isOpen = item.classList.contains('open');
      document.querySelectorAll('.faq-item').forEach(i => i.classList.remove('open'));
      if (!isOpen) item.classList.add('open');
      btn.setAttribute('aria-expanded', !isOpen);
    });
  });

// =======================
// Supabase Init
// =======================
  const { createClient } = supabase;

const supabaseClient = supabase.createClient(
  "https://krmhgcbmonocngjjpjgw.supabase.co",
  "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImtybWhnY2Jtb25vY25nampwamd3Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzA1ODIyODcsImV4cCI6MjA4NjE1ODI4N30.-7dNxyrISyouzAgx_s8tlR8B0PvD8LiaGLC0jzIz2FY"
);

  

  // Form handler
  function handleSubmit(e) {
    e.preventDefault();
    const btn = document.getElementById('submit-btn');
    btn.textContent = 'Sending…';
    btn.disabled = true;
    setTimeout(() => {
      btn.textContent = 'Message sent! We\'ll be in touch soon.';
      btn.style.background = '#1d6b3f';
    }, 1200);
  }

  // Trigger reveals for above-fold content
  reveals.forEach(el => {
    const rect = el.getBoundingClientRect();
    if (rect.top < window.innerHeight) el.classList.add('in');
  });


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
      company: contactForm.company.value,
      service: document.getElementById("service").value,
      message: contactForm.message.value,
      file_link: fileLink,
    };

    Promise.all([
      emailjs.send(
        "service_ivfwz6v",
        "template_20x0lee",
        templateParams
      ),
      emailjs.send(
        "service_ivfwz6v",
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

        // ✅ Fire Google Ads conversion HERE
  gtag('event', 'conversion', {
      'send_to': 'AW-18010785984/vWOcCLS7jJYcEMCRm4xD',
      'value': 10.0,
      'currency': 'ZAR'
      });
})

function toggleMenu() {
  const menu = document.getElementById("mobile-menu");
  menu.classList.toggle("active");
}

let lastScrollY = window.scrollY;

window.addEventListener('scroll', () => {
  const mobileMenu = document.getElementById('mobile-menu');

  if (Math.abs(window.scrollY - lastScrollY) > 20) {
    mobileMenu.classList.remove('active');
  }

  lastScrollY = window.scrollY;
});
document.addEventListener('click', (e) => {
  const menu = document.getElementById('mobile-menu');
  const hamburger = document.getElementById('hamburger');

  if (!menu.contains(e.target) && !hamburger.contains(e.target)) {
    menu.classList.remove('active');
  }
});
