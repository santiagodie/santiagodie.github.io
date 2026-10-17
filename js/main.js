// santiagodie.com: i18n, project cards, navigation and section reveals.
// No dependencies. All UI text comes from i18n/<lang>.json.

(() => {
  "use strict";

  const LANGS = ["en", "es", "fr"];
  const DEFAULT_LANG = "en";
  const STORAGE_KEY = "lang";
  const SWAP_MS = 120;

  const root = document.documentElement;
  const cache = new Map();
  let strings = {};
  let projects = null;
  let projectsFailed = false;
  let currentLang = null;

  // Storage can throw (private mode, blocked cookies), so every access is guarded.
  const storage = {
    get() {
      try { return window.localStorage.getItem(STORAGE_KEY); } catch { return null; }
    },
    set(value) {
      try { window.localStorage.setItem(STORAGE_KEY, value); } catch { /* not persisted */ }
    },
  };

  function initialLang() {
    const fromUrl = new URLSearchParams(window.location.search).get("lang");
    if (LANGS.includes(fromUrl)) return fromUrl;
    const saved = storage.get();
    if (LANGS.includes(saved)) return saved;
    const browser = (navigator.languages || [navigator.language || ""])
      .map((tag) => String(tag).slice(0, 2).toLowerCase())
      .find((code) => code === "es" || code === "fr");
    return browser || DEFAULT_LANG;
  }

  async function fetchJson(url) {
    const response = await fetch(url, { cache: "no-cache" });
    if (!response.ok) throw new Error(`${url}: ${response.status}`);
    return response.json();
  }

  function loadStrings(lang) {
    if (!cache.has(lang)) {
      const request = fetchJson(`i18n/${lang}.json`);
      request.catch(() => cache.delete(lang));
      cache.set(lang, request);
    }
    return cache.get(lang);
  }

  function lookup(path, source = strings) {
    return path.split(".").reduce((node, key) => (node == null ? undefined : node[key]), source);
  }

  // Writes text into an element, turning a leading "TODO:" into a visible marker.
  const TODO = /^TODO\s*:?\s*/;
  function setText(node, value) {
    const text = value == null ? "" : String(value);
    if (!TODO.test(text)) {
      node.textContent = text;
      return;
    }
    const marker = document.createElement("span");
    marker.className = "todo";
    marker.textContent = "TODO";
    const rest = document.createElement("span");
    rest.className = "todo-text";
    rest.textContent = text.replace(TODO, "");
    node.replaceChildren(marker, rest);
  }

  function el(tag, className, text) {
    const node = document.createElement(tag);
    if (className) node.className = className;
    if (text !== undefined) setText(node, text);
    return node;
  }

  const ARROW = '<svg class="icon" aria-hidden="true" viewBox="0 0 16 16"><path d="M5 11 11 5M6 5h5v5"/></svg>';

  function externalLink(href, label, className) {
    const a = el("a", className);
    a.href = href;
    a.target = "_blank";
    a.rel = "noopener";
    if (label) a.append(document.createTextNode(label));
    return a;
  }

  // `context` names the target for screen readers ("Code: WordHive"), so a links
  // list does not read "Code" eight times.
  function finishExternal(a, context) {
    a.insertAdjacentHTML("beforeend", ARROW);
    const hidden = context ? `: ${context} (${lookup("a11y.newTab")})` : ` (${lookup("a11y.newTab")})`;
    a.append(el("span", "visually-hidden", hidden));
    return a;
  }

  // Static strings ---------------------------------------------------------

  function applyStatic() {
    document.querySelectorAll("[data-i18n]").forEach((node) => {
      setText(node, lookup(node.dataset.i18n));
    });
    document.querySelectorAll("[data-i18n-attr]").forEach((node) => {
      node.dataset.i18nAttr.split(";").forEach((pair) => {
        const [attr, key] = pair.split(":");
        const value = lookup(key);
        if (attr && value != null) node.setAttribute(attr.trim(), value);
      });
    });

    document.title = lookup("meta.title") || document.title;
    const description = document.querySelector('meta[name="description"]');
    if (description && lookup("meta.description")) description.content = lookup("meta.description");

    document.querySelectorAll("[data-lang]").forEach((button) => {
      button.setAttribute("aria-pressed", String(button.dataset.lang === currentLang));
    });

    const year = document.querySelector("[data-year]");
    if (year) year.textContent = String(new Date().getFullYear());

    syncMenuLabel();
  }

  // Dynamic sections -------------------------------------------------------

  function renderAbout() {
    const target = document.querySelector('[data-render="about"]');
    const paragraphs = lookup("about.paragraphs") || [];
    target.replaceChildren(...paragraphs.map((text) => el("p", "", text)));
    // No text yet: hide the section and its menu entry instead of showing a lone heading.
    const section = target.closest("section");
    section.hidden = !paragraphs.length;
    const link = document.querySelector(`.nav__list a[href="#${section.id}"]`);
    if (link) link.parentElement.hidden = !paragraphs.length;
  }

  function renderEntries(name) {
    const list = document.querySelector(`[data-render="${name}"]`);
    const items = lookup(`${name}.items`) || [];
    if (!items.length) {
      list.replaceChildren(el("li", "status", lookup(`${name}.empty`)));
      return;
    }
    list.replaceChildren(...items.map((item) => {
      const li = el("li", "entry");
      li.append(el("p", "entry__period", item.period));
      const body = el("div");
      body.append(el("h3", "entry__title", item.title));
      if (item.org) body.append(el("p", "entry__org", item.org));
      if (item.text) body.append(el("p", "entry__text", item.text));
      li.append(body);
      return li;
    }));
  }

  function renderSkills() {
    const target = document.querySelector('[data-render="skills"]');
    const groups = (lookup("skills.groups") || []).filter((group) => group.items && group.items.length);
    if (!groups.length) {
      target.replaceChildren(el("p", "status", lookup("skills.empty")));
      return;
    }
    target.replaceChildren(...groups.map((group) => {
      const section = el("div", "skills__group");
      section.append(el("h3", "skills__name", group.name));
      const ul = el("ul", "skills__items");
      group.items.forEach((item) => ul.append(el("li", "", item)));
      section.append(ul);
      return section;
    }));
  }

  function renderCv() {
    const slot = document.querySelector('[data-render="cv"]');
    const file = lookup("contact.cvFile");
    if (file) {
      const a = externalLink(file, "", "contact__link");
      a.append(el("span", "contact__label", lookup("contact.cv")));
      a.append(el("span", "contact__value", file.split("/").pop()));
      slot.replaceChildren(finishExternal(a));
      return;
    }
    const row = el("div", "contact__row");
    row.append(el("span", "contact__label", lookup("contact.cv")));
    row.append(el("span", "contact__value", lookup("contact.cvPending")));
    slot.replaceChildren(row);
  }

  function renderProjects() {
    const list = document.querySelector('[data-render="projects"]');
    const status = document.querySelector("[data-projects-status]");

    if (projectsFailed) {
      list.replaceChildren();
      status.replaceChildren(
        document.createTextNode(`${lookup("projects.error")} `),
        finishExternal(externalLink("https://github.com/santiagodie?tab=repositories", "GitHub")),
      );
      return;
    }
    if (!projects || !projects.length) {
      list.replaceChildren();
      setText(status, lookup(projects ? "projects.empty" : "projects.loading"));
      return;
    }

    status.replaceChildren();
    list.replaceChildren(...projects.map((project, index) => {
      const li = el("li", project.featured ? "card card--featured" : "card");
      li.style.setProperty("--i", String(index));
      li.append(el("h3", "card__title", project.title));

      // Course names are the official English ones, so they keep lang="en".
      if (project.course) {
        const course = el("p", "card__course");
        const name = el("span", "", project.course);
        name.lang = "en";
        course.append(name, document.createTextNode(` · ${lookup("projects.university")}`));
        li.append(course);
      }

      // Untranslated descriptions are English text: mark them so screen readers
      // switch pronunciation.
      const pending = (project.todo || []).includes(`description.${currentLang}`);
      const own = project.description && project.description[currentLang];
      const text = el("p", "card__text", own || (project.description && project.description.en) || "");
      if (currentLang !== "en" && (pending || !own)) text.lang = "en";
      li.append(text);

      if (pending) li.append(el("p", "card__pending", lookup("projects.translationPending")));

      if (project.tech && project.tech.length) {
        li.append(el("p", "visually-hidden", lookup("projects.stack")));
        const tags = el("ul", "tags");
        project.tech.forEach((tech) => tags.append(el("li", "", tech)));
        li.append(tags);
      }

      const links = el("div", "card__links");
      if (project.repo) links.append(finishExternal(externalLink(project.repo, lookup("projects.code")), project.title));
      if (project.demo && project.demo.url) {
        const label = lookup(project.demo.type === "colab" ? "projects.colab" : "projects.demo");
        links.append(finishExternal(externalLink(project.demo.url, label), project.title));
      }
      if (links.childElementCount) li.append(links);
      return li;
    }));
  }

  function renderAll() {
    applyStatic();
    renderAbout();
    renderProjects();
    renderEntries("experience");
    renderEntries("education");
    renderSkills();
    renderCv();
  }

  // Language switching -----------------------------------------------------

  let switchToken = 0;

  async function setLang(lang, { persist = false, animate = false } = {}) {
    if (!LANGS.includes(lang)) lang = DEFAULT_LANG;
    const token = ++switchToken;

    let next;
    try {
      next = await loadStrings(lang);
    } catch (error) {
      console.warn("Could not load language", lang, error);
      if (lang !== DEFAULT_LANG && !currentLang) return setLang(DEFAULT_LANG);
      return;
    }
    if (token !== switchToken) return; // a newer switch won

    const swap = () => {
      strings = next;
      currentLang = lang;
      root.lang = lang;
      if (persist) storage.set(lang);
      renderAll();
    };

    // Reduced motion keeps the fade (it explains the change) and drops the blur in CSS.
    if (animate) {
      root.classList.add("is-switching");
      await new Promise((resolve) => setTimeout(resolve, SWAP_MS));
      if (token !== switchToken) return;
      swap();
      requestAnimationFrame(() => root.classList.remove("is-switching"));
    } else {
      swap();
    }
  }

  document.querySelectorAll("[data-lang]").forEach((button) => {
    button.addEventListener("click", () => {
      if (button.dataset.lang !== currentLang) setLang(button.dataset.lang, { persist: true, animate: true });
    });
  });

  // Mobile menu ------------------------------------------------------------

  const header = document.querySelector("[data-header]");
  const toggle = document.querySelector("[data-nav-toggle]");
  const navList = document.querySelector("[data-nav-list]");
  const compact = window.matchMedia("(max-width: 59.99em)");

  function syncMenuLabel() {
    const label = document.querySelector("[data-nav-label]");
    const open = toggle.getAttribute("aria-expanded") === "true";
    if (label) label.textContent = lookup(open ? "nav.close" : "nav.menu") || "";
  }

  function setMenu(open, { returnFocus = false } = {}) {
    toggle.setAttribute("aria-expanded", String(open));
    header.toggleAttribute("data-menu-open", open);
    navList.inert = compact.matches && !open;
    syncMenuLabel();
    if (!open && returnFocus) toggle.focus();
  }

  toggle.addEventListener("click", () => setMenu(toggle.getAttribute("aria-expanded") !== "true"));
  navList.addEventListener("click", (event) => {
    if (event.target.closest("a")) setMenu(false);
  });
  document.addEventListener("keydown", (event) => {
    if (event.key === "Escape" && header.hasAttribute("data-menu-open")) setMenu(false, { returnFocus: true });
  });
  document.addEventListener("click", (event) => {
    if (header.hasAttribute("data-menu-open") && !header.contains(event.target)) setMenu(false);
  });
  compact.addEventListener("change", () => setMenu(false));
  setMenu(false);

  // Scroll state: header hairline and current section ----------------------

  const onScroll = () => header.toggleAttribute("data-scrolled", window.scrollY > 8);
  window.addEventListener("scroll", onScroll, { passive: true });
  onScroll();

  const navLinks = new Map(
    [...navList.querySelectorAll('a[href^="#"]')].map((link) => [link.getAttribute("href").slice(1), link]),
  );

  if ("IntersectionObserver" in window) {
    const visible = new Set();
    const spy = new IntersectionObserver((entries) => {
      entries.forEach((entry) => (entry.isIntersecting ? visible.add(entry.target.id) : visible.delete(entry.target.id)));
      const current = [...navLinks.keys()].find((id) => visible.has(id));
      navLinks.forEach((link, id) => {
        if (id === current) link.setAttribute("aria-current", "true");
        else link.removeAttribute("aria-current");
      });
    }, { rootMargin: "-45% 0px -50% 0px" });
    navLinks.forEach((_, id) => {
      const section = document.getElementById(id);
      if (section) spy.observe(section);
    });

    const reveal = new IntersectionObserver((entries, observer) => {
      entries.forEach((entry) => {
        if (!entry.isIntersecting) return;
        entry.target.classList.add("is-visible");
        observer.unobserve(entry.target);
      });
    }, { rootMargin: "0px 0px -10% 0px", threshold: 0.05 });
    document.querySelectorAll(".reveal").forEach((section) => reveal.observe(section));
  } else {
    document.querySelectorAll(".reveal").forEach((section) => section.classList.add("is-visible"));
  }

  // Boot -------------------------------------------------------------------

  fetchJson("data/projects.json")
    .then((data) => { projects = Array.isArray(data.projects) ? data.projects : []; })
    .catch((error) => { console.warn("Could not load projects", error); projectsFailed = true; })
    .finally(() => { if (currentLang) renderProjects(); });

  setLang(initialLang()).finally(() => root.classList.add("is-ready"));
})();
