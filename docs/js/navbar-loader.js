function setActiveNavLink(root) {
  const currentPage = document.body.dataset.page;
  const navLinks = root.querySelectorAll(".top-nav a");

  navLinks.forEach((link) => {
    const pageName = link.dataset.page;
    link.classList.toggle("active", pageName === currentPage);
  });
}


function initNavbarMenu(root) {
  const menuButton = root.querySelector(".menu-toggle");
  const nav = root.querySelector(".top-nav");

  if (!menuButton || !nav) {
    return;
  }

  menuButton.addEventListener("click", () => {
    const isOpen = nav.classList.toggle("open");
    menuButton.setAttribute("aria-expanded", isOpen ? "true" : "false");
  });
}


async function loadNavbar() {
  const slot = document.getElementById("site-navbar");

  if (!slot) {
    return;
  }

  const response = await fetch("navbar.html");
  if (!response.ok) {
    throw new Error(`Failed to load navbar.html (${response.status}).`);
  }

  slot.innerHTML = await response.text();
  setActiveNavLink(slot);
  initNavbarMenu(slot);
}


loadNavbar().catch((error) => {
  console.error("Failed to load shared navbar.", error);
});
